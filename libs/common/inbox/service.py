import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session


def mark_event_processed(db: Session, inbox_model, event: dict) -> bool:
    """Return False when a consumer already processed this event.

    This is the Inbox Pattern. RabbitMQ can redeliver messages, so consumers
    persist the event_id before running business logic.
    """

    event_id = str(event.get("event_id") or "")
    if not event_id:
        return True

    existing = db.get(inbox_model, event_id)
    if existing and existing.status == "PROCESSED":
        return False
    if existing:
        existing.status = "PROCESSING"
        existing.payload = json.dumps(event, default=str)
        existing.received_at = datetime.now(timezone.utc)
        db.flush()
        return True

    db.add(
        inbox_model(
            event_id=event_id,
            event_type=event.get("event_type", "UNKNOWN"),
            payload=json.dumps(event, default=str),
            status="PROCESSING",
        )
    )
    db.flush()
    return True
