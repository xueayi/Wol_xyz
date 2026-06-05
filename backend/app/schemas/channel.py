from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from ..tz import ensure_tz


class ChannelCreate(BaseModel):
    type: str  # email / webhook
    name: str
    config: dict = {}
    enabled: bool = True
    notify_on_trigger: bool = True
    notify_on_success: bool = False


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None
    notify_on_trigger: Optional[bool] = None
    notify_on_success: Optional[bool] = None


class ChannelOut(BaseModel):
    id: int
    type: str
    name: str
    config: dict
    enabled: bool
    notify_on_trigger: bool
    notify_on_success: bool
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def apply_tz(cls, v):
        if isinstance(v, datetime):
            return ensure_tz(v)
        return v

    model_config = {"from_attributes": True}
