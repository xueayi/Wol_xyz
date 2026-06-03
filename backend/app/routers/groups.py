from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models.group import DeviceGroup
from ..models.device import Device
from ..schemas.group import GroupCreate, GroupUpdate, GroupOut, GroupWithDevices

router = APIRouter(prefix="/api/groups", tags=["groups"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[GroupOut])
async def list_groups(db: AsyncSession = Depends(get_db)):
    q = select(DeviceGroup).order_by(DeviceGroup.sort_order, DeviceGroup.id)
    result = await db.execute(q)
    groups = result.scalars().all()
    out = []
    for g in groups:
        cnt_q = select(func.count()).select_from(Device).where(Device.group_id == g.id)
        cnt = (await db.execute(cnt_q)).scalar()
        obj = GroupOut.model_validate(g)
        obj.device_count = cnt
        out.append(obj)
    return out


@router.get("/with-devices", response_model=List[GroupWithDevices])
async def list_groups_with_devices(db: AsyncSession = Depends(get_db)):
    q = select(DeviceGroup).options(selectinload(DeviceGroup.devices)).order_by(DeviceGroup.sort_order, DeviceGroup.id)
    result = await db.execute(q)
    groups = result.scalars().unique().all()
    out = []
    for g in groups:
        obj = GroupWithDevices.model_validate(g)
        obj.device_count = len(g.devices)
        out.append(obj)
    # also include ungrouped devices
    ungrouped_q = select(Device).where(Device.group_id.is_(None))
    ungrouped = (await db.execute(ungrouped_q)).scalars().all()
    if ungrouped:
        from ..schemas.device import DeviceOut
        ug = GroupWithDevices(
            id=0, name="未分组", icon="folder", sort_order=9999,
            created_at=groups[0].created_at if groups else ungrouped[0].created_at,
            device_count=len(ungrouped),
            devices=[DeviceOut.model_validate(d) for d in ungrouped],
        )
        out.append(ug)
    return out


@router.post("", response_model=GroupOut, status_code=201)
async def create_group(body: GroupCreate, db: AsyncSession = Depends(get_db)):
    group = DeviceGroup(name=body.name, icon=body.icon, sort_order=body.sort_order)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    obj = GroupOut.model_validate(group)
    obj.device_count = 0
    return obj


@router.put("/{group_id}", response_model=GroupOut)
async def update_group(group_id: int, body: GroupUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DeviceGroup).where(DeviceGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(group, k, v)
    await db.commit()
    await db.refresh(group)
    cnt = (await db.execute(select(func.count()).select_from(Device).where(Device.group_id == group.id))).scalar()
    obj = GroupOut.model_validate(group)
    obj.device_count = cnt
    return obj


@router.delete("/{group_id}", status_code=204)
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DeviceGroup).where(DeviceGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    await db.delete(group)
    await db.commit()
