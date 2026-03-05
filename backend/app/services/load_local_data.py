"""从本地 Excel 加载白菜/土豆价格与天气数据，预处理后写入数据库 - PRD 3.1"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import date

from app.config import get_settings
from app.services.preprocess import (
    fill_missing_mean,
    remove_outliers_df,
    integrate_price_weather,
)
from app.models.price import PriceRecord
from app.models.weather import WeatherRecord
from app.services.analysis import detect_extreme_weather

settings = get_settings()

# 价格表可能列名（江南果菜市场等）
PRICE_COL_MAP = [
    ("市场名称","market_name"),
    ("产品名称", "product_name"),
    ("批发价格", "price"),
    ("价格", "price"),
    ("地区", "origin"),
    ("日期", "record_date"),
    ("产品规格", "spec"),
]

# 天气表可能列名（广东省-广州等）
WEATHER_COL_MAP = [
    ("地区", "origin"),
    ("时间", "record_date"),  # 添加这一行
    ("最高气温", "temp_max"),
    ("最低气温", "temp_min"),
    ("平均气温", "temp_avg"),
    ("降水", "precipitation"),
    ("平均相对湿度", "humidity_avg"),
    ("气压", "pressure"),
    ("极端天气标识", "extreme_weather"),
]

# 产品名称标准化：映射到 PRD 枚举
PRODUCT_NORMALIZE = {
    "矮脚白菜": "矮脚白菜",
    "本地白菜": "本地白菜",
    "小塘白菜": "小塘白菜",
    "土豆": "土豆",
}

EXTREME_WEATHER_VALID = {"无极端天气","暴雨", "低温", "高温",  "干旱" }


def _normalize_columns(df: pd.DataFrame, col_map: List[Tuple[str, str]]) -> pd.DataFrame:
    """将 Excel 列名映射为统一字段名，取第一个匹配的列"""
    out = pd.DataFrame()
    for src_name, dst_name in col_map:
        if dst_name in out.columns:
            continue
        if src_name in df.columns:
            out[dst_name] = df[src_name]
    return out


# def _parse_date(series: pd.Series) -> pd.Series:
#     """统一转为 date，支持多种格式"""
#     return pd.to_datetime(series, errors="coerce").dt.normalize()
def _parse_date(series: pd.Series) -> pd.Series:
    """统一转为 date，支持多种日期格式"""
    # 定义常见的日期格式
    date_formats = [
        '%Y-%m-%d',  # 2023-01-15
        '%Y/%m/%d',  # 2023/01/15
        '%Y.%m.%d',  # 2023.01.15
        '%m/%d/%Y',  # 01/15/2023
        '%d/%m/%Y',  # 15/01/2023
        '%Y年%m月%d日',  # 2023年01月15日
        '%Y-%m-%d %H:%M:%S',  # 2023-01-15 10:30:00
        '%Y/%m/%d %H:%M:%S',  # 2023/01/15 10:30:00
    ]

    # 尝试逐个格式解析
    for fmt in date_formats:
        try:
            parsed = pd.to_datetime(series, format=fmt, errors='coerce')
            if not parsed.isna().all():  # 如果至少解析成功了一些数据
                print(f"使用日期格式 {fmt} 成功解析 {parsed.notna().sum()} 条记录")
                return parsed.dt.normalize()
        except Exception:
            continue

    # 如果所有格式都失败，使用默认的智能解析（会产生警告但能处理大多数情况）
    print("使用默认日期解析方式...")
    return pd.to_datetime(series, infer_datetime_format=True, errors="coerce").dt.normalize()


def load_price_excel(
    path: str,
    product_filter: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    从本地 Excel 加载价格数据，列名自动映射。
    product_filter: 仅保留这些产品名称，如 None 表示全部。
    """
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()

    # 支持多 sheet：常见为第一个 sheet 或按 sheet 名
    try:
        df = pd.read_excel(path, sheet_name=0)
    except Exception:
        df = pd.read_excel(path)

    df = _normalize_columns(df, PRICE_COL_MAP)
    if df.empty or "price" not in df.columns:
        return pd.DataFrame()

    # 必须有日期与价格
    if "record_date" not in df.columns:
        for c in ["日期", "交易日期", "发布日期"]:
            if c in df.columns:
                df["record_date"] = df[c]
                break
    if "record_date" not in df.columns:
        return pd.DataFrame()

    df["record_date"] = _parse_date(df["record_date"])
    df = df.dropna(subset=["record_date"])
    df["record_date"] = df["record_date"].dt.date

    # 价格：元/斤 转 元/公斤
    price_col = df["price"].astype(str).str.replace(",", "").str.replace(" ", "")
    price_num = pd.to_numeric(price_col, errors="coerce")
    # 若表头或单位说明为「元/斤」，可在此乘以 2；这里默认已是元/公斤，若需可根据实际列判断
    df["price"] = price_num

    if "product_name" not in df.columns and "产品名称" in df.columns:
        df["product_name"] = df["产品名称"]
    if "product_name" in df.columns:
        df["product_name"] = df["product_name"].astype(str).str.strip()
        df["product_name"] = df["product_name"].replace(PRODUCT_NORMALIZE)
    if "origin" not in df.columns:
        df["origin"] = None
    if "sale_region" not in df.columns:
        df["sale_region"] = None
    df["spec"] = df.get("spec", "中等")
    if df["spec"].isna().all():
        df["spec"] = "中等"

    # 过滤产品
    if product_filter is not None and "product_name" in df.columns:
        df = df[df["product_name"].isin(product_filter)]

    # 丢弃无价格行
    df = df.dropna(subset=["price"])
    df["price"] = df["price"].astype(float).round(2)
    return df.reset_index(drop=True)


def load_weather_excel(path: str) -> pd.DataFrame:
    """从本地 Excel 加载天气数据"""
    print(f"尝试加载天气数据文件: {path}")  # 调试信息

    path = Path(path)
    print(f"文件是否存在: {path.exists()}")  # 调试信息
    if not path.exists():
        print("天气文件不存在!")  # 调试信息
        return pd.DataFrame()

    try:
        df = pd.read_excel(path, sheet_name=0)
        print(f"成功读取Excel，形状: {df.shape}")  # 调试信息
        print(f"列名: {list(df.columns)}")  # 调试信息
        # 添加降水数据的详细调试信息
        precip_cols = [col for col in df.columns if '降水' in col or '降雨' in col]
        if precip_cols:
            print(f"找到降水相关列: {precip_cols}")
            for col in precip_cols:
                print(f"列 '{col}' 的前5个值: {df[col].head().tolist()}")
    except Exception as e:
        print(f"读取Excel失败: {e}")  # 调试信息
        df = pd.read_excel(path)

    df = _normalize_columns(df, WEATHER_COL_MAP)
    if df.empty or "record_date" not in df.columns:
        if "日期" in df.columns:
            df["record_date"] = df["日期"]
        else:
            return pd.DataFrame()

    df["record_date"] = _parse_date(df["record_date"])
    df = df.dropna(subset=["record_date"])
    df["record_date"] = df["record_date"].dt.date

    # if "origin" not in df.columns:
    #     # 广东省-广州 可能只有一地，用文件名或默认
    #     df["region"] = "广东-广州"
    # df["region"] = df["region"].astype(str).str.strip()
    if "origin" not in df.columns:
        # 广东省-广州 可能只有一地，用文件名或默认
        df["origin"] = "广东-广州"
        # 修复：正确处理NaN值，避免转换为"nan"字符串
    df["origin"] = df["origin"].fillna("广东-广州").astype(str).str.strip()
    # 若仅有最高/最低气温，则计算日平均
    if "temp_avg" not in df.columns or df["temp_avg"].isna().all():
        if "temp_max" in df.columns and "temp_min" in df.columns:
            df["temp_avg"] = (pd.to_numeric(df["temp_max"], errors="coerce") + pd.to_numeric(df["temp_min"], errors="coerce")) / 2
        elif "temp_max" in df.columns:
            df["temp_avg"] = pd.to_numeric(df["temp_max"], errors="coerce")
        elif "temp_min" in df.columns:
            df["temp_avg"] = pd.to_numeric(df["temp_min"], errors="coerce")

    # 数值列转换：最高/最低/平均气温、降水、湿度、气压
    num_cols = ["temp_max", "temp_min", "temp_avg", "precipitation", "humidity_avg", "pressure"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = fill_missing_mean(df[col])
            # 气温、降水、湿度、气压统一保留 1 位小数
            df[col] = df[col].round(1)
        else:
            df[col] = np.nan

    if "extreme_weather" not in df.columns:
        df["extreme_weather"] = "无极端天气"
    else:
        df["extreme_weather"] = df["extreme_weather"].fillna("无极端天气").astype(str).str.strip()
        df.loc[~df["extreme_weather"].isin(EXTREME_WEATHER_VALID), "extreme_weather"] = "无极端天气"
        # 如果 Excel 中没有极端天气标识，根据气温和降水自动判断
    if df["extreme_weather"].eq("无极端天气").all():
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

    return df.reset_index(drop=True)


def preprocess_price(df: pd.DataFrame, remove_outliers: bool = True) -> pd.DataFrame:
    """价格预处理：缺失值均值填充、异常值剔除（均值±3倍标准差）"""
    if df.empty or "price" not in df.columns:
        return df
    df = df.copy()
    df["price"] = fill_missing_mean(df["price"])
    df["price"] = df["price"].round(2)
    if remove_outliers:
        # 按产品分组剔除异常值，避免不同产品混在一起
        out = []
        for name, g in df.groupby("product_name", dropna=False):
            g = remove_outliers_df(g, "price", inplace=False)
            out.append(g)
        if out:
            df = pd.concat(out, ignore_index=True)
        else:
            df = remove_outliers_df(df, "price", inplace=False)
    return df


def preprocess_weather(df: pd.DataFrame) -> pd.DataFrame:
    """天气预处理：数值列均值填充、保留一位小数。
    只处理真正需要的数值列，避免字符串参与求均值导致报错。
    """
    if df.empty:
        return df
    df = df.copy()
    numeric_cols = ["temp_max", "temp_min", "temp_avg", "precipitation", "humidity_avg", "pressure"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = fill_missing_mean(df[col])
            df[col] = df[col].round(1)
    return df


def load_and_preprocess_all(
    cabbage_path: Optional[str] = None,
    potato_path: Optional[str] = None,
    weather_path: Optional[str] = None,
    remove_price_outliers: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    加载白菜、土豆、天气三个 Excel，预处理后返回 (价格 DataFrame, 天气 DataFrame)。
    若 cabbage_path 与 potato_path 相同，则从同一文件按产品名称区分白菜类与土豆。
    """
    cabbage_path = cabbage_path or settings.DATA_CABBAGE_PATH
    potato_path = potato_path or settings.DATA_POTATO_PATH
    weather_path = weather_path or settings.DATA_WEATHER_PATH

    cabbage_df = load_price_excel(cabbage_path, product_filter=["矮脚白菜", "本地白菜", "小塘白菜"])
    if cabbage_path == potato_path:
        potato_df = load_price_excel(potato_path, product_filter=["土豆"])
        price_df = pd.concat([cabbage_df, potato_df], ignore_index=True)
    else:
        potato_df = load_price_excel(potato_path, product_filter=["土豆"])
        price_df = pd.concat([cabbage_df, potato_df], ignore_index=True)

    # 若未按产品名过滤到，则尝试整表加载再按名称筛选
    valid = ["矮脚白菜", "本地白菜", "小塘白菜", "土豆"]
    if price_df.empty:
        price_df = load_price_excel(cabbage_path, product_filter=None)
        if not price_df.empty and "product_name" in price_df.columns:
            price_df = price_df[price_df["product_name"].isin(valid)]
        if potato_path != cabbage_path:
            p2 = load_price_excel(potato_path, product_filter=None)
            if not p2.empty:
                if price_df.empty:
                    price_df = p2
                else:
                    price_df = pd.concat([price_df, p2], ignore_index=True)
                if "product_name" in price_df.columns:
                    price_df = price_df[price_df["product_name"].isin(valid)]

    price_df = preprocess_price(price_df, remove_outliers=remove_price_outliers)
    weather_df = load_weather_excel(weather_path)
    weather_df = preprocess_weather(weather_df)

    return price_df, weather_df


def save_to_db(
    price_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    db_session,
    clear_before: bool = True,
) -> Tuple[int, int]:
    """
    将预处理后的价格、天气 DataFrame 写入数据库。
    clear_before: 是否先清空现有 price_records / weather_records（可选）。
    返回 (写入价格条数, 写入天气条数)。
    """
    from app.models.price import PriceRecord
    from app.models.weather import WeatherRecord

    if clear_before:
        db_session.query(PriceRecord).delete()
        db_session.query(WeatherRecord).delete()
        db_session.commit()

    n_price = 0
    # for _, row in price_df.iterrows():
    #     r = PriceRecord(
    #         product_name=str(row.get("product_name", "")),
    #         price=float(row["price"]),
    #         origin=str(row["origin"]) if pd.notna(row.get("origin")) else None,
    #         sale_region=str(row["sale_region"]) if pd.notna(row.get("sale_region")) else None,
    #         record_date=row["record_date"] if isinstance(row["record_date"], date) else pd.Timestamp(row["record_date"]).date(),
    #         spec=str(row.get("spec", "中等")),
    #     )
    #     db_session.add(r)
    #     n_price += 1
    for _, row in price_df.iterrows():
        r = PriceRecord(
            market_name=str(row["market_name"]) if pd.notna(row.get("market_name")) else None,
            product_name=str(row.get("product_name", "")),
            price=float(row["price"]),
            origin=str(row["origin"]) if pd.notna(row.get("origin")) else "广东",
            record_date=row["record_date"] if isinstance(row["record_date"], date) else pd.Timestamp(
                row["record_date"]).date(),
        )
        db_session.add(r)
        n_price += 1

    n_weather = 0
    print(f"开始保存天气数据，共 {len(weather_df)} 行")  # 调试信息
    for i, (_, row) in enumerate(weather_df.iterrows()):
        try:
            r = WeatherRecord(
                origin=str(row.get("origin", "广东-广州")),
                record_date=row["record_date"] if isinstance(row["record_date"], date) else pd.Timestamp(
                    row["record_date"]).date(),
                temp_max=float(row["temp_max"]) if pd.notna(row.get("temp_max")) else None,
                temp_min=float(row["temp_min"]) if pd.notna(row.get("temp_min")) else None,
                temp_avg=float(row["temp_avg"]) if pd.notna(row.get("temp_avg")) else None,
                precipitation=float(row["precipitation"]) if pd.notna(row.get("precipitation")) else None,
                humidity_avg=float(row["humidity_avg"]) if pd.notna(row.get("humidity_avg")) else None,
                pressure=float(row["pressure"]) if pd.notna(row.get("pressure")) else None,
                extreme_weather=str(row.get("extreme_weather", "无极端天气")),
            )
            db_session.add(r)
            n_weather += 1
            if i < 3:  # 只打印前3行的调试信息
                print(
                    f"第{i + 1}行天气数据: 日期={row.get('record_date')}, 区域={row.get('origin')}, 平均气温={row.get('temp_avg')}")
        except Exception as e:
            print(f"保存第{i + 1}行天气数据时出错: {e}")
            print(f"行数据: {row.to_dict()}")
            raise

    db_session.commit()
    return n_price, n_weather
