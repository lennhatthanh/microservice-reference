from sqlalchemy.orm import Session

from app.infrastructure.database.models import OrderModel


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, order: OrderModel) -> None:
        self.db.add(order)

    def get(self, order_id: str) -> OrderModel | None:
        return self.db.get(OrderModel, order_id)

    def list_by_user(self, user_id: str) -> list[OrderModel]:
        return (
            self.db.query(OrderModel)
            .filter(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
            .all()
        )
