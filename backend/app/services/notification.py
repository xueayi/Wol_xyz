import logging
import aiosmtplib
from email.message import EmailMessage
import httpx
from sqlalchemy import select

from ..database import async_session
from ..models.channel import NotificationChannel

logger = logging.getLogger(__name__)


async def send_notification(channel: NotificationChannel, title: str, body: str) -> bool:
    try:
        if channel.type == "email":
            return await _send_email(channel.config, title, body)
        elif channel.type == "webhook":
            return await _send_webhook(channel.config, title, body)
        elif channel.type == "telegram":
            return await _send_telegram(channel.config, title, body)
        else:
            logger.warning("Unknown channel type: %s", channel.type)
            return False
    except Exception as e:
        logger.error("Notification error (%s): %s", channel.name, e)
        return False


async def _send_email(config: dict, title: str, body: str) -> bool:
    msg = EmailMessage()
    msg["From"] = config.get("from_addr", config.get("username", ""))
    msg["To"] = config["to_addr"]
    msg["Subject"] = title
    msg.set_content(body)

    await aiosmtplib.send(
        msg,
        hostname=config["host"],
        port=config.get("port", 587),
        start_tls=config.get("tls", True),
        username=config.get("username"),
        password=config.get("password"),
    )
    return True


async def _send_webhook(config: dict, title: str, body: str) -> bool:
    import json as _json
    url = config["url"]
    method = config.get("method", "POST").upper()

    raw_headers = config.get("headers", {})
    if isinstance(raw_headers, str):
        try:
            raw_headers = _json.loads(raw_headers)
        except _json.JSONDecodeError:
            raw_headers = {}
    headers = dict(raw_headers) if isinstance(raw_headers, dict) else {}

    payload = config.get("body_template", {"title": "{title}", "body": "{body}"})
    if isinstance(payload, str):
        try:
            payload = _json.loads(payload)
        except _json.JSONDecodeError:
            pass

    if "Content-Type" not in headers and "content-type" not in headers:
        headers["Content-Type"] = "application/json"

    def _render(v):
        if isinstance(v, str):
            return v.replace("{title}", title).replace("{body}", body)
        if isinstance(v, dict):
            return {k: _render(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_render(i) for i in v]
        return v

    data = _render(payload)
    async with httpx.AsyncClient(timeout=10) as client:
        if method == "GET":
            resp = await client.get(url, params=data if isinstance(data, dict) else {}, headers=headers)
        else:
            resp = await client.post(url, json=data, headers=headers)
        resp.raise_for_status()
    return True


async def _send_telegram(config: dict, title: str, body: str) -> bool:
    bot_token = config.get("bot_token", "")
    chat_ids_raw = config.get("chat_ids", "")
    if not bot_token or not chat_ids_raw:
        return False

    chat_ids = []
    if isinstance(chat_ids_raw, list):
        chat_ids = [int(x) for x in chat_ids_raw]
    elif isinstance(chat_ids_raw, str) and chat_ids_raw.strip():
        chat_ids = [int(x.strip()) for x in chat_ids_raw.split(",") if x.strip()]

    text = f"<b>{title}</b>\n{body}"
    async with httpx.AsyncClient(timeout=10) as client:
        for cid in chat_ids:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": cid, "text": text, "parse_mode": "HTML"},
            )
    return True


async def notify_all(title: str, body: str, event: str = "trigger"):
    """Send to all enabled channels that subscribe to this event type.
    event: 'trigger' for command-sent notifications, 'success' for confirmed state-change notifications.
    """
    async with async_session() as db:
        query = select(NotificationChannel).where(NotificationChannel.enabled.is_(True))
        if event == "trigger":
            query = query.where(NotificationChannel.notify_on_trigger.is_(True))
        elif event == "success":
            query = query.where(NotificationChannel.notify_on_success.is_(True))
        result = await db.execute(query)
        channels = result.scalars().all()

    for ch in channels:
        try:
            await send_notification(ch, title, body)
        except Exception as e:
            logger.error("Notify via %s failed: %s", ch.name, e)
