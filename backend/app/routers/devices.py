from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models.device import Device
from ..models.user import User
from ..schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceOut,
    BatchDeleteRequest, BatchMoveRequest, BatchWakeRequest, BatchShutdownRequest,
)
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
        adapter_name=body.adapter_name, device_type=body.device_type,
        group_id=body.group_id,
        shutdown_enabled=body.shutdown_enabled, shutdown_user=body.shutdown_user,
        shutdown_password_enc=encrypt(body.shutdown_password),
        shutdown_auth_type=body.shutdown_auth_type,
        shutdown_key_enc=encrypt(body.shutdown_private_key),
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
    if "shutdown_private_key" in update_data:
        update_data["shutdown_key_enc"] = encrypt(update_data.pop("shutdown_private_key"))
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
    pwd = decrypt(device.shutdown_password_enc) if device.shutdown_auth_type == "password" else ""
    key = decrypt(device.shutdown_key_enc) if device.shutdown_auth_type == "key" else None
    success, detail = await send_shutdown(
        device.ip, device.shutdown_user, pwd,
        private_key=key, device_type=device.device_type,
    )
    from ..services.log_writer import write_log
    await write_log(db, device.id, "shutdown", "success" if success else "failure", detail, "manual")
    return {"success": success, "detail": detail}


@router.post("/generate-keypair")
async def generate_keypair(user: User = Depends(get_current_user)):
    """Generate an Ed25519 SSH key pair and return both keys."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode()
    return {"private_key": private_pem, "public_key": public_key + " wol_xyz"}


@router.post("/batch-wake", status_code=200)
async def batch_wake_devices(body: BatchWakeRequest, db: AsyncSession = Depends(get_db)):
    """Batch wake devices by IDs or by group_id."""
    from ..services.wol import send_wol
    from ..services.log_writer import write_log

    q = select(Device)
    if body.ids:
        q = q.where(Device.id.in_(body.ids))
    elif body.group_id is not None:
        q = q.where(Device.group_id == body.group_id)
    else:
        raise HTTPException(status_code=400, detail="请指定设备ID列表或分组ID")

    result = await db.execute(q)
    devices = result.scalars().all()
    if not devices:
        raise HTTPException(status_code=404, detail="未找到匹配的设备")

    results = []
    for device in devices:
        ok, detail = await send_wol(device.mac)
        await write_log(db, device.id, "wake", "success" if ok else "failure", detail, "manual")
        results.append({"device_id": device.id, "name": device.name, "success": ok, "detail": detail})
    return {"total": len(results), "results": results}


@router.post("/batch-shutdown", status_code=200)
async def batch_shutdown_devices(body: BatchShutdownRequest, db: AsyncSession = Depends(get_db)):
    """Batch shutdown devices by IDs or by group_id."""
    from ..services.shutdown import send_shutdown
    from ..services.log_writer import write_log
    from ..crypto import decrypt

    q = select(Device)
    if body.ids:
        q = q.where(Device.id.in_(body.ids))
    elif body.group_id is not None:
        q = q.where(Device.group_id == body.group_id)
    else:
        raise HTTPException(status_code=400, detail="请指定设备ID列表或分组ID")

    result = await db.execute(q)
    devices = result.scalars().all()
    if not devices:
        raise HTTPException(status_code=404, detail="未找到匹配的设备")

    results = []
    for device in devices:
        if not device.shutdown_enabled:
            results.append({
                "device_id": device.id, "name": device.name,
                "success": False, "detail": "未启用远程关机",
            })
            continue
        pwd = decrypt(device.shutdown_password_enc) if device.shutdown_auth_type == "password" else ""
        key = decrypt(device.shutdown_key_enc) if device.shutdown_auth_type == "key" else None
        ok, detail = await send_shutdown(
            device.ip, device.shutdown_user, pwd,
            private_key=key, device_type=device.device_type,
        )
        await write_log(db, device.id, "shutdown", "success" if ok else "failure", detail, "manual")
        results.append({"device_id": device.id, "name": device.name, "success": ok, "detail": detail})
    return {"total": len(results), "results": results}


@router.post("/batch-delete", status_code=200)
async def batch_delete_devices(body: BatchDeleteRequest, db: AsyncSession = Depends(get_db)):
    if not body.ids:
        raise HTTPException(status_code=400, detail="请选择至少一个设备")
    result = await db.execute(select(Device).where(Device.id.in_(body.ids)))
    devices = result.scalars().all()
    for device in devices:
        await db.delete(device)
    await db.commit()
    return {"deleted": len(devices)}


@router.post("/batch-move", status_code=200)
async def batch_move_devices(body: BatchMoveRequest, db: AsyncSession = Depends(get_db)):
    if not body.ids:
        raise HTTPException(status_code=400, detail="请选择至少一个设备")
    result = await db.execute(select(Device).where(Device.id.in_(body.ids)))
    devices = result.scalars().all()
    for device in devices:
        device.group_id = body.group_id
    await db.commit()
    return {"moved": len(devices)}
