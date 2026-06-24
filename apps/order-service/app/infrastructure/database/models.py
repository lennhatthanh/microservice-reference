from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    payment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    items: Mapped[list["OrderItemModel"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(36), index=True)
    product_name_snapshot: Mapped[str] = mapped_column(String(255))
    price_snapshot: Mapped[float] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    order: Mapped[OrderModel] = relationship(back_populates="items")


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
