from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateNotificationRequest(BaseModel):
    recipient: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=1000)


class NotificationResponse(BaseModel):
    id: UUID
    recipient: str
    type: str
    message: str
    status: str
    created_at: datetime
