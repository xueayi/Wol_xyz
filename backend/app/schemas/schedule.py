from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from ..tz import ensure_tz


class ScheduleCreate(BaseModel):
    name: str
    device_id: int
    action: str  # wake / shutdown
    cron_expression: str
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    device_id: Optional[int] = None
    action: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None


class ScheduleOut(BaseModel):
    id: int
    name: str
    device_id: int
    action: str
    cron_expression: str
    enabled: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime

    @field_validator("last_run_at", "next_run_at", "created_at", mode="before")
    @classmethod
    def apply_tz(cls, v):
        if isinstance(v, datetime):
            return ensure_tz(v)
        return v

    model_config = {"from_attributes": True}
