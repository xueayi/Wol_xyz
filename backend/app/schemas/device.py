from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DeviceCreate(BaseModel):
    name: str
    ip: str
    mac: str
    adapter_name: str = ""
    group_id: Optional[int] = None
    shutdown_enabled: bool = False
    shutdown_user: str = ""
    shutdown_password: str = ""


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    adapter_name: Optional[str] = None
    group_id: Optional[int] = None
    shutdown_enabled: Optional[bool] = None
    shutdown_user: Optional[str] = None
    shutdown_password: Optional[str] = None


class DeviceOut(BaseModel):
    id: int
    name: str
    ip: str
    mac: str
    adapter_name: str
    group_id: Optional[int]
    shutdown_enabled: bool
    shutdown_user: str
    is_online: bool
    last_seen_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
