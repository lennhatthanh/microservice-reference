import json
import logging
import time
from typing import Protocol

from sqlalchemy.orm import Session

from libs.common.broker import RabbitMQClient

logger = logging.getLogger(__name__)


class OutboxEventLike(Protocol):
    id: str
    event_type: str
    payload: str
    status: str


class OutboxPublisher:
    """Polls an outbox table and publishes events to RabbitMQ.

    Outbox pattern goal:
    1. Save business state and event in the same DB transaction.
    2. Publish event later.
    3. Mark event as published only after RabbitMQ accepts it.
    """

    def __init__(
        self,
        db_factory,
        event_model,
        broker: RabbitMQClient,
        poll_interval_seconds: float = 2.0,
    ) -> None:
        self.db_factory = db_factory
        self.event_model = event_model
        self.broker = broker
        self.poll_interval_seconds = poll_interval_seconds

    def run_forever(self) -> None:
        while True:
            try:
                self.publish_pending_once()
            except Exception:
                logger.exception("Outbox publisher loop failed")
            time.sleep(self.poll_interval_seconds)

    def publish_pending_once(self) -> None:
        db: Session = self.db_factory()
        try:
            events = (
                db.query(self.event_model)
                .filter(self.event_model.status == "PENDING")
                .order_by(self.event_model.created_at.asc())
                .limit(20)
                .all()
            )
            for event in events:
                payload = json.loads(event.payload)
                self.broker.publish(event.event_type, payload)
                event.status = "PUBLISHED"
            db.commit()
        finally:
            db.close()
