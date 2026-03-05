from pydantic import BaseModel
from typing import TypeVar, Generic, List

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: List[T]
