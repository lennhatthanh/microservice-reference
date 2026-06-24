from sqlalchemy.orm import Session

from app.infrastructure.database.models import PaymentModel
from app.infrastructure.outbox.service import add_outbox_event
from app.infrastructure.repositories import PaymentRepository
from app.schemas.payment_schema import ProcessPaymentRequest
from libs.contracts.events import PaymentFailed, PaymentSucceeded


class PaymentService:
    """Application service for the Payment bounded context.

    The provider is fake for local learning, but the boundary is real: Order
    service never writes payment rows directly.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.payments = PaymentRepository(db)

    def process_payment(self, payload: ProcessPaymentRequest) -> PaymentModel:
        existing = self.payments.get_by_order_id(str(payload.order_id))
        if existing:
            # Idempotent consumer guard: a retried StockReserved event should
            # return the existing payment instead of charging twice.
            return existing

        failed = payload.force_fail
        payment = PaymentModel(
            order_id=str(payload.order_id),
            user_id=str(payload.user_id),
            amount=payload.amount,
            provider=payload.provider,
            status="FAILED" if failed else "SUCCEEDED",
            failure_reason="Forced fake payment failure" if failed else None,
        )
        self.payments.add(payment)
        self.db.flush()
        if payment.status == "SUCCEEDED":
            add_outbox_event(
                self.db,
                PaymentSucceeded(
                    payment_id=payment.id,
                    order_id=payment.order_id,
                    user_id=payment.user_id,
                    amount=payment.amount,
                    provider=payment.provider,
                ),
            )
        else:
            add_outbox_event(
                self.db,
                PaymentFailed(
                    payment_id=payment.id,
                    order_id=payment.order_id,
                    user_id=payment.user_id,
                    amount=payment.amount,
                    provider=payment.provider,
                    reason=payment.failure_reason or "PAYMENT_FAILED",
                ),
            )
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def process_payment_from_event(self, event: dict) -> PaymentModel:
        """Consumer-side use case for async saga after StockReserved."""

        return self.process_payment(
            ProcessPaymentRequest(
                order_id=event["order_id"],
                user_id=event["user_id"],
                amount=event["total_amount"],
            )
        )
