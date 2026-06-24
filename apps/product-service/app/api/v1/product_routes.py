from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.product_service import ProductService
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories import ProductRepository
from app.schemas.product_schema import ProductCreate, ProductResponse
from libs.common.exceptions import NotFoundError
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("", response_model=ApiResponse[ProductResponse])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = ProductService(db).create_product(payload)
    return ApiResponse[ProductResponse].ok(data=ProductResponse.model_validate(product, from_attributes=True))


@router.get("", response_model=ApiResponse[list[ProductResponse]])
def list_products(db: Session = Depends(get_db)):
    products = ProductRepository(db).list_products()
    data = [ProductResponse.model_validate(item, from_attributes=True) for item in products]
    return ApiResponse[list[ProductResponse]].ok(data=data)


@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    product = ProductRepository(db).get_product(str(product_id))
    if not product:
        raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
    return ApiResponse[ProductResponse].ok(data=ProductResponse.model_validate(product, from_attributes=True))
