import asyncio
import platform
import logging
import time
from datetime import datetime

from sqlalchemy import select
from ..database import async_session
from ..models.device import Device
from ..config import settings

logger = logging.getLogger(__name__)

_pending_checks: dict[int, dict] = {}

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


def register_pending_check(device_id: int, action: str, device_name: str):
    """Register that we expect device_id to change state after a wake/shutdown command."""
    _pending_checks[device_id] = {
        "action": action,
        "device_name": device_name,
        "registered_at": time.time(),
    }


async def _ping(ip: str) -> bool:
    flag = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_flag = "-w" if platform.system().lower() == "windows" else "-W"
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", flag, "2", timeout_flag, "3", ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=8)
        return proc.returncode == 0
    except Exception:
        return False


_offline_counter: dict[int, int] = {}
OFFLINE_THRESHOLD = 2


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

                expired = [did for did, info in _pending_checks.items()
                           if time.time() - info["registered_at"] > 300]
                for did in expired:
                    _pending_checks.pop(did, None)

                for d in devices:
                    alive = tasks[d.id].result() if not tasks[d.id].cancelled() else False

                    if alive:
                        _offline_counter.pop(d.id, None)
                        new_online = True
                    else:
                        _offline_counter[d.id] = _offline_counter.get(d.id, 0) + 1
                        new_online = _offline_counter[d.id] < OFFLINE_THRESHOLD and d.is_online

                    changed = d.is_online != new_online
                    d.is_online = new_online
                    if new_online:
                        d.last_seen_at = datetime.utcnow()
                    if changed:
                        await _broadcast_status(d.id, new_online)
                        if d.id in _pending_checks:
                            info = _pending_checks.pop(d.id)
                            expected = (info["action"] == "wake" and new_online) or \
                                       (info["action"] == "shutdown" and not new_online)
                            if expected:
                                from .notification import notify_all
                                action_label = "开机" if info["action"] == "wake" else "关机"
                                await notify_all(
                                    f"任务成功 — {action_label}已确认",
                                    f"设备: {info['device_name']} | 状态已确认{'在线' if new_online else '离线'}",
                                    event="success",
                                )

                await db.commit()
        except Exception as e:
            logger.error("Ping loop error: %s", e)

        try:
            await asyncio.wait_for(event.wait(), timeout=settings.PING_INTERVAL)
        except asyncio.TimeoutError:
            pass
