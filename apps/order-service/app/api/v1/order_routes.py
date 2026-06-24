from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services import OrderService
from app.infrastructure.database.session import get_db
from app.schemas.order_schema import CreateOrderRequest, OrderItemResponse, OrderResponse
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


def to_order_response(order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        payment_id=order.payment_id,
        cancellation_reason=order.cancellation_reason,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name_snapshot=item.product_name_snapshot,
                price_snapshot=item.price_snapshot,
                quantity=item.quantity,
            )
            for item in order.items
        ],
    )


@router.post("", response_model=ApiResponse[OrderResponse])
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    order = OrderService(db).create_order(payload)
    return ApiResponse[OrderResponse].ok(data=to_order_response(order))


@router.post("/async", response_model=ApiResponse[OrderResponse])
def create_order_async(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    order = OrderService(db).create_order_async(payload)
    return ApiResponse[OrderResponse].ok(data=to_order_response(order), message="Order accepted")


@router.get("/by-user/{user_id}", response_model=ApiResponse[list[OrderResponse]])
def list_user_orders(user_id: UUID, db: Session = Depends(get_db)):
    orders = OrderService(db).list_user_orders(user_id)
    return ApiResponse[list[OrderResponse]].ok(data=[to_order_response(order) for order in orders])


@router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    order = OrderService(db).get_order(order_id)
    return ApiResponse[OrderResponse].ok(data=to_order_response(order))


@router.post("/{order_id}/cancel", response_model=ApiResponse[OrderResponse])
def cancel_order(order_id: UUID, db: Session = Depends(get_db)):
    order = OrderService(db).cancel_order(order_id)
    return ApiResponse[OrderResponse].ok(data=to_order_response(order))
