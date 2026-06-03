from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models.announcement import Announcement
from ..schemas.announcement import AnnouncementCreate, AnnouncementUpdate, AnnouncementOut

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


@router.get("", response_model=List[AnnouncementOut])
async def list_announcements(db: AsyncSession = Depends(get_db)):
    q = select(Announcement).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=AnnouncementOut, status_code=201, dependencies=[Depends(get_current_user)])
async def create_announcement(body: AnnouncementCreate, db: AsyncSession = Depends(get_db)):
    ann = Announcement(**body.model_dump())
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann


@router.put("/{ann_id}", response_model=AnnouncementOut, dependencies=[Depends(get_current_user)])
async def update_announcement(ann_id: int, body: AnnouncementUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ann, k, v)
    await db.commit()
    await db.refresh(ann)
    return ann


@router.delete("/{ann_id}", status_code=204, dependencies=[Depends(get_current_user)])
async def delete_announcement(ann_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")
    await db.delete(ann)
    await db.commit()
