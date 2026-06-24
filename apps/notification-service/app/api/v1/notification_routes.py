from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.notification_service import NotificationService
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories import NotificationRepository
from app.schemas.notification_schema import CreateNotificationRequest, NotificationResponse
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("", response_model=ApiResponse[NotificationResponse])
def create_notification(payload: CreateNotificationRequest, db: Session = Depends(get_db)):
    notification = NotificationService(db).create(payload)
    return ApiResponse[NotificationResponse].ok(
        data=NotificationResponse.model_validate(notification, from_attributes=True)
    )


@router.get("", response_model=ApiResponse[list[NotificationResponse]])
def list_notifications(db: Session = Depends(get_db)):
    notifications = NotificationRepository(db).list_all()
    data = [NotificationResponse.model_validate(item, from_attributes=True) for item in notifications]
    return ApiResponse[list[NotificationResponse]].ok(data=data)
