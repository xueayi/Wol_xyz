"""Centralised timezone helper. All datetime generation should use tz_now()."""

from datetime import datetime
from zoneinfo import ZoneInfo

from .config import settings

APP_TZ = ZoneInfo(settings.TZ)


def tz_now() -> datetime:
    """Return the current time with the configured timezone (default: Asia/Shanghai)."""
    return datetime.now(APP_TZ)


def ensure_tz(dt: datetime) -> datetime:
    """Attach APP_TZ to a naive datetime (assumed to be in the app timezone),
    or convert an aware datetime to APP_TZ."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=APP_TZ)
    return dt.astimezone(APP_TZ)
