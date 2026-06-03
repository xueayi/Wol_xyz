from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from ..auth import get_current_user
from ..models.log import OperationLog
from ..models.device import Device
from ..schemas.log import LogOut

router = APIRouter(prefix="/api/logs", tags=["logs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[LogOut])
async def list_logs(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    device_id: Optional[int] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(OperationLog).order_by(OperationLog.created_at.desc())
    if device_id:
        q = q.where(OperationLog.device_id == device_id)
    if action:
        q = q.where(OperationLog.action == action)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    logs = result.scalars().all()

    device_ids = {l.device_id for l in logs if l.device_id}
    names = {}
    if device_ids:
        dr = await db.execute(select(Device.id, Device.name).where(Device.id.in_(device_ids)))
        names = {row.id: row.name for row in dr}

    out = []
    for l in logs:
        obj = LogOut.model_validate(l)
        obj.device_name = names.get(l.device_id)
        out.append(obj)
    return out


@router.get("/count")
async def log_count(db: AsyncSession = Depends(get_db)):
    cnt = (await db.execute(select(func.count()).select_from(OperationLog))).scalar()
    return {"count": cnt}
