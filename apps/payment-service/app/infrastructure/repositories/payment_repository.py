from sqlalchemy.orm import Session

from app.infrastructure.database.models import PaymentModel


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, payment_id: str) -> PaymentModel | None:
        return self.db.get(PaymentModel, payment_id)

    def get_by_order_id(self, order_id: str) -> PaymentModel | None:
        return self.db.query(PaymentModel).filter(PaymentModel.order_id == order_id).first()

    def add(self, payment: PaymentModel) -> None:
        self.db.add(payment)
