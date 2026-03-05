"""价格分析：时间序列、相关性、产品对比"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List

from app.database import get_db
from app.services.analysis import get_price_series, correlation_price_weather, compare_products

router = APIRouter(prefix="/analysis", tags=["价格分析"])


@router.get("/series")
def price_series(
    product_name: str,
    origin: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    freq: str = Query("D", description="D | W | M"),
    db: Session = Depends(get_db),
):
    """时间序列：日/周/月价格走势"""
    df = get_price_series(db, product_name, origin, date_start, date_end, freq)
    return df.to_dict(orient="records")


@router.get("/correlation")
def correlation(
    product_name: str,
    origin: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """多因素关联：价格与天气相关性（热力图数据）"""
    corr = correlation_price_weather(db, product_name, origin, date_start, date_end)
    if corr.empty:
        return {"matrix": [], "columns": []}
    return {"matrix": corr.values.tolist(), "columns": corr.columns.tolist()}


@router.get("/compare")
def compare(
    product_names: str = Query(..., description="逗号分隔，如 本地白菜,土豆"),
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    freq: str = "D",
    db: Session = Depends(get_db),
):
    """农产品对比：多产品同期价格"""
    names = [x.strip() for x in product_names.split(",")]
    df = compare_products(db, names, date_start, date_end, freq)
    return df.to_dict(orient="records")
