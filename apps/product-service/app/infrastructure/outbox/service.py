import json

from sqlalchemy.orm import Session

from app.infrastructure.database.models import OutboxEventModel
from libs.contracts.events import IntegrationEvent


def add_outbox_event(db: Session, event: IntegrationEvent) -> None:
    """Store event for reliable async publishing."""

    db.add(
        OutboxEventModel(
            event_type=event.event_type,
            payload=json.dumps(event.model_dump(mode="json")),
        )
    )
