from uuid import UUID

from .base import IntegrationEvent


class UserRegistered(IntegrationEvent):
    event_type: str = "UserRegistered"
    source: str = "user-service"
    user_id: UUID
    email: str
    full_name: str
