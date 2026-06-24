import json

from sqlalchemy.orm import Session

from app.infrastructure.database.models import OutboxEventModel
from libs.contracts.events import IntegrationEvent


def add_outbox_event(db: Session, event: IntegrationEvent) -> None:
    """Persist an integration event in the same transaction as business data.

    This is the Outbox Pattern. The service does not publish to RabbitMQ inside
    the business method; it stores the event first, then a publisher worker sends
    it after commit.
    """

    db.add(
        OutboxEventModel(
            event_type=event.event_type,
            payload=json.dumps(event.model_dump(mode="json")),
        )
    )
