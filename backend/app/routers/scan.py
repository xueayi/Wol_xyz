from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models.device import Device

router = APIRouter(prefix="/api/scan", tags=["scan"], dependencies=[Depends(get_current_user)])

_HOSTNAME_TYPE_RULES = [
    ("ipad", "ipad"),
    ("iphone", "iphone"),
    ("apple-watch", "watch"),
    ("watch", "watch"),
    ("macbook", "macos"),
    ("imac", "macos"),
    ("mac-mini", "macos"),
    ("mac-studio", "macos"),
    ("android", "android"),
    ("pixel", "android"),
]


@router.post("/start")
async def start_scan(db: AsyncSession = Depends(get_db)):
    from ..services.scanner import scan_lan

    try:
        devices = await scan_lan()
    except RuntimeError as e:
        if "scan_already_running" in str(e):
            raise HTTPException(status_code=409, detail="扫描正在进行中，请稍候")
        raise

    for d in devices:
        d["guessed_type"] = "computer"
        hostname = d.get("hostname", "").lower()
        if hostname:
            for keyword, dtype in _HOSTNAME_TYPE_RULES:
                if keyword in hostname:
                    d["guessed_type"] = dtype
                    break

    existing = (await db.execute(select(Device.mac))).scalars().all()
    existing_macs = [m.upper() for m in existing]
    return {"devices": devices, "existing_macs": existing_macs}
