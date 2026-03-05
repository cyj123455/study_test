"""多源数据采集：蔬菜网/农业农村部/中国天气网 - PRD 3.1 爬虫占位与接口"""
import pandas as pd
from typing import List, Optional
from datetime import date, timedelta

# 实际爬虫需根据目标网站结构实现，此处提供接口与示例数据结构


def crawl_vegetable_prices(
    products: Optional[List[str]] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
) -> pd.DataFrame:
    """
    从蔬菜网等抓取白菜（矮脚/本地/小塘）、土豆批发价格。
    返回列：product_name, price, origin, sale_region, record_date, spec
    """
    # 占位：实际应使用 requests + BeautifulSoup 或 API
    # 可配置蔬菜网接口、农业农村部官网
    return pd.DataFrame(
        columns=["product_name", "price", "origin", "sale_region", "record_date", "spec"]
    )


def crawl_weather(
    regions: Optional[List[str]] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
) -> pd.DataFrame:
    """
    从中国天气网采集产区：日平均气温、降水量、日照时长、极端天气标识。
    返回列：origin, record_date, temp_avg, precipitation, sunshine_hours, extreme_weather
    """
    # 占位：实际应请求中国天气网，解析极端天气枚举
    return pd.DataFrame(
        columns=[
            "origin",
            "record_date",
            "temp_avg",
            "precipitation",
            "sunshine_hours",
            "extreme_weather",
        ]
    )


def crawl_all(
    products: Optional[List[str]] = None,
    days_back: int = 365,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """一次性抓取价格与天气，默认近 1 年。返回 (price_df, weather_df)。"""
    end = date.today()
    start = end - timedelta(days=days_back)
    products = products or ["矮脚白菜", "本地白菜", "小塘白菜", "土豆"]
    price_df = crawl_vegetable_prices(products=products, date_start=start, date_end=end)
    regions = price_df["origin"].dropna().unique().tolist() if not price_df.empty else []
    weather_df = crawl_weather(regions=regions, date_start=start, date_end=end)
    return price_df, weather_df
