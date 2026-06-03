from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_devices: int
    online_devices: int
    group_count: int
    schedule_count: int
    today_triggers: int
    version: str
