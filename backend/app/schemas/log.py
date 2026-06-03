from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LogOut(BaseModel):
    id: int
    device_id: Optional[int]
    device_name: Optional[str] = None
    action: str
    result: str
    detail: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
