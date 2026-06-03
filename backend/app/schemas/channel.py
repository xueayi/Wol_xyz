from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChannelCreate(BaseModel):
    type: str  # email / webhook
    name: str
    config: dict = {}
    enabled: bool = True


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None


class ChannelOut(BaseModel):
    id: int
    type: str
    name: str
    config: dict
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
