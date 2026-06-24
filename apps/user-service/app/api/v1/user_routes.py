from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.infrastructure.repositories import UserRepository
from app.schemas.user_schema import UserResponse
from libs.common.exceptions import NotFoundError
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(str(user_id))
    if not user:
        raise NotFoundError("User not found", code="USER_NOT_FOUND")
    return ApiResponse[UserResponse].ok(data=UserResponse.model_validate(user, from_attributes=True))
