from sqlalchemy.orm import Session

from app.infrastructure.database.models import NotificationModel


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, notification: NotificationModel) -> None:
        self.db.add(notification)

    def list_all(self) -> list[NotificationModel]:
        return self.db.query(NotificationModel).order_by(NotificationModel.created_at.desc()).all()
