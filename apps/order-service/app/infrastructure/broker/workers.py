from threading import Thread

from app.application.services import OrderService
from app.core.config import settings
from app.infrastructure.database.models import InboxEventModel, OutboxEventModel
from app.infrastructure.database.session import SessionLocal
from libs.common.broker import RabbitMQClient
from libs.common.inbox import mark_event_processed
from libs.common.outbox import OutboxPublisher


def start_mq_workers() -> None:
    """Start Order Service MQ workers.

    Order service is the Saga Orchestrator. It reacts to stock/payment events
    and emits final order events through its outbox.
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
            service = OrderService(db)
            event_type = event.get("event_type")
            if event_type == "StockReservationFailed":
                service.handle_stock_reservation_failed(event)
            elif event_type == "PaymentSucceeded":
                service.handle_payment_succeeded(event)
            elif event_type == "PaymentFailed":
                service.handle_payment_failed(event)
            db.get(InboxEventModel, event["event_id"]).status = "PROCESSED"
            db.commit()
        finally:
            db.close()

    Thread(
        target=lambda: broker.consume(
            queue="order-service.saga-events",
            bindings=["StockReservationFailed", "PaymentSucceeded", "PaymentFailed"],
            handler=handle_event,
        ),
        daemon=True,
    ).start()
