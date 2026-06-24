from sqlalchemy.orm import Session

from app.infrastructure.database.models import CategoryModel, ProductModel, StockReservationModel


class ProductRepository:
    """Persistence adapter for catalog and inventory tables."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_category(self, category_id: str) -> CategoryModel | None:
        return self.db.get(CategoryModel, category_id)

    def get_category_by_name(self, name: str) -> CategoryModel | None:
        return self.db.query(CategoryModel).filter(CategoryModel.name == name).first()

    def list_categories(self) -> list[CategoryModel]:
        return self.db.query(CategoryModel).order_by(CategoryModel.name.asc()).all()

    def add_category(self, category: CategoryModel) -> None:
        self.db.add(category)

    def get_product(self, product_id: str) -> ProductModel | None:
        return self.db.get(ProductModel, product_id)

    def list_products(self) -> list[ProductModel]:
        return self.db.query(ProductModel).order_by(ProductModel.created_at.desc()).all()

    def add_product(self, product: ProductModel) -> None:
        self.db.add(product)

    def has_active_reservation(self, order_id: str) -> bool:
        return (
            self.db.query(StockReservationModel)
            .filter(
                StockReservationModel.order_id == order_id,
                StockReservationModel.status == "RESERVED",
            )
            .first()
            is not None
        )

    def list_active_reservations(self, order_id: str) -> list[StockReservationModel]:
        return (
            self.db.query(StockReservationModel)
            .filter(
                StockReservationModel.order_id == order_id,
                StockReservationModel.status == "RESERVED",
            )
            .all()
        )

    def add_reservation(self, reservation: StockReservationModel) -> None:
        self.db.add(reservation)
