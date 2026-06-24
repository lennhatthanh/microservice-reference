from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from .base import IntegrationEvent


class OrderItemPayload(BaseModel):
    product_id: UUID
    product_name: str
    price: Decimal
    quantity: int


class OrderCreated(IntegrationEvent):
    event_type: str = "OrderCreated"
    source: str = "order-service"
    order_id: UUID
    user_id: UUID
    items: list[OrderItemPayload]
    total_amount: Decimal


class OrderCompleted(IntegrationEvent):
    event_type: str = "OrderCompleted"
    source: str = "order-service"
    order_id: UUID
    user_id: UUID


class OrderCancelled(IntegrationEvent):
    event_type: str = "OrderCancelled"
    source: str = "order-service"
    order_id: UUID
    user_id: UUID
    reason: str
