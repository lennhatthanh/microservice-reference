from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IntegrationEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    version: int = 1
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
