from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from ..tz import ensure_tz


class AnnouncementCreate(BaseModel):
    title: str
    content: str = ""
    is_pinned: bool = False


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def apply_tz(cls, v):
        if isinstance(v, datetime):
            return ensure_tz(v)
        return v

    model_config = {"from_attributes": True}
