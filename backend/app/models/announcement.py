from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from ..tz import tz_now


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=tz_now, onupdate=tz_now)
