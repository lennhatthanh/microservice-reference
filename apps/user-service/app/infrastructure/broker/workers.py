from threading import Thread

from app.core.config import settings
from app.infrastructure.database.models import OutboxEventModel
from app.infrastructure.database.session import SessionLocal
from libs.common.broker import RabbitMQClient
from libs.common.outbox import OutboxPublisher


def start_mq_workers() -> None:
    """Start User Service MQ publisher for UserRegistered events."""

    if not settings.ENABLE_MQ or not settings.RABBITMQ_URL:
        return

    broker = RabbitMQClient(settings.RABBITMQ_URL)
    publisher = OutboxPublisher(SessionLocal, OutboxEventModel, broker)
    Thread(target=publisher.run_forever, daemon=True).start()
