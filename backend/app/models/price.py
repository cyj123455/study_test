"""农产品价格数据模型（精简版）

字段完全对应你提供的白菜/土豆 Excel 表头：
- 市场名称（market_name）
- 产品名称（product_name）
- 批发价格（price）
- 日期（record_date）
- 地区（origin，均为广东或广东-广州）
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


# 产品名称枚举：矮脚白菜、本地白菜、小塘白菜、土豆
PRODUCT_NAMES = ("矮脚白菜", "本地白菜", "小塘白菜", "土豆")


class PriceRecord(Base):
    """农产品批发价格记录"""
    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, index=True)
    market_name = Column(String(64), nullable=True, index=True)     # 市场名称（如：江南果菜市场）
    product_name = Column(String(32), nullable=False, index=True)   # 产品名称
    price = Column(Numeric(10, 2), nullable=False)                  # 批发价格 元/公斤
    record_date = Column(Date, nullable=False, index=True)          # 日期 YYYY-MM-DD
    origin = Column(String(64), nullable=True, index=True)          # 产地（如：广东、山东等）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "market_name": self.market_name,
            "product_name": self.product_name,
            "price": float(self.price),
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "origin": self.origin,
        }


class PriceDatasetVersion(Base):
    """预处理阶段的数据集版本，支持回溯对比"""
    __tablename__ = "price_dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)   # 版本描述
    note = Column(Text, nullable=True)            # 备注（如预处理方式）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
