from sqlalchemy.orm import Session

from app.infrastructure.database.models import UserModel


class UserRepository:
    """SQLAlchemy repository for user persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: str) -> UserModel | None:
        return self.db.get(UserModel, user_id)

    def get_by_email(self, email: str) -> UserModel | None:
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def add(self, user: UserModel) -> None:
        self.db.add(user)
