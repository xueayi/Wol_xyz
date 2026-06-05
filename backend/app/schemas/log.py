from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from ..tz import ensure_tz


class LogOut(BaseModel):
    id: int
    device_id: Optional[int]
    device_name: Optional[str] = None
    action: str
    result: str
    detail: str
    source: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def apply_tz(cls, v: datetime) -> datetime:
        if isinstance(v, datetime):
            return ensure_tz(v)
        return v

    model_config = {"from_attributes": True}
