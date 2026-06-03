from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.log import OperationLog


async def write_log(
    db: AsyncSession,
    device_id: Optional[int],
    action: str,
    result: str,
    detail: str = "",
    source: str = "manual",
):
    log = OperationLog(
        device_id=device_id, action=action,
        result=result, detail=detail, source=source,
    )
    db.add(log)
    await db.commit()
