from math import ceil

from pydantic import BaseModel, Field

from libs.common.response.api_response import PageMeta


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def build_page_meta(page: int, page_size: int, total_items: int) -> PageMeta:
    total_pages = ceil(total_items / page_size) if total_items else 0
    return PageMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
