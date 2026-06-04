import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..database import async_session
from ..models.schedule import ScheduledTask
from ..models.device import Device

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        self.scheduler.start()
        async with async_session() as db:
            from sqlalchemy import select
            result = await db.execute(select(ScheduledTask).where(ScheduledTask.enabled.is_(True)))
            for task in result.scalars().all():
                self.add_task(task)
        logger.info("Scheduler started")

    def stop(self):
        self.scheduler.shutdown(wait=False)

    def _job_id(self, task_id: int) -> str:
        return f"xwol_task_{task_id}"

    def add_task(self, task: ScheduledTask):
        if not task.enabled:
            return
        try:
            parts = task.cron_expression.strip().split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0], hour=parts[1],
                    day=parts[2], month=parts[3], day_of_week=parts[4],
                )
            else:
                logger.error("Invalid cron: %s", task.cron_expression)
                return

            self.scheduler.add_job(
                _execute_task, trigger=trigger,
                id=self._job_id(task.id),
                args=[task.id, task.device_id, task.action],
                replace_existing=True,
            )
            logger.info("Scheduled task %d: %s", task.id, task.cron_expression)
        except Exception as e:
            logger.error("Failed to schedule task %d: %s", task.id, e)

    def update_task(self, task: ScheduledTask):
        self.remove_task(task.id)
        self.add_task(task)

    def remove_task(self, task_id: int):
        jid = self._job_id(task_id)
        if self.scheduler.get_job(jid):
            self.scheduler.remove_job(jid)


async def _execute_task(task_id: int, device_id: int, action: str):
    from sqlalchemy import select
    async with async_session() as db:
        device = (await db.execute(select(Device).where(Device.id == device_id))).scalar_one_or_none()
        if not device:
            logger.error("Task %d: device %d not found", task_id, device_id)
            return

        if action == "wake":
            from .wol import send_wol
            ok, detail = await send_wol(device.mac)
        elif action == "shutdown":
            from .shutdown import send_shutdown
            from ..crypto import decrypt
            pwd = decrypt(device.shutdown_password_enc)
            ok, detail = await send_shutdown(device.ip, device.shutdown_user, pwd)
        else:
            logger.error("Task %d: unknown action %s", task_id, action)
            return

        from .log_writer import write_log
        await write_log(db, device_id, action, "success" if ok else "failure", detail, "scheduled")
        if ok:
            from .ping_monitor import register_pending_check
            register_pending_check(device_id, action, device.name)

        task_obj = (await db.execute(select(ScheduledTask).where(ScheduledTask.id == task_id))).scalar_one_or_none()
        if task_obj:
            task_obj.last_run_at = datetime.utcnow()
            await db.commit()

    from .notification import notify_all
    await notify_all(
        f"定时任务 {'成功' if ok else '失败'}",
        f"设备: {device.name} | 动作: {action} | {detail}",
    )


scheduler_service = SchedulerService()
