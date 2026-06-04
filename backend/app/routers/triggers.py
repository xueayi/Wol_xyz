from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db, async_session
from ..auth import get_current_user
from ..models.trigger import TriggerSource
from ..models.channel import NotificationChannel
from ..models.device import Device
from ..schemas.trigger import TriggerCreate, TriggerUpdate, TriggerOut

router = APIRouter(tags=["triggers"])
mgmt_router = APIRouter(prefix="/api/triggers", tags=["triggers"], dependencies=[Depends(get_current_user)])


@mgmt_router.get("", response_model=List[TriggerOut])
async def list_triggers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TriggerSource).order_by(TriggerSource.id))
    return result.scalars().all()


@mgmt_router.post("", response_model=TriggerOut, status_code=201)
async def create_trigger(body: TriggerCreate, db: AsyncSession = Depends(get_db)):
    trigger = TriggerSource(**body.model_dump())
    db.add(trigger)
    await db.commit()
    await db.refresh(trigger)
    if trigger.type == "telegram" and trigger.config.get("sync_notify"):
        await _sync_telegram_channel(db, trigger)
    return trigger


@mgmt_router.put("/{trigger_id}", response_model=TriggerOut)
async def update_trigger(trigger_id: int, body: TriggerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TriggerSource).where(TriggerSource.id == trigger_id))
    trigger = result.scalar_one_or_none()
    if not trigger:
        raise HTTPException(status_code=404, detail="触发源不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(trigger, k, v)
    await db.commit()
    await db.refresh(trigger)
    if trigger.type == "telegram":
        if trigger.config.get("sync_notify"):
            await _sync_telegram_channel(db, trigger)
        else:
            await _remove_synced_channel(db, trigger.id)
    return trigger


@mgmt_router.delete("/{trigger_id}", status_code=204)
async def delete_trigger(trigger_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TriggerSource).where(TriggerSource.id == trigger_id))
    trigger = result.scalar_one_or_none()
    if not trigger:
        raise HTTPException(status_code=404, detail="触发源不存在")
    if trigger.type == "telegram":
        await _remove_synced_channel(db, trigger.id)
    await db.delete(trigger)
    await db.commit()


async def _sync_telegram_channel(db: AsyncSession, trigger: TriggerSource):
    """Create or update a notification channel that mirrors this Telegram trigger."""
    result = await db.execute(
        select(NotificationChannel).where(
            NotificationChannel.type == "telegram",
            NotificationChannel.config["_trigger_id"].as_integer() == trigger.id,
        )
    )
    ch = result.scalar_one_or_none()
    channel_config = {
        "bot_token": trigger.config.get("bot_token", ""),
        "chat_ids": trigger.config.get("allowed_chat_ids", ""),
        "_trigger_id": trigger.id,
    }
    if ch:
        ch.name = f"Telegram — {trigger.name}"
        ch.config = channel_config
        ch.enabled = trigger.enabled
    else:
        ch = NotificationChannel(
            type="telegram",
            name=f"Telegram — {trigger.name}",
            config=channel_config,
            enabled=trigger.enabled,
        )
        db.add(ch)
    await db.commit()


async def _remove_synced_channel(db: AsyncSession, trigger_id: int):
    result = await db.execute(
        select(NotificationChannel).where(
            NotificationChannel.type == "telegram",
            NotificationChannel.config["_trigger_id"].as_integer() == trigger_id,
        )
    )
    ch = result.scalar_one_or_none()
    if ch:
        await db.delete(ch)
        await db.commit()


@router.api_route("/api/external/trigger", methods=["GET", "POST"])
async def external_trigger(
    request: Request,
    token: str = Query(...),
    mac: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    action: str = Query("wake"),
):
    """Token-based external HTTP API trigger (no JWT required)."""
    async with async_session() as db:
        triggers = (await db.execute(
            select(TriggerSource).where(TriggerSource.type == "http_api", TriggerSource.enabled.is_(True))
        )).scalars().all()

        valid = any(t.config.get("token") == token for t in triggers)
        if not valid:
            raise HTTPException(status_code=403, detail="Token 无效")

        device = None
        if device_id:
            device = (await db.execute(select(Device).where(Device.id == device_id))).scalar_one_or_none()
        elif mac:
            device = (await db.execute(select(Device).where(Device.mac == mac.upper()))).scalar_one_or_none()

        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

        from ..services.log_writer import write_log
        if action == "wake":
            from ..services.wol import send_wol
            ok, detail = await send_wol(device.mac)
        elif action == "shutdown":
            from ..services.shutdown import send_shutdown
            from ..crypto import decrypt
            if not device.shutdown_enabled:
                raise HTTPException(status_code=400, detail="该设备未启用远程关机")
            pwd = decrypt(device.shutdown_password_enc)
            ok, detail = await send_shutdown(device.ip, device.shutdown_user, pwd)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的动作: {action}")

        await write_log(db, device.id, action, "success" if ok else "failure", detail, "external")
        return {"success": ok, "detail": detail}
