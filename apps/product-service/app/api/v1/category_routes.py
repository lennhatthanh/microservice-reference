from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.product_service import ProductService
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories import ProductRepository
from app.schemas.product_schema import CategoryCreate, CategoryResponse
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.post("", response_model=ApiResponse[CategoryResponse])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    category = ProductService(db).create_category(payload)
    return ApiResponse[CategoryResponse].ok(data=CategoryResponse.model_validate(category, from_attributes=True))


@router.get("", response_model=ApiResponse[list[CategoryResponse]])
def list_categories(db: Session = Depends(get_db)):
    categories = ProductRepository(db).list_categories()
    data = [CategoryResponse.model_validate(item, from_attributes=True) for item in categories]
    return ApiResponse[list[CategoryResponse]].ok(data=data)
