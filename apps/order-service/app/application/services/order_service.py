from decimal import Decimal
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.infrastructure.database.models import OrderItemModel, OrderModel
from app.infrastructure.outbox.service import add_outbox_event
from app.infrastructure.repositories import OrderRepository
from app.schemas.order_schema import CreateOrderRequest
from libs.common.exceptions import NotFoundError, ValidationError
from libs.contracts.events import (
    OrderCancelled,
    OrderCompleted,
    OrderCreated,
    OrderItemPayload,
)


class OrderService:
    """Application service: keeps order use cases in one place.

    API routes stay thin, domain decisions live here, and infrastructure
    details are hidden behind helper methods/outbox functions.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)

    def create_order(self, payload: CreateOrderRequest) -> OrderModel:
        """Synchronous orchestration path.

        This path is easier for local learning because a single request shows
        the whole workflow. The async MQ version is `create_order_async`.
        """

        product_snapshots = [self._get_product(item.product_id) for item in payload.items]
        items_by_product_id = {str(item.product_id): item for item in payload.items}

        order = OrderModel(user_id=str(payload.user_id), status="PENDING", total_amount=0)
        total_amount = Decimal("0")

        for snapshot in product_snapshots:
            product_id = str(snapshot["id"])
            requested_item = items_by_product_id[product_id]
            price = Decimal(str(snapshot["price"]))
            total_amount += price * requested_item.quantity
            order.items.append(
                OrderItemModel(
                    product_id=product_id,
                    product_name_snapshot=snapshot["name"],
                    price_snapshot=price,
                    quantity=requested_item.quantity,
                )
            )

        order.total_amount = total_amount
        self.orders.add(order)
        self.db.commit()
        self.db.refresh(order)

        reserved, reason = self._reserve_stock(order)
        if not reserved:
            order.status = "CANCELLED"
            order.cancellation_reason = reason or "STOCK_RESERVATION_FAILED"
            add_outbox_event(
                self.db,
                OrderCancelled(
                    order_id=order.id,
                    user_id=order.user_id,
                    reason=order.cancellation_reason,
                ),
            )
            self.db.commit()
            self._notify(str(payload.user_id), "ORDER_CANCELLED", f"Order {order.id} cancelled: {order.cancellation_reason}")
            return order

        # Saga orchestration: Order service owns the workflow decision, while
        # Product/Payment services own their data and expose bounded APIs.
        payment = self._process_payment(order, payload.force_payment_fail)
        order.payment_id = payment["id"]

        if payment["status"] == "SUCCEEDED":
            order.status = "COMPLETED"
            add_outbox_event(
                self.db,
                OrderCompleted(order_id=order.id, user_id=order.user_id),
            )
            self._notify(str(payload.user_id), "ORDER_COMPLETED", f"Order {order.id} completed")
        else:
            order.status = "CANCELLED"
            order.cancellation_reason = payment.get("failure_reason") or "PAYMENT_FAILED"
            self._release_stock(order.id)
            add_outbox_event(
                self.db,
                OrderCancelled(
                    order_id=order.id,
                    user_id=order.user_id,
                    reason=order.cancellation_reason,
                ),
            )
            self._notify(str(payload.user_id), "ORDER_CANCELLED", f"Order {order.id} cancelled: {order.cancellation_reason}")

        self.db.commit()
        self.db.refresh(order)
        return order

    def create_order_async(self, payload: CreateOrderRequest) -> OrderModel:
        """Async saga entrypoint.

        It creates an order and writes OrderCreated to the outbox. Product,
        payment, order, and notification workers continue the workflow via MQ.
        """

        product_snapshots = [self._get_product(item.product_id) for item in payload.items]
        items_by_product_id = {str(item.product_id): item for item in payload.items}
        order = OrderModel(user_id=str(payload.user_id), status="PENDING", total_amount=0)
        total_amount = Decimal("0")
        event_items: list[OrderItemPayload] = []

        for snapshot in product_snapshots:
            product_id = str(snapshot["id"])
            requested_item = items_by_product_id[product_id]
            price = Decimal(str(snapshot["price"]))
            total_amount += price * requested_item.quantity
            order.items.append(
                OrderItemModel(
                    product_id=product_id,
                    product_name_snapshot=snapshot["name"],
                    price_snapshot=price,
                    quantity=requested_item.quantity,
                )
            )
            event_items.append(
                OrderItemPayload(
                    product_id=product_id,
                    product_name=snapshot["name"],
                    price=price,
                    quantity=requested_item.quantity,
                )
            )

        order.total_amount = total_amount
        self.orders.add(order)
        self.db.flush()
        add_outbox_event(
            self.db,
            OrderCreated(
                order_id=order.id,
                user_id=order.user_id,
                items=event_items,
                total_amount=total_amount,
            ),
        )
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_order(self, order_id: UUID) -> OrderModel:
        order = self.orders.get(str(order_id))
        if not order:
            raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
        return order

    def list_user_orders(self, user_id: UUID) -> list[OrderModel]:
        return self.orders.list_by_user(str(user_id))

    def cancel_order(self, order_id: UUID) -> OrderModel:
        order = self.get_order(order_id)
        if order.status == "COMPLETED":
            raise ValidationError("Completed order cannot be cancelled", code="ORDER_ALREADY_COMPLETED")
        if order.status == "CANCELLED":
            return order

        order.status = "CANCELLED"
        order.cancellation_reason = "CANCELLED_BY_USER"
        self._release_stock(order.id)
        add_outbox_event(
            self.db,
            OrderCancelled(
                order_id=order.id,
                user_id=order.user_id,
                reason=order.cancellation_reason,
            ),
        )
        self.db.commit()
        self.db.refresh(order)
        self._notify(order.user_id, "ORDER_CANCELLED", f"Order {order.id} cancelled by user")
        return order

    def handle_stock_reservation_failed(self, event: dict) -> None:
        """Async saga handler: product-service could not reserve stock."""

        order = self.get_order(UUID(event["order_id"]))
        if order.status in {"COMPLETED", "CANCELLED"}:
            return
        order.status = "CANCELLED"
        order.cancellation_reason = event.get("reason") or "STOCK_RESERVATION_FAILED"
        add_outbox_event(
            self.db,
            OrderCancelled(
                order_id=order.id,
                user_id=order.user_id,
                reason=order.cancellation_reason,
            ),
        )
        self.db.commit()

    def handle_payment_succeeded(self, event: dict) -> None:
        """Async saga handler: payment-service accepted payment."""

        order = self.get_order(UUID(event["order_id"]))
        if order.status in {"COMPLETED", "CANCELLED"}:
            return
        order.status = "COMPLETED"
        order.payment_id = event["payment_id"]
        add_outbox_event(
            self.db,
            OrderCompleted(order_id=order.id, user_id=order.user_id),
        )
        self.db.commit()

    def handle_payment_failed(self, event: dict) -> None:
        """Async saga handler: payment-service rejected payment."""

        order = self.get_order(UUID(event["order_id"]))
        if order.status in {"COMPLETED", "CANCELLED"}:
            return
        order.status = "CANCELLED"
        order.payment_id = event["payment_id"]
        order.cancellation_reason = event.get("reason") or "PAYMENT_FAILED"
        self._release_stock(order.id)
        add_outbox_event(
            self.db,
            OrderCancelled(
                order_id=order.id,
                user_id=order.user_id,
                reason=order.cancellation_reason,
            ),
        )
        self.db.commit()

    def _get_product(self, product_id: UUID) -> dict:
        response = httpx.get(f"{settings.PRODUCT_SERVICE_URL}/api/v1/products/{product_id}", timeout=10)
        response.raise_for_status()
        body = response.json()
        if not body.get("success"):
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
        return body["data"]

    def _reserve_stock(self, order: OrderModel) -> tuple[bool, str | None]:
        response = httpx.post(
            f"{settings.PRODUCT_SERVICE_URL}/api/v1/products/stock/reserve",
            json={
                "order_id": order.id,
                "items": [
                    {"product_id": item.product_id, "quantity": item.quantity}
                    for item in order.items
                ],
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return data["reserved"], data.get("reason")

    def _release_stock(self, order_id: str) -> None:
        try:
            httpx.post(f"{settings.PRODUCT_SERVICE_URL}/api/v1/products/stock/release/{order_id}", timeout=10)
        except httpx.HTTPError:
            pass

    def _process_payment(self, order: OrderModel, force_fail: bool) -> dict:
        response = httpx.post(
            f"{settings.PAYMENT_SERVICE_URL}/api/v1/payments/process",
            json={
                "order_id": order.id,
                "user_id": order.user_id,
                "amount": str(order.total_amount),
                "force_fail": force_fail,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["data"]

    def _notify(self, recipient: str, notification_type: str, message: str) -> None:
        if not settings.NOTIFICATION_SERVICE_URL:
            return
        try:
            httpx.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notifications",
                json={"recipient": recipient, "type": notification_type, "message": message},
                timeout=5,
            )
        except httpx.HTTPError:
            pass
