from threading import Thread

from app.application.services.notification_service import NotificationService
from app.core.config import settings
from app.infrastructure.database.models import InboxEventModel
from app.infrastructure.database.session import SessionLocal
from app.schemas.notification_schema import CreateNotificationRequest
from libs.common.broker import RabbitMQClient
from libs.common.inbox import mark_event_processed


def start_mq_workers() -> None:
    """Start Notification Service consumers.

    Notification service is a pure consumer in this learning project. It records
    messages for user/order events instead of sending real email.
    """

    if not settings.ENABLE_MQ or not settings.RABBITMQ_URL:
        return

    broker = RabbitMQClient(settings.RABBITMQ_URL)

    def handle_event(event: dict) -> None:
        db = SessionLocal()
        try:
            if not mark_event_processed(db, InboxEventModel, event):
                db.commit()
                return
            event_type = event.get("event_type", "UNKNOWN_EVENT")
            recipient = str(event.get("user_id") or event.get("email") or "unknown")
            message = f"{event_type}: {event}"
            NotificationService(db).create(
                CreateNotificationRequest(
                    recipient=recipient,
                    type=event_type,
                    message=message[:1000],
                )
            )
            db.get(InboxEventModel, event["event_id"]).status = "PROCESSED"
            db.commit()
        finally:
            db.close()

    Thread(
        target=lambda: broker.consume(
            queue="notification-service.events",
            bindings=["UserRegistered", "OrderCompleted", "OrderCancelled", "PaymentFailed"],
            handler=handle_event,
        ),
        daemon=True,
    ).start()
