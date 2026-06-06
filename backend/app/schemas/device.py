from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from ..tz import ensure_tz


class DeviceCreate(BaseModel):
    name: str
    ip: str
    mac: str
    adapter_name: str = ""
    device_type: str = "computer"
    group_id: Optional[int] = None
    shutdown_enabled: bool = False
    shutdown_user: str = ""
    shutdown_password: str = ""
    shutdown_auth_type: str = "password"
    shutdown_private_key: str = ""


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    adapter_name: Optional[str] = None
    device_type: Optional[str] = None
    group_id: Optional[int] = None
    shutdown_enabled: Optional[bool] = None
    shutdown_user: Optional[str] = None
    shutdown_password: Optional[str] = None
    shutdown_auth_type: Optional[str] = None
    shutdown_private_key: Optional[str] = None


class DeviceOut(BaseModel):
    id: int
    name: str
    ip: str
    mac: str
    adapter_name: str
    device_type: str
    group_id: Optional[int]
    shutdown_enabled: bool
    shutdown_user: str
    shutdown_auth_type: str
    has_password: bool = False
    has_private_key: bool = False
    is_online: bool
    last_seen_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @field_validator("last_seen_at", "created_at", "updated_at", mode="before")
    @classmethod
    def apply_tz(cls, v):
        if isinstance(v, datetime):
            return ensure_tz(v)
        return v

    model_config = {"from_attributes": True}


class BatchDeleteRequest(BaseModel):
    ids: list[int]


class BatchMoveRequest(BaseModel):
    ids: list[int]
    group_id: Optional[int] = None


class BatchWakeRequest(BaseModel):
    ids: Optional[list[int]] = None
    group_id: Optional[int] = None


class BatchShutdownRequest(BaseModel):
    ids: Optional[list[int]] = None
    group_id: Optional[int] = None
