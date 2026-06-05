from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from ..auth import get_current_user
from ..config import settings as app_settings
from ..services.proxy import get_proxy_config, save_proxy_config, build_proxy_url

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(get_current_user)])


class ProxyConfig(BaseModel):
    proxy_enabled: bool = False
    proxy_type: str = "http"
    proxy_host: str = ""
    proxy_port: int = 7890
    proxy_username: str = ""
    proxy_password: str = ""


@router.get("/timezone")
async def get_timezone():
    return {"timezone": app_settings.TZ}


@router.get("/proxy", response_model=ProxyConfig)
async def get_proxy():
    cfg = await get_proxy_config()
    return cfg


@router.put("/proxy", response_model=ProxyConfig)
async def update_proxy(body: ProxyConfig):
    data = body.model_dump()
    await save_proxy_config(data)
    return data


@router.post("/proxy/test")
async def test_proxy(body: ProxyConfig):
    """Test proxy connectivity regardless of the enabled switch."""
    import httpx
    test_cfg = body.model_dump()
    test_cfg["proxy_enabled"] = True
    proxy_url = build_proxy_url(test_cfg)
    if not proxy_url:
        return {"success": False, "detail": "请填写代理地址"}
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10) as client:
            resp = await client.get("https://httpbin.org/ip")
            data = resp.json()
            return {"success": True, "detail": f"代理连接成功，出口 IP: {data.get('origin', '未知')}"}
    except Exception as e:
        return {"success": False, "detail": f"代理连接失败: {str(e)}"}
