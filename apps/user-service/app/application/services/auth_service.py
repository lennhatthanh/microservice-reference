from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.infrastructure.database.models import UserModel
from app.infrastructure.repositories import UserRepository
from app.infrastructure.outbox.service import add_outbox_event
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from libs.common.exceptions import ConflictError, UnauthorizedError
from libs.contracts.enums import UserRole
from libs.contracts.events import UserRegistered


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> UserModel:
        existing = self.users.get_by_email(payload.email)
        if existing:
            raise ConflictError("Email already registered", code="EMAIL_ALREADY_REGISTERED")

        user = UserModel(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=UserRole.CUSTOMER.value,
        )
        self.users.add(user)
        self.db.flush()
        # Outbox Pattern: user data and UserRegistered event commit together.
        add_outbox_event(
            self.db,
            UserRegistered(user_id=user.id, email=user.email, full_name=user.full_name),
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, payload: LoginRequest) -> str:
        user = self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password", code="INVALID_CREDENTIALS")

        return create_access_token(
            {
                "sub": str(user.id),
                "user_id": str(UUID(user.id)),
                "email": user.email,
                "role": user.role,
            }
        )
