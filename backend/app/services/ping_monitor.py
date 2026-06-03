import asyncio
import platform
import logging
from datetime import datetime

from sqlalchemy import select
from ..database import async_session
from ..models.device import Device
from ..config import settings

logger = logging.getLogger(__name__)

_ws_clients: set = set()
_wake_event: asyncio.Event = None  # type: ignore


def _get_event() -> asyncio.Event:
    global _wake_event
    if _wake_event is None:
        _wake_event = asyncio.Event()
    return _wake_event


def register_ws(ws):
    _ws_clients.add(ws)
    _get_event().set()
    if len(_ws_clients) == 1:
        logger.info("Ping monitor activated (client connected)")


def unregister_ws(ws):
    _ws_clients.discard(ws)
    if not _ws_clients:
        _get_event().clear()
        logger.info("Ping monitor paused (no active clients)")


def has_active_clients() -> bool:
    return len(_ws_clients) > 0


async def _ping(ip: str) -> bool:
    flag = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_flag = "-w" if platform.system().lower() == "windows" else "-W"
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", flag, "1", timeout_flag, "2", ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=5)
        return proc.returncode == 0
    except Exception:
        return False


async def _broadcast_status(device_id: int, is_online: bool):
    import json
    msg = json.dumps({"type": "device_status", "device_id": device_id, "is_online": is_online})
    dead = set()
    for ws in _ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


async def ping_loop():
    """Background task: only ping devices when there are active WebSocket clients."""
    event = _get_event()
    logger.info("Ping monitor ready (interval=%ds, waiting for clients)", settings.PING_INTERVAL)
    while True:
        await event.wait()

        if not has_active_clients():
            continue

        try:
            async with async_session() as db:
                result = await db.execute(select(Device))
                devices = result.scalars().all()

                tasks = {d.id: asyncio.create_task(_ping(d.ip)) for d in devices}
                if tasks:
                    await asyncio.gather(*tasks.values(), return_exceptions=True)

                for d in devices:
                    alive = tasks[d.id].result() if not tasks[d.id].cancelled() else False
                    changed = d.is_online != alive
                    d.is_online = alive
                    if alive:
                        d.last_seen_at = datetime.utcnow()
                    if changed:
                        await _broadcast_status(d.id, alive)

                await db.commit()
        except Exception as e:
            logger.error("Ping loop error: %s", e)

        try:
            await asyncio.wait_for(event.wait(), timeout=settings.PING_INTERVAL)
        except asyncio.TimeoutError:
            pass
