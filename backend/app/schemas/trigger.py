from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TriggerCreate(BaseModel):
    type: str  # bemfa / http_api / mqtt
    name: str
    config: dict = {}
    enabled: bool = True


class TriggerUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None


class TriggerOut(BaseModel):
    id: int
    type: str
    name: str
    config: dict
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
