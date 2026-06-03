from fastapi import APIRouter, Depends
from ..auth import get_current_user

router = APIRouter(prefix="/api/scan", tags=["scan"], dependencies=[Depends(get_current_user)])


@router.post("/start")
async def start_scan():
    from ..services.scanner import scan_lan
    devices = await scan_lan()
    return {"devices": devices}
