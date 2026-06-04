from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    mac: Mapped[str] = mapped_column(String(17), nullable=False)
    adapter_name: Mapped[str] = mapped_column(String(64), default="")
    device_type: Mapped[str] = mapped_column(String(16), default="computer")
    group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("device_groups.id", ondelete="SET NULL"), nullable=True)
    shutdown_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    shutdown_user: Mapped[str] = mapped_column(String(64), default="")
    shutdown_password_enc: Mapped[str] = mapped_column(String(256), default="")
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group: Mapped[Optional["DeviceGroup"]] = relationship(back_populates="devices")  # noqa: F821
