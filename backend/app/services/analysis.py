"""价格分析：时间序列、多因素关联、农产品对比 - PRD 3.2"""
import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from app.models.price import PriceRecord
from app.models.weather import WeatherRecord


def get_price_series(
    db: Session,
    product_name: str,
    origin: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    freq: str = "D",  # D / W / M
) -> pd.DataFrame:
    """时间序列：日/周/月价格走势。返回 date, price, (可选 origin)。"""
    q = db.query(PriceRecord.record_date, PriceRecord.price, PriceRecord.origin).filter(
        PriceRecord.product_name == product_name
    )
    if origin:
        q = q.filter(PriceRecord.origin == origin)
    if date_start:
        q = q.filter(PriceRecord.record_date >= date_start)
    if date_end:
        q = q.filter(PriceRecord.record_date <= date_end)
    rows = q.order_by(PriceRecord.record_date).all()
    df = pd.DataFrame(rows, columns=["record_date", "price", "origin"])
    df["record_date"] = pd.to_datetime(df["record_date"])
    df = df.set_index("record_date")
    if freq != "D":
        df = df.resample(freq).agg({"price": "mean", "origin": "first"}).dropna(subset=["price"])
    return df.reset_index()


def get_weather_series(
    db: Session,
    origin: str,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
) -> pd.DataFrame:
    """天气时间序列"""
    q = db.query(
        WeatherRecord.record_date,
        WeatherRecord.temp_avg,
        WeatherRecord.precipitation,
        WeatherRecord.extreme_weather,
    ).filter(WeatherRecord.origin == origin)
    if date_start:
        q = q.filter(WeatherRecord.record_date >= date_start)
    if date_end:
        q = q.filter(WeatherRecord.record_date <= date_end)
    rows = q.order_by(WeatherRecord.record_date).all()
    df = pd.DataFrame(
        rows,
        columns=["record_date", "temp_avg", "precipitation", "extreme_weather"],
    )
    df["record_date"] = pd.to_datetime(df["record_date"])
    return df


def correlation_price_weather(
    db: Session,
    product_name: str,
    origin: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
) -> pd.DataFrame:
    """多因素关联：价格与气温/降水/极端天气的相关性，返回相关系数矩阵（热力图用）。"""
    price_df = get_price_series(db, product_name, origin, date_start, date_end)
    if price_df.empty or "origin" in price_df.columns and price_df["origin"].isna().all():
        return pd.DataFrame()
    origin = origin or price_df["origin"].dropna().iloc[0] if "origin" in price_df.columns else None
    if not origin:
        return pd.DataFrame()

    # Try to resolve origin to a valid weather origin if exact match not found
    try:
        existing_origins = [o[0] for o in db.query(WeatherRecord.origin).distinct().all()]
    except Exception:
        existing_origins = []

    if existing_origins and origin not in existing_origins:
        # try fuzzy matches: contains or prefix
        origin_lower = str(origin).lower()
        candidate = None
        for o in existing_origins:
            if origin_lower in str(o).lower() or str(o).lower() in origin_lower:
                candidate = o
                break
        if candidate is None:
            # try matching by first token before '-' or space
            origin_head = origin.split('-')[0].split(' ')[0].lower()
            for o in existing_origins:
                if str(o).lower().startswith(origin_head):
                    candidate = o
                    break
        if candidate:
            origin = candidate

    weather_df = get_weather_series(db, origin, date_start, date_end)
    if weather_df.empty:
        return pd.DataFrame()
    price_df["record_date"] = pd.to_datetime(price_df["record_date"])
    weather_df["record_date"] = pd.to_datetime(weather_df["record_date"])
    merged = price_df.merge(weather_df, on="record_date", how="inner")
    # 极端天气转数值（简单编码）
    ext_map = {
        "无极端天气": 0, "暴雨": 1, "低温": 2, "高温": 3, "干旱": 4
    }
    merged["extreme_code"] = merged["extreme_weather"].map(lambda x: ext_map.get(x, 0))
    cols = ["price", "temp_avg", "precipitation", "sunshine_hours", "extreme_code"]
    merged = merged[[c for c in cols if c in merged.columns]].dropna(how="all", axis=1)
    return merged.corr()


def compare_products(
    db: Session,
    product_names: List[str],
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    freq: str = "D",
) -> pd.DataFrame:
    """农产品对比：多产品同期价格，返回 record_date, product_name, price。"""
    out = []
    for p in product_names:
        df = get_price_series(db, p, date_start=date_start, date_end=date_end, freq=freq)
        df["product_name"] = p
        out.append(df[["record_date", "product_name", "price"]])
    if not out:
        return pd.DataFrame()
    return pd.concat(out, ignore_index=True)


def detect_extreme_weather(temp_avg: float, precipitation: float, temp_max: float = None,
                           temp_min: float = None) -> str:
    """
    根据气象数据判断极端天气类型
    返回: "无极端天气", "暴雨", "寒潮", "高温", "干旱" 等
    """
    extreme_types = []

    # 高温判断（日平均温度 > 35°C）
    if temp_avg is not None and temp_avg >= 35:
        extreme_types.append("高温")

    # 低温判断（日平均温度 < 0°C）
    if temp_avg is not None and temp_avg <= 0:
        extreme_types.append("寒潮")

    # 暴雨判断（日降水量 > 50mm）
    if precipitation is not None and precipitation >= 50:
        extreme_types.append("暴雨")

    # 干旱判断（连续多日无降水且温度高）
    # 这里简化处理，实际应该考虑时间序列

    if not extreme_types:
        return "无极端天气"
    elif len(extreme_types) == 1:
        return extreme_types[0]
    else:
        return "多种极端天气"


def get_weather_series_with_analysis(
        db: Session,
        origin: str,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
) -> pd.DataFrame:
    """带极端天气分析的天气时间序列"""
    q = db.query(
        WeatherRecord.record_date,
        WeatherRecord.temp_avg,
        WeatherRecord.temp_max,
        WeatherRecord.temp_min,
        WeatherRecord.precipitation,
        WeatherRecord.humidity_avg,
        WeatherRecord.pressure,
    ).filter(WeatherRecord.origin == origin)

    if date_start:
        q = q.filter(WeatherRecord.record_date >= date_start)
    if date_end:
        q = q.filter(WeatherRecord.record_date <= date_end)

    rows = q.order_by(WeatherRecord.record_date).all()
    df = pd.DataFrame(
        rows,
        columns=["record_date", "temp_avg", "temp_max", "temp_min", "precipitation", "humidity_avg", "pressure"]
    )

    df["record_date"] = pd.to_datetime(df["record_date"])

    # 添加极端天气分析列
    df["extreme_weather"] = df.apply(
        lambda row: detect_extreme_weather(
            row["temp_avg"],
            row["precipitation"],
            row["temp_max"],
            row["temp_min"]
        ), axis=1
    )

    return df
