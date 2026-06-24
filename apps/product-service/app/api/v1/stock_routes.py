from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.product_service import ProductService
from app.infrastructure.database.session import get_db
from app.schemas.product_schema import ReserveStockRequest, ReserveStockResponse
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/products/stock", tags=["stock"])


@router.post("/reserve", response_model=ApiResponse[ReserveStockResponse])
def reserve_stock(payload: ReserveStockRequest, db: Session = Depends(get_db)):
    reserved, reason = ProductService(db).reserve_stock(payload)
    return ApiResponse[ReserveStockResponse].ok(data=ReserveStockResponse(reserved=reserved, reason=reason))


@router.post("/release/{order_id}", response_model=ApiResponse[dict])
def release_stock(order_id: UUID, db: Session = Depends(get_db)):
    ProductService(db).release_stock(str(order_id))
    return ApiResponse[dict].ok(data={"released": True})
