"""异常预警记录"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class AlertRecord(Base):
    """价格异常预警记录"""
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(32), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=True)
    alert_type = Column(String(32), nullable=False)   # 如：超出区间、异常涨幅、异常跌幅
    reason = Column(Text, nullable=True)              # 可能原因，如关联产区暴雨
    is_read = Column(Integer, default=0)               # 0 未读 1 已读
    created_at = Column(DateTime(timezone=True), server_default=func.now())
