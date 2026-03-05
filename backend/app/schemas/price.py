from pydantic import BaseModel
from typing import Optional
from datetime import date


class PriceRecordCreate(BaseModel):
    market_name: Optional[str] = None  # 新增
    product_name: str
    price: float
    origin: Optional[str] = None
    sale_region: Optional[str] = None
    record_date: date
    spec: str = "中等"

class PriceRecordResponse(BaseModel):
    id: int
    market_name: Optional[str] = None  # 新增
    product_name: str
    price: float
    origin: Optional[str] = None
    sale_region: Optional[str] = None
    record_date: date
    spec: str = "中等"

    class Config:
        from_attributes = True


class PriceQuery(BaseModel):
    product_name: Optional[str] = None
    origin: Optional[str] = None
    sale_region: Optional[str] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    page: int = 1
    page_size: int = 100
