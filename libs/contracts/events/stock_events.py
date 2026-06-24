from uuid import UUID

from decimal import Decimal
from pydantic import BaseModel

from .base import IntegrationEvent


class StockReservationItemPayload(BaseModel):
    product_id: UUID
    quantity: int


class StockReserved(IntegrationEvent):
    event_type: str = "StockReserved"
    source: str = "product-service"
    reservation_id: UUID
    order_id: UUID
    user_id: UUID
    total_amount: Decimal
    items: list[StockReservationItemPayload]


class StockReservationFailed(IntegrationEvent):
    event_type: str = "StockReservationFailed"
    source: str = "product-service"
    order_id: UUID
    failed_items: list[StockReservationItemPayload]
    reason: str
