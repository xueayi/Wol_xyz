from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_user
from ..models.device import Device
from ..models.group import DeviceGroup
from ..models.schedule import ScheduledTask
from ..models.log import OperationLog
from ..schemas.dashboard import DashboardStats
from ..config import APP_VERSION
from ..tz import tz_now

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/stats", response_model=DashboardStats)
async def stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(Device))).scalar()
    online = (await db.execute(select(func.count()).select_from(Device).where(Device.is_online.is_(True)))).scalar()
    groups = (await db.execute(select(func.count()).select_from(DeviceGroup))).scalar()
    schedules = (await db.execute(select(func.count()).select_from(ScheduledTask))).scalar()

    today_start = tz_now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_triggers = (await db.execute(
        select(func.count()).select_from(OperationLog).where(OperationLog.created_at >= today_start)
    )).scalar()

    return DashboardStats(
        total_devices=total, online_devices=online,
        group_count=groups, schedule_count=schedules,
        today_triggers=today_triggers,
        version=APP_VERSION,
    )
