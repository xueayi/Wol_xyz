import asyncio
import logging
from sqlalchemy import select

from ..database import async_session
from ..models.trigger import TriggerSource
from ..models.device import Device

logger = logging.getLogger(__name__)

_tasks: dict[int, asyncio.Task] = {}


async def start_bemfa_clients():
    async with async_session() as db:
        result = await db.execute(
            select(TriggerSource).where(TriggerSource.type == "bemfa", TriggerSource.enabled.is_(True))
        )
        for trigger in result.scalars().all():
            _start_one(trigger.id, trigger.config)


def _start_one(trigger_id: int, config: dict):
    if trigger_id in _tasks and not _tasks[trigger_id].done():
        _tasks[trigger_id].cancel()
    _tasks[trigger_id] = asyncio.create_task(_bemfa_loop(trigger_id, config))


async def _bemfa_loop(trigger_id: int, config: dict):
    host = config.get("host", "bemfa.com")
    port = config.get("port", 8344)
    uid = config.get("uid", "")
    topic = config.get("topic", "")
    device_mac = config.get("device_mac", "")

    while True:
        reader = writer = None
        try:
            reader, writer = await asyncio.open_connection(host, port)
            sub = f"cmd=1&uid={uid}&topic={topic}\r\n"
            writer.write(sub.encode())
            await writer.drain()
            logger.info("Bemfa trigger %d connected, subscribed to %s", trigger_id, topic)

            ping_task = asyncio.create_task(_heartbeat(writer))
            try:
                while True:
                    data = await asyncio.wait_for(reader.read(1024), timeout=90)
                    if not data:
                        break
                    msg = data.decode("utf-8", errors="ignore").strip()
                    if not msg or msg == "cmd=0":
                        continue
                    logger.info("Bemfa [%s]: %s", topic, msg)
                    await _handle_message(msg, topic, device_mac)
            finally:
                ping_task.cancel()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Bemfa trigger %d error: %s", trigger_id, e)

        if writer:
            writer.close()
        await asyncio.sleep(5)


async def _heartbeat(writer: asyncio.StreamWriter):
    while True:
        await asyncio.sleep(30)
        try:
            writer.write(b"ping\r\n")
            await writer.drain()
        except Exception:
            break


async def _handle_message(msg: str, topic: str, device_mac: str):
    if f"topic={topic}&msg=on" in msg:
        action = "wake"
    elif f"topic={topic}&msg=off" in msg:
        action = "shutdown"
    else:
        return

    async with async_session() as db:
        device = None
        if device_mac:
            device = (await db.execute(
                select(Device).where(Device.mac == device_mac.upper())
            )).scalar_one_or_none()

        if not device:
            logger.warning("Bemfa: device %s not found", device_mac)
            return

        from .log_writer import write_log
        if action == "wake":
            from .wol import send_wol
            ok, detail = await send_wol(device.mac)
        else:
            from .shutdown import send_shutdown
            from ..crypto import decrypt
            if not device.shutdown_enabled:
                logger.warning("Bemfa: shutdown not enabled for %s", device.name)
                return
            pwd = decrypt(device.shutdown_password_enc)
            ok, detail = await send_shutdown(device.ip, device.shutdown_user, pwd)

        await write_log(db, device.id, action, "success" if ok else "failure", detail, "external")
        if ok:
            from .ping_monitor import register_pending_check
            register_pending_check(device.id, action, device.name)

    from .notification import notify_all
    await notify_all(
        f"巴法云触发 {'成功' if ok else '失败'}",
        f"设备: {device.name} | 动作: {action} | {detail}",
    )


def stop_all():
    for t in _tasks.values():
        t.cancel()
    _tasks.clear()
