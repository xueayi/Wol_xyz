from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models.device import Device

router = APIRouter(prefix="/api/scan", tags=["scan"], dependencies=[Depends(get_current_user)])


@router.post("/start")
async def start_scan(db: AsyncSession = Depends(get_db)):
    from ..services.scanner import scan_lan
    from ..services.oui_detect import guess_device_type
    devices = await scan_lan()
    for d in devices:
        oui_type = guess_device_type(d["mac"])
        hostname = d.get("hostname", "").lower()
        if hostname:
            if "ipad" in hostname:
                oui_type = "ipad"
            elif "iphone" in hostname:
                oui_type = "iphone"
            elif "watch" in hostname or "apple-watch" in hostname:
                oui_type = "watch"
            elif "macbook" in hostname or "imac" in hostname or "mac-mini" in hostname or "mac-studio" in hostname:
                oui_type = "macos"
            elif "android" in hostname or "pixel" in hostname:
                oui_type = "android"
        d["guessed_type"] = oui_type
    existing = (await db.execute(select(Device.mac))).scalars().all()
    existing_macs = [m.upper() for m in existing]
    return {"devices": devices, "existing_macs": existing_macs}
