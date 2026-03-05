"""数据导出：按产品类型、时间范围、数据类型导出 Excel - PRD 3.1"""
import pandas as pd
from pathlib import Path
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from app.models.price import PriceRecord
from app.models.weather import WeatherRecord
from app.config import get_settings

settings = get_settings()
EXPORT_DIR = Path(settings.UPLOAD_DIR) / "export"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _query_prices(
    db: Session,
    product_names: Optional[List[str]] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
) -> pd.DataFrame:
    q = db.query(PriceRecord)
    if product_names:
        q = q.filter(PriceRecord.product_name.in_(product_names))
    if date_start:
        q = q.filter(PriceRecord.record_date >= date_start)
    if date_end:
        q = q.filter(PriceRecord.record_date <= date_end)
    rows = q.order_by(PriceRecord.record_date).all()
    return pd.DataFrame([r.to_dict() for r in rows])


def _query_weather(
    db: Session,
    regions: Optional[List[str]] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
) -> pd.DataFrame:
    q = db.query(WeatherRecord)
    if regions:
        q = q.filter(WeatherRecord.origin.in_(regions))
    if date_start:
        q = q.filter(WeatherRecord.record_date >= date_start)
    if date_end:
        q = q.filter(WeatherRecord.record_date <= date_end)
    rows = q.order_by(WeatherRecord.record_date).all()
    return pd.DataFrame([r.to_dict() for r in rows])


def export_excel(
    db: Session,
    data_type: str,  # "price" | "weather" | "integrated"
    product_names: Optional[List[str]] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    regions: Optional[List[str]] = None,
) -> str:
    """
    导出 Excel，返回文件路径。
    """
    if data_type == "price":
        df = _query_prices(db, product_names, date_start, date_end)
        path = EXPORT_DIR / f"price_{date_start}_{date_end}.xlsx"
    elif data_type == "weather":
        df = _query_weather(db, regions, date_start, date_end)
        path = EXPORT_DIR / f"weather_{date_start}_{date_end}.xlsx"
    elif data_type == "integrated":
        price_df = _query_prices(db, product_names, date_start, date_end)
        regions = regions or price_df["origin"].dropna().unique().tolist()
        weather_df = _query_weather(db, regions, date_start, date_end)
        from app.services.preprocess import integrate_price_weather
        df = integrate_price_weather(price_df, weather_df)
        path = EXPORT_DIR / f"integrated_{date_start}_{date_end}.xlsx"
    else:
        raise ValueError("data_type 应为 price / weather / integrated")
    df.to_excel(path, index=False)
    return str(path)
