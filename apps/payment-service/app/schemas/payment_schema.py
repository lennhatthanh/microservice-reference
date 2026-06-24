from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProcessPaymentRequest(BaseModel):
    order_id: UUID
    user_id: UUID
    amount: Decimal = Field(gt=0)
    provider: str = Field(default="fake_provider", min_length=1, max_length=100)
    force_fail: bool = False


class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    status: str
    provider: str
    failure_reason: str | None = None
