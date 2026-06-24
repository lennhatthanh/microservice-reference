from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CategoryResponse(BaseModel):
    id: UUID
    name: str


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)
    category_id: UUID | None = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    price: Decimal
    stock: int
    category_id: UUID | None


class StockItem(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class ReserveStockRequest(BaseModel):
    order_id: UUID
    items: list[StockItem] = Field(min_length=1)


class ReserveStockResponse(BaseModel):
    reserved: bool
    reason: str | None = None
