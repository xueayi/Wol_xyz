from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models.schedule import ScheduledTask
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleOut

router = APIRouter(prefix="/api/schedules", tags=["schedules"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[ScheduleOut])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).order_by(ScheduledTask.id))
    return result.scalars().all()


@router.post("", response_model=ScheduleOut, status_code=201)
async def create_schedule(body: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    task = ScheduledTask(**body.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    from ..services.scheduler import scheduler_service
    scheduler_service.add_task(task)
    return task


@router.put("/{task_id}", response_model=ScheduleOut)
async def update_schedule(task_id: int, body: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    from ..services.scheduler import scheduler_service
    scheduler_service.update_task(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_schedule(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    from ..services.scheduler import scheduler_service
    scheduler_service.remove_task(task_id)
    await db.delete(task)
    await db.commit()
