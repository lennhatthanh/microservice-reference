from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recipient: Mapped[str] = mapped_column(String(255), index=True)
    type: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(50), default="SENT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class InboxEventModel(Base):
    __tablename__ = "inbox_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="PROCESSING", index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
