from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models.device import Device
from ..models.user import User
from ..schemas.device import DeviceCreate, DeviceUpdate, DeviceOut
from ..crypto import encrypt
from typing import Optional

router = APIRouter(prefix="/api/devices", tags=["devices"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[DeviceOut])
async def list_devices(group_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    q = select(Device)
    if group_id is not None:
        q = q.where(Device.group_id == group_id)
    q = q.order_by(Device.group_id, Device.id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=DeviceOut, status_code=201)
async def create_device(body: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device = Device(
        name=body.name, ip=body.ip, mac=body.mac.upper(),
        adapter_name=body.adapter_name, group_id=body.group_id,
        shutdown_enabled=body.shutdown_enabled, shutdown_user=body.shutdown_user,
        shutdown_password_enc=encrypt(body.shutdown_password),
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.put("/{device_id}", response_model=DeviceOut)
async def update_device(device_id: int, body: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    update_data = body.model_dump(exclude_unset=True)
    if "shutdown_password" in update_data:
        update_data["shutdown_password_enc"] = encrypt(update_data.pop("shutdown_password"))
    for k, v in update_data.items():
        if k == "mac" and v:
            v = v.upper()
        setattr(device, k, v)
    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=204)
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await db.delete(device)
    await db.commit()


@router.post("/{device_id}/wake")
async def wake_device(device_id: int, db: AsyncSession = Depends(get_db)):
    from ..services.wol import send_wol
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    success, detail = await send_wol(device.mac)
    from ..services.log_writer import write_log
    await write_log(db, device.id, "wake", "success" if success else "failure", detail, "manual")
    return {"success": success, "detail": detail}


@router.post("/{device_id}/shutdown")
async def shutdown_device(device_id: int, db: AsyncSession = Depends(get_db)):
    from ..services.shutdown import send_shutdown
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    if not device.shutdown_enabled:
        raise HTTPException(status_code=400, detail="该设备未启用远程关机")
    from ..crypto import decrypt
    pwd = decrypt(device.shutdown_password_enc)
    success, detail = await send_shutdown(device.ip, device.shutdown_user, pwd)
    from ..services.log_writer import write_log
    await write_log(db, device.id, "shutdown", "success" if success else "failure", detail, "manual")
    return {"success": success, "detail": detail}
