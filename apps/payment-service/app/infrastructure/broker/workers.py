from threading import Thread

from app.application.services.payment_service import PaymentService
from app.core.config import settings
from app.infrastructure.database.models import InboxEventModel, OutboxEventModel
from app.infrastructure.database.session import SessionLocal
from libs.common.broker import RabbitMQClient
from libs.common.inbox import mark_event_processed
from libs.common.outbox import OutboxPublisher


def start_mq_workers() -> None:
    """Start Payment Service MQ workers.

    Consumer responsibility: handle StockReserved and process fake payment.
    Publisher responsibility: send PaymentSucceeded or PaymentFailed.
    """

    if not settings.ENABLE_MQ or not settings.RABBITMQ_URL:
        return

    broker = RabbitMQClient(settings.RABBITMQ_URL)
    publisher = OutboxPublisher(SessionLocal, OutboxEventModel, broker)
    Thread(target=publisher.run_forever, daemon=True).start()

    def handle_event(event: dict) -> None:
        db = SessionLocal()
        try:
            if not mark_event_processed(db, InboxEventModel, event):
                db.commit()
                return
            PaymentService(db).process_payment_from_event(event)
            db.get(InboxEventModel, event["event_id"]).status = "PROCESSED"
            db.commit()
        finally:
            db.close()

    Thread(
        target=lambda: broker.consume(
            queue="payment-service.stock-reserved",
            bindings=["StockReserved"],
            handler=handle_event,
        ),
        daemon=True,
    ).start()
