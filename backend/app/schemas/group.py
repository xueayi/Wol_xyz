from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    icon: str = "desktop"
    sort_order: int = 0


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class GroupOut(BaseModel):
    id: int
    name: str
    icon: str
    sort_order: int
    created_at: datetime
    device_count: int = 0

    model_config = {"from_attributes": True}


class GroupWithDevices(GroupOut):
    devices: List["DeviceOut"] = []  # noqa: F821

    model_config = {"from_attributes": True}


from .device import DeviceOut  # noqa: E402
GroupWithDevices.model_rebuild()
