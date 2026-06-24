from sqlalchemy.orm import Session

from app.infrastructure.database.models import NotificationModel
from app.infrastructure.repositories import NotificationRepository
from app.schemas.notification_schema import CreateNotificationRequest


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notifications = NotificationRepository(db)

    def create(self, payload: CreateNotificationRequest) -> NotificationModel:
        notification = NotificationModel(
            recipient=payload.recipient,
            type=payload.type,
            message=payload.message,
            status="SENT",
        )
        self.notifications.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
