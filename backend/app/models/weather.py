"""天气数据模型（精简版）

字段完全对应你提供的天气 Excel 表头：
- 时间（record_date）
- 最高气温（temp_max）
- 最低气温（temp_min）
- 平均气温（temp_avg）
- 降水（precipitation）
- 平均相对湿度（humidity_avg）
- 气压（pressure）
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base


class WeatherRecord(Base):
    """天气记录"""
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String(64), nullable=False, index=True)      # 地区（如：广东-广州）
    record_date = Column(Date, nullable=False, index=True)       # 日期
    temp_max = Column(Numeric(5, 1), nullable=True)              # 最高气温 ℃
    temp_min = Column(Numeric(5, 1), nullable=True)              # 最低气温 ℃
    temp_avg = Column(Numeric(5, 1), nullable=True)              # 平均气温 ℃
    precipitation = Column(Numeric(6, 1), nullable=True)         # 降水 mm
    humidity_avg = Column(Numeric(5, 1), nullable=True)          # 平均相对湿度 %
    pressure = Column(Numeric(7, 1), nullable=True)              # 气压 hPa
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    extreme_weather = Column(String(32), nullable=True)  # 极端天气标识

    def to_dict(self):
        return {
            "id": self.id,
            "origin": self.origin,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "temp_max": float(self.temp_max) if self.temp_max is not None else None,
            "temp_min": float(self.temp_min) if self.temp_min is not None else None,
            "temp_avg": float(self.temp_avg) if self.temp_avg is not None else None,
            "precipitation": float(self.precipitation) if self.precipitation is not None else None,
            "humidity_avg": float(self.humidity_avg) if self.humidity_avg is not None else None,
            "pressure": float(self.pressure) if self.pressure is not None else None,
            "extreme_weather": self.extreme_weather or "无极端天气",
        }
