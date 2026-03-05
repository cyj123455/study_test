from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class AlertResponse(BaseModel):
    id: int
    product_name: str
    record_date: date
    price: Optional[float] = None
    alert_type: str
    reason: Optional[str] = None
    is_read: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
