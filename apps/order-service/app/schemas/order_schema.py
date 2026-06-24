from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateOrderItem(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    user_id: UUID
    items: list[CreateOrderItem] = Field(min_length=1)
    force_payment_fail: bool = False


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name_snapshot: str
    price_snapshot: Decimal
    quantity: int


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    total_amount: Decimal
    payment_id: UUID | None = None
    cancellation_reason: str | None = None
    items: list[OrderItemResponse] = []
