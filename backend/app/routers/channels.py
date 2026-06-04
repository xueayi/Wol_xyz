from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models.channel import NotificationChannel
from ..schemas.channel import ChannelCreate, ChannelUpdate, ChannelOut

router = APIRouter(prefix="/api/channels", tags=["channels"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[ChannelOut])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationChannel).order_by(NotificationChannel.id))
    return result.scalars().all()


@router.post("", response_model=ChannelOut, status_code=201)
async def create_channel(body: ChannelCreate, db: AsyncSession = Depends(get_db)):
    ch = NotificationChannel(**body.model_dump())
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ch


@router.put("/{ch_id}", response_model=ChannelOut)
async def update_channel(ch_id: int, body: ChannelUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationChannel).where(NotificationChannel.id == ch_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ch, k, v)
    await db.commit()
    await db.refresh(ch)
    return ch


@router.delete("/{ch_id}", status_code=204)
async def delete_channel(ch_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationChannel).where(NotificationChannel.id == ch_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    await db.delete(ch)
    await db.commit()


@router.post("/{ch_id}/test")
async def test_channel(ch_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationChannel).where(NotificationChannel.id == ch_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    from ..services.notification import send_notification
    ok = await send_notification(ch, "Wol_xyz 测试通知", "如果您看到此消息，说明通知渠道配置正确。")
    return {"success": ok}
