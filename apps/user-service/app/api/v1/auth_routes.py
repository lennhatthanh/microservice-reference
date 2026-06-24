from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.auth_service import AuthService
from app.infrastructure.database.session import get_db
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user_schema import UserResponse
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[UserResponse])
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService(db).register(payload)
    return ApiResponse[UserResponse].ok(data=UserResponse.model_validate(user, from_attributes=True))


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = AuthService(db).login(payload)
    return ApiResponse[TokenResponse].ok(data=TokenResponse(access_token=token))
