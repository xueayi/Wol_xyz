import asyncio
import json
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


async def start_mqtt_clients():
    async with async_session() as db:
        result = await db.execute(
            select(TriggerSource).where(TriggerSource.type == "mqtt", TriggerSource.enabled.is_(True))
        )
        for trigger in result.scalars().all():
            _start_one(trigger.id, trigger.config)


def _start_one(trigger_id: int, config: dict):
    if trigger_id in _tasks and not _tasks[trigger_id].done():
        _tasks[trigger_id].cancel()
    _status[trigger_id] = "connecting"
    _tasks[trigger_id] = asyncio.create_task(_mqtt_loop(trigger_id, config))


async def _mqtt_loop(trigger_id: int, config: dict):
    """Run paho-mqtt in a thread since it's synchronous."""
    import paho.mqtt.client as mqtt

    host = config.get("broker", config.get("host", "localhost"))
    port = config.get("port", 1883)
    username = config.get("username")
    password = config.get("password")
    topic = config.get("topic", "wol_xyz/#")
    device_mac = config.get("device_mac", "")

    loop = asyncio.get_event_loop()

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            _status[trigger_id] = "connected"
            logger.info("MQTT trigger %d connected to %s:%d", trigger_id, host, port)
            client.subscribe(topic)
        else:
            _status[trigger_id] = "disconnected"
            logger.error("MQTT trigger %d connect failed: rc=%d", trigger_id, rc)

    def on_disconnect(client, userdata, rc, properties=None, reason=None):
        _status[trigger_id] = "connecting"
        logger.warning("MQTT trigger %d disconnected (rc=%s), will reconnect", trigger_id, rc)

    def on_message(client, userdata, msg):
        payload = msg.payload.decode(errors="ignore").strip().lower()
        if payload in ("on", "wake", "1"):
            action = "wake"
        elif payload in ("off", "shutdown", "0"):
            action = "shutdown"
        else:
            try:
                data = json.loads(msg.payload)
                action = data.get("action", "")
                if action not in ("wake", "shutdown"):
                    return
            except Exception:
                return

        asyncio.run_coroutine_threadsafe(_handle_mqtt(action, device_mac), loop)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if username:
        client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    backoff = 5
    fail_count = 0
    ever_connected = False
    while True:
        try:
            await loop.run_in_executor(None, lambda: client.connect(host, port, 60))
            if not ever_connected:
                ever_connected = True
            backoff = 5
            fail_count = 0
            await loop.run_in_executor(None, client.loop_forever)
        except asyncio.CancelledError:
            _status.pop(trigger_id, None)
            client.disconnect()
            break
        except Exception as e:
            fail_count += 1
            _status[trigger_id] = "disconnected"
            if fail_count == 1:
                log = logger.error if ever_connected else logger.warning
                log("MQTT trigger %d error: %s", trigger_id, e)
            elif fail_count == 2:
                logger.warning("MQTT trigger %d still failing, retrying every %ds", trigger_id, backoff)
            _status[trigger_id] = "connecting"
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 300)


async def _handle_mqtt(action: str, device_mac: str):
    async with async_session() as db:
        device = None
        if device_mac:
            device = (await db.execute(
                select(Device).where(Device.mac == device_mac.upper())
            )).scalar_one_or_none()
        if not device:
            logger.warning("MQTT: device %s not found", device_mac)
            return

        from .log_writer import write_log
        if action == "wake":
            from .wol import send_wol
            ok, detail = await send_wol(device.mac)
        else:
            from .shutdown import send_shutdown
            from ..crypto import decrypt
            if not device.shutdown_enabled:
                return
            pwd = decrypt(device.shutdown_password_enc) if device.shutdown_auth_type == "password" else ""
            key = decrypt(device.shutdown_key_enc) if device.shutdown_auth_type == "key" else None
            ok, detail = await send_shutdown(
                device.ip, device.shutdown_user, pwd,
                private_key=key, device_type=device.device_type,
            )

        await write_log(db, device.id, action, "success" if ok else "failure", detail, "external")
        if ok:
            from .ping_monitor import register_pending_check
            register_pending_check(device.id, action, device.name)

        device_name = device.name

    from .notification import notify_all
    await notify_all(
        f"MQTT 触发 {'成功' if ok else '失败'}",
        f"设备: {device_name} | 动作: {action} | {detail}",
    )


def stop_all():
    for t in _tasks.values():
        t.cancel()
    _tasks.clear()
    _status.clear()
