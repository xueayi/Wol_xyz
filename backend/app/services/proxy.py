import json
import logging
from typing import Optional

import httpx
from sqlalchemy import select

from ..database import async_session
from ..models.setting import Setting

logger = logging.getLogger(__name__)

_PROXY_KEYS = ("proxy_enabled", "proxy_type", "proxy_host", "proxy_port", "proxy_username", "proxy_password")

_DEFAULTS = {
    "proxy_enabled": "false",
    "proxy_type": "http",
    "proxy_host": "",
    "proxy_port": "7890",
    "proxy_username": "",
    "proxy_password": "",
}


async def get_proxy_config() -> dict:
    async with async_session() as db:
        result = await db.execute(select(Setting).where(Setting.key.in_(_PROXY_KEYS)))
        rows = {r.key: r.value for r in result.scalars().all()}
    cfg = {k: rows.get(k, _DEFAULTS[k]) for k in _PROXY_KEYS}
    cfg["proxy_enabled"] = cfg["proxy_enabled"].lower() == "true"
    try:
        cfg["proxy_port"] = int(cfg["proxy_port"])
    except (ValueError, TypeError):
        cfg["proxy_port"] = 7890
    return cfg


async def save_proxy_config(cfg: dict):
    async with async_session() as db:
        for key in _PROXY_KEYS:
            val = str(cfg.get(key, _DEFAULTS[key]))
            existing = (await db.execute(select(Setting).where(Setting.key == key))).scalar_one_or_none()
            if existing:
                existing.value = val
            else:
                db.add(Setting(key=key, value=val))
        await db.commit()


def build_proxy_url(cfg: dict) -> Optional[str]:
    if not cfg.get("proxy_enabled"):
        return None
    host = cfg.get("proxy_host", "").strip()
    if not host:
        return None
    port = cfg.get("proxy_port", 7890)
    proxy_type = cfg.get("proxy_type", "http")
    scheme = "socks5" if proxy_type == "socks5" else "http"
    username = cfg.get("proxy_username", "").strip()
    password = cfg.get("proxy_password", "").strip()
    if username:
        return f"{scheme}://{username}:{password}@{host}:{port}"
    return f"{scheme}://{host}:{port}"


async def get_httpx_client(**kwargs) -> httpx.AsyncClient:
    cfg = await get_proxy_config()
    proxy_url = build_proxy_url(cfg)
    if proxy_url:
        kwargs.setdefault("proxy", proxy_url)
    kwargs.setdefault("timeout", 30)
    return httpx.AsyncClient(**kwargs)
