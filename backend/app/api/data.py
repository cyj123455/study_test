"""数据管理：导入、预处理、导出、爬虫触发、本地数据加载"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
import pandas as pd
import io

from app.database import get_db
from app.models.price import PriceRecord, PriceDatasetVersion
from app.models.weather import WeatherRecord
from app.schemas.price import PriceRecordCreate, PriceRecordResponse, PriceQuery
from app.schemas.weather import WeatherRecordCreate, WeatherRecordResponse
from app.services.preprocess import fill_missing_mean, remove_outliers_df, standardize
from app.services.export_data import export_excel
from app.services.crawler import crawl_all
from app.services.load_local_data import (
    load_and_preprocess_all,
    save_to_db,
)
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/data", tags=["数据管理"])


@router.post("/price", response_model=PriceRecordResponse)
def create_price_record(
    data: PriceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = PriceRecord(
        market_name=data.market_name,  # 新增
        product_name=data.product_name,
        price=data.price,
        origin=data.origin,
        sale_region=data.sale_region,
        record_date=data.record_date,
        spec=data.spec,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.get("/price", response_model=List[PriceRecordResponse])
def list_prices(
    product_name: Optional[str] = None,
    origin: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(PriceRecord)
    if product_name:
        q = q.filter(PriceRecord.product_name == product_name)
    if origin:
        q = q.filter(PriceRecord.origin == origin)
    if date_start:
        q = q.filter(PriceRecord.record_date >= date_start)
    if date_end:
        q = q.filter(PriceRecord.record_date <= date_end)
    if price_min is not None:
        q = q.filter(PriceRecord.price >= price_min)
    if price_max is not None:
        q = q.filter(PriceRecord.price <= price_max)
    q = q.order_by(PriceRecord.record_date.desc()).offset((page - 1) * page_size).limit(page_size)
    return q.all()


@router.post("/weather", response_model=WeatherRecordResponse)
def create_weather_record(
    data: WeatherRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = WeatherRecord(
        origin=data.origin,
        record_date=data.record_date,
        temp_avg=data.temp_avg,
        precipitation=data.precipitation,
        sunshine_hours=data.sunshine_hours,
        extreme_weather=data.extreme_weather,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.get("/weather", response_model=List[WeatherRecordResponse])
def list_weather(
    origin: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(WeatherRecord)
    if origin:
        q = q.filter(WeatherRecord.origin == origin)
    if date_start:
        q = q.filter(WeatherRecord.record_date >= date_start)
    if date_end:
        q = q.filter(WeatherRecord.record_date <= date_end)
    q = q.order_by(WeatherRecord.record_date.desc()).offset((page - 1) * page_size).limit(page_size)
    return q.all()


@router.post("/import/price")
def import_price_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传 Excel 导入价格数据。

    支持的列名（至少需要包含产品名称 + 批发价格 + 日期）：
    - 市场名称: market_name
    - 产品名称 / 品种 / 品名: product_name
    - 批发价格 / 价格 / 平均价: price
    - 日期 / 时间: record_date
    - 地区: origin（本项目统一为广东，可写具体城市如“广东-广州”）
    """
    content = file.file.read()
    df = pd.read_excel(io.BytesIO(content))
    col_map = {
        "市场名称": "market_name",
        "产品名称": "product_name",
        "品种": "product_name",
        "品名": "product_name",
        "批发价格": "price",
        "价格": "price",
        "平均价": "price",
        "日期": "record_date",
        "时间": "record_date",
        "地区": "origin",
    }
    for src, dst in col_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]

    if "record_date" not in df.columns:
        raise HTTPException(status_code=400, detail="缺少日期/时间列（日期 或 时间）")

    df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce").dt.date
    df = df.dropna(subset=["record_date"])
    n = 0
    for _, row in df.iterrows():
        price_val = row.get("price", row.get("批发价格", None))
        if pd.isna(price_val):
            continue
        r = PriceRecord(
            market_name=str(row.get("market_name", row.get("市场名称", ""))) or None,
            product_name=str(row.get("product_name", row.get("产品名称", ""))),
            price=float(price_val),
            origin="广东-广州",
            sale_region=None,
            record_date=row["record_date"],
            spec=str(row.get("spec", "中等")),
        )
        db.add(r)
        n += 1
    db.commit()
    return {"imported": n}


@router.post("/import/weather")
def import_weather_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传 Excel 导入天气数据。

    支持的列名（至少需要包含时间 + 平均气温 或 最高/最低气温）：
    - 时间 / 日期: record_date
    - 最高气温: temp_max
    - 最低气温: temp_min
    - 平均气温 / 日平均气温: temp_avg
    - 降水 / 日降水量: precipitation
    - 平均相对湿度: humidity_avg
    - 气压: pressure
    - 地区（可选，缺省时默认“广东-广州”）: origin
    """
    content = file.file.read()
    df = pd.read_excel(io.BytesIO(content))
    col_map = {
        "时间": "record_date",
        "日期": "record_date",
        "地区": "origin",
        "最高气温": "temp_max",
        "最低气温": "temp_min",
        "平均气温": "temp_avg",
        "降水": "precipitation",
        "平均相对湿度": "humidity_avg",
        "气压": "pressure",
    }
    for src, dst in col_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]

    if "record_date" not in df.columns:
        raise HTTPException(status_code=400, detail="缺少时间/日期列（时间 或 日期）")

    # 统一解析日期，兼容 2015年06月05日 / 2015-06-05 / 2015/06/05 等格式
    df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce").dt.date

    df = df.dropna(subset=["record_date"])

    if "origin" not in df.columns:
        df["origin"] = "广东-广州"

    # 数值列转换
    num_cols = ["temp_max", "temp_min", "temp_avg", "precipitation", "humidity_avg", "pressure"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 若未给平均气温，则用最高/最低气温求平均
    if "temp_avg" not in df.columns or df["temp_avg"].isna().all():
        if "temp_max" in df.columns and "temp_min" in df.columns:
            df["temp_avg"] = (df["temp_max"] + df["temp_min"]) / 2

        # 自动判断极端天气（如果 Excel 中没有提供）
    if "extreme_weather" not in df.columns or df["extreme_weather"].isna().all():
        print("正在根据气象数据自动判断极端天气...")
        df["extreme_weather"] = df.apply(
            lambda row: detect_extreme_weather(
                temp_avg=row.get("temp_avg"),
                precipitation=row.get("precipitation"),
                temp_max=row.get("temp_max"),
                temp_min=row.get("temp_min")
            ),
            axis=1
        )
        extreme_count = (df["extreme_weather"] != "无极端天气").sum()
        print(f"自动识别到 {extreme_count} 天的极端天气")

    n = 0
    for _, row in df.iterrows():
        r = WeatherRecord(
            origin="广东-广州",
            record_date=row["record_date"],
            temp_max=float(row["temp_max"]) if pd.notna(row.get("temp_max")) else None,
            temp_min=float(row["temp_min"]) if pd.notna(row.get("temp_min")) else None,
            temp_avg=float(row["temp_avg"]) if pd.notna(row.get("temp_avg")) else None,
            precipitation=float(row["precipitation"]) if pd.notna(row.get("precipitation")) else None,
            humidity_avg=float(row["humidity_avg"]) if pd.notna(row.get("humidity_avg")) else None,
            pressure=float(row["pressure"]) if pd.notna(row.get("pressure")) else None,
            sunshine_hours=None,
            extreme_weather="无极端天气",
        )
        db.add(r)
        n += 1
    db.commit()
    return {"imported": n}


@router.post("/crawl")
def trigger_crawl(
    products: Optional[List[str]] = Query(None),
    days_back: int = 365,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发爬虫抓取价格与天气（占位实现，实际需配置目标站）"""
    price_df, weather_df = crawl_all(products=products, days_back=days_back)
    # 若爬虫返回了数据，可在此写入 DB
    return {"price_rows": len(price_df), "weather_rows": len(weather_df), "message": "爬虫接口已调用，实际采集需配置数据源"}


@router.get("/export")
def export_data(
    data_type: str = Query(..., description="price | weather | integrated"),
    product_names: Optional[str] = Query(None),
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """导出 Excel 文件"""
    products = product_names.split(",") if product_names else None
    path = export_excel(db, data_type=data_type, product_names=products, date_start=date_start, date_end=date_end)
    return FileResponse(path, filename=path.split("/")[-1].split("\\")[-1])


@router.post("/load-local")
def load_local_data(
    clear_before: bool = Query(True, description="加载前是否清空现有价格与天气数据"),
    remove_outliers: bool = Query(True, description="是否剔除价格异常值（均值±3倍标准差）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    从配置的本地 Excel 路径加载白菜、土豆价格与广州天气数据，预处理后写入数据库。
    路径在 .env 或 config 中：DATA_CABBAGE_PATH, DATA_POTATO_PATH, DATA_WEATHER_PATH。
    """
    try:
        price_df, weather_df = load_and_preprocess_all(remove_price_outliers=remove_outliers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载或预处理失败: {str(e)}")

    if price_df.empty and weather_df.empty:
        raise HTTPException(
            status_code=400,
            detail="未读取到任何数据，请检查 DATA_CABBAGE_PATH / DATA_POTATO_PATH / DATA_WEATHER_PATH 路径及 Excel 列名。",
        )

    try:
        n_price, n_weather = save_to_db(price_df, weather_df, db, clear_before=clear_before)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入数据库失败: {str(e)}")

    return {
        "message": "本地数据加载完成",
        "price_rows": n_price,
        "weather_rows": n_weather,
        "price_preview_rows": len(price_df),
        "weather_preview_rows": len(weather_df),
    }
