from decimal import Decimal
from uuid import UUID

from .base import IntegrationEvent


class PaymentSucceeded(IntegrationEvent):
    event_type: str = "PaymentSucceeded"
    source: str = "payment-service"
    payment_id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    provider: str


class PaymentFailed(IntegrationEvent):
    event_type: str = "PaymentFailed"
    source: str = "payment-service"
    payment_id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    reason: str
    provider: str
