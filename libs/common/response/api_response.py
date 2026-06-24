from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class PageMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None
    errors: list[ErrorDetail] = Field(default_factory=list)
    meta: Optional[PageMeta] = None

    @classmethod
    def ok(
        cls,
        data: Optional[T] = None,
        message: str = "OK",
        meta: Optional[PageMeta] = None,
    ) -> "ApiResponse[T]":
        return cls(success=True, message=message, data=data, meta=meta)

    @classmethod
    def fail(
        cls,
        message: str,
        errors: Optional[list[ErrorDetail]] = None,
    ) -> "ApiResponse[T]":
        return cls(
            success=False,
            message=message,
            data=None,
            errors=errors or [],
        )
