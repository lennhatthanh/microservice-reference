from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    CategoryModel,
    ProductModel,
    StockReservationModel,
)
from app.infrastructure.outbox.service import add_outbox_event
from app.infrastructure.repositories import ProductRepository
from app.schemas.product_schema import CategoryCreate, ProductCreate, ReserveStockRequest
from libs.common.exceptions import ConflictError, NotFoundError
from libs.contracts.events import (
    StockReservationFailed,
    StockReservationItemPayload,
    StockReserved,
)


class ProductService:
    """Application service for the Product bounded context.

    Product service is the only service allowed to mutate stock. Other services
    ask it to reserve/release stock through REST or integration events.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)

    def create_category(self, payload: CategoryCreate) -> CategoryModel:
        existing = self.products.get_category_by_name(payload.name)
        if existing:
            raise ConflictError("Category already exists", code="CATEGORY_EXISTS")
        category = CategoryModel(name=payload.name)
        self.products.add_category(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def create_product(self, payload: ProductCreate) -> ProductModel:
        if payload.category_id:
            category = self.products.get_category(str(payload.category_id))
            if not category:
                raise NotFoundError("Category not found", code="CATEGORY_NOT_FOUND")

        product = ProductModel(
            name=payload.name,
            description=payload.description,
            price=payload.price,
            stock=payload.stock,
            category_id=str(payload.category_id) if payload.category_id else None,
        )
        self.products.add_product(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def reserve_stock(self, payload: ReserveStockRequest, commit: bool = True) -> tuple[bool, str | None]:
        if self.products.has_active_reservation(str(payload.order_id)):
            # Idempotent consumer guard: if RabbitMQ redelivers OrderCreated,
            # do not decrease stock twice for the same order.
            return True, None

        reservations: list[StockReservationModel] = []
        for item in payload.items:
            product = self.products.get_product(str(item.product_id))
            if not product:
                self.db.rollback()
                return False, f"Product {item.product_id} not found"
            if product.stock < item.quantity:
                self.db.rollback()
                return False, f"Insufficient stock for product {item.product_id}"

            product.stock -= item.quantity
            reservations.append(
                StockReservationModel(
                    product_id=str(item.product_id),
                    order_id=str(payload.order_id),
                    quantity=item.quantity,
                    status="RESERVED",
                )
            )

        for reservation in reservations:
            self.products.add_reservation(reservation)
        if commit:
            self.db.commit()
        return True, None

    def reserve_stock_from_event(self, event: dict) -> None:
        """Consumer-side use case for async saga.

        OrderCreated arrives from RabbitMQ. Product service owns stock, so it
        decides whether to reserve inventory and emits the next event.
        """

        request = ReserveStockRequest(
            order_id=event["order_id"],
            items=[
                {"product_id": item["product_id"], "quantity": item["quantity"]}
                for item in event["items"]
            ],
        )
        reserved, reason = self.reserve_stock(request, commit=False)
        event_items = [
            StockReservationItemPayload(
                product_id=item.product_id,
                quantity=item.quantity,
            )
            for item in request.items
        ]
        if reserved:
            add_outbox_event(
                self.db,
                StockReserved(
                    reservation_id=uuid4(),
                    order_id=request.order_id,
                    user_id=event["user_id"],
                    total_amount=Decimal(str(event["total_amount"])),
                    items=event_items,
                ),
            )
        else:
            add_outbox_event(
                self.db,
                StockReservationFailed(
                    order_id=request.order_id,
                    failed_items=event_items,
                    reason=reason or "STOCK_RESERVATION_FAILED",
                ),
            )
        self.db.commit()

    def release_stock(self, order_id: str) -> None:
        reservations = self.products.list_active_reservations(order_id)
        if not reservations:
            # Release can be called by retries/cancel races. Treating it as
            # idempotent keeps rollback flows safe for local learning.
            return

        for reservation in reservations:
            product = self.products.get_product(reservation.product_id)
            if product:
                product.stock += reservation.quantity
            reservation.status = "RELEASED"
        self.db.commit()
