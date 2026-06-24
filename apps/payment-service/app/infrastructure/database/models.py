from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    provider: Mapped[str] = mapped_column(String(100), default="fake_provider")
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OutboxEventModel(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class InboxEventModel(Base):
    __tablename__ = "inbox_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="PROCESSING", index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
