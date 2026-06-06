import asyncio
import logging
from sqlalchemy import select

from ..database import async_session
from ..models.trigger import TriggerSource
from ..models.device import Device

logger = logging.getLogger(__name__)

_tasks: dict[int, asyncio.Task] = {}
_status: dict[int, str] = {}


def get_status() -> dict[int, str]:
    return dict(_status)


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
    _status[trigger_id] = "connecting"
    _tasks[trigger_id] = asyncio.create_task(_bemfa_loop(trigger_id, config))


async def _bemfa_loop(trigger_id: int, config: dict):
    host = config.get("host", "bemfa.com")
    port = config.get("port", 8344)
    uid = config.get("uid", "")
    topic = config.get("topic", "")

    backoff = 5
    fail_count = 0

    def _fail(msg: str):
        nonlocal fail_count, backoff
        fail_count += 1
        if fail_count == 1:
            logger.warning("Bemfa trigger %d %s", trigger_id, msg)
        elif fail_count == 2:
            logger.warning("Bemfa trigger %d still failing, retrying every %ds", trigger_id, backoff)
        _status[trigger_id] = "disconnected"

    while True:
        reader = writer = None
        try:
            reader, writer = await asyncio.open_connection(host, port)
            sub = f"cmd=1&uid={uid}&topic={topic}\r\n"
            writer.write(sub.encode())
            await writer.drain()
            if fail_count == 0:
                logger.info("Bemfa trigger %d subscribing to %s ...", trigger_id, topic)

            try:
                ack = await asyncio.wait_for(reader.read(1024), timeout=10)
            except asyncio.TimeoutError:
                _fail("handshake timeout (uid may be invalid)")
                if writer:
                    writer.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 300)
                continue

            if not ack:
                _fail("connection closed during handshake")
                if writer:
                    writer.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 300)
                continue

            ack_msg = ack.decode("utf-8", errors="ignore").strip()
            if "res=1" not in ack_msg:
                _fail(f"handshake failed: {ack_msg}")
                if writer:
                    writer.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 300)
                continue

            _status[trigger_id] = "connected"
            backoff = 5
            fail_count = 0
            logger.info("Bemfa trigger %d connected, subscribed to %s", trigger_id, topic)

            ping_task = asyncio.create_task(_heartbeat(writer))
            try:
                while True:
                    data = await asyncio.wait_for(reader.read(1024), timeout=90)
                    if not data:
                        break
                    msg = data.decode("utf-8", errors="ignore").strip()
                    if not msg or msg.startswith("cmd=0"):
                        continue
                    logger.info("Bemfa [%s]: %s", topic, msg)
                    await _handle_message(msg, topic, config)
            finally:
                ping_task.cancel()

        except asyncio.CancelledError:
            _status.pop(trigger_id, None)
            break
        except Exception as e:
            _fail(f"error: {e}")

        if writer:
            writer.close()
        _status[trigger_id] = "connecting"
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 300)


async def _heartbeat(writer: asyncio.StreamWriter):
    while True:
        await asyncio.sleep(30)
        try:
            writer.write(b"ping\r\n")
            await writer.drain()
        except Exception:
            break


async def _resolve_devices(config: dict) -> list:
    """Resolve target devices from config (supports device_mac and target_device_ids)."""
    device_mac = config.get("device_mac", "")
    target_ids = config.get("target_device_ids", [])

    devices = []
    async with async_session() as db:
        if device_mac:
            device = (await db.execute(
                select(Device).where(Device.mac == device_mac.upper())
            )).scalar_one_or_none()
            if device:
                devices.append(device)
        if not devices and target_ids:
            result = await db.execute(
                select(Device).where(Device.id.in_(target_ids))
            )
            devices = list(result.scalars().all())
    return devices


async def _handle_message(msg: str, topic: str, config: dict):
    if f"topic={topic}&msg=on" in msg:
        action = "wake"
    elif f"topic={topic}&msg=off" in msg:
        action = "shutdown"
    else:
        return

    devices = await _resolve_devices(config)
    if not devices:
        logger.warning("Bemfa: no target device found for topic %s", topic)
        return

    for device in devices:
        async with async_session() as db:
            merged = (await db.execute(
                select(Device).where(Device.id == device.id)
            )).scalar_one()

            from .log_writer import write_log
            if action == "wake":
                from .wol import send_wol
                ok, detail = await send_wol(merged.mac)
            else:
                from .shutdown import send_shutdown
                from ..crypto import decrypt
                if not merged.shutdown_enabled:
                    logger.warning("Bemfa: shutdown not enabled for %s", merged.name)
                    continue
                pwd = decrypt(merged.shutdown_password_enc) if merged.shutdown_auth_type == "password" else ""
                key = decrypt(merged.shutdown_key_enc) if merged.shutdown_auth_type == "key" else None
                ok, detail = await send_shutdown(
                    merged.ip, merged.shutdown_user, pwd,
                    private_key=key, device_type=merged.device_type,
                )

            await write_log(db, merged.id, action, "success" if ok else "failure", detail, "external")
            if ok:
                from .ping_monitor import register_pending_check
                register_pending_check(merged.id, action, merged.name)

            device_name = merged.name

        from .notification import notify_all
        await notify_all(
            f"巴法云触发 {'成功' if ok else '失败'}",
            f"设备: {device_name} | 动作: {action} | {detail}",
        )


def stop_all():
    for t in _tasks.values():
        t.cancel()
    _tasks.clear()
    _status.clear()
