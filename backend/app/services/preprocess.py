"""数据预处理：缺失值、标准化、异常值、数据集成 - PRD 3.1"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from app.config import get_settings
# 解决FutureWarning
pd.set_option('future.no_silent_downcasting', True)

settings = get_settings()
STD_MULT = settings.OUTLIER_STD_MULTIPLIER  # 均值 ± 3 倍标准差


# def fill_missing_mean(series: pd.Series) -> pd.Series:
#     """缺失值：均值填充"""
#     return series.fillna(series.mean())
def fill_missing_mean(series: pd.Series) -> pd.Series:
    """缺失值：均值填充"""
    result = series.fillna(series.mean())
    return result.infer_objects(copy=False)

def fill_missing_regression(
    target: pd.Series, features: pd.DataFrame
) -> pd.Series:
    """缺失值：简单回归填充（用其它列预测）"""
    from sklearn.linear_model import LinearRegression
    mask = target.notna()
    if mask.sum() < 3 or mask.sum() == len(target):
        return target.fillna(target.mean())
    X = features.loc[mask]
    y = target.loc[mask]
    X_miss = features.loc[~mask]
    if len(X_miss) == 0:
        return target
    model = LinearRegression().fit(X, y)
    target = target.copy()
    target.loc[~mask] = model.predict(X_miss)
    return target


def standardize(series: pd.Series) -> pd.Series:
    """标准化 (z-score)"""
    mean, std = series.mean(), series.std()
    if std == 0:
        return series - mean
    return (series - mean) / std


def normalize_minmax(series: pd.Series) -> pd.Series:
    """归一化 [0,1]"""
    min_, max_ = series.min(), series.max()
    if max_ == min_:
        return series - min_
    return (series - min_) / (max_ - min_)


def detect_outliers(series: pd.Series, n_std: float = STD_MULT) -> pd.Series:
    """异常值：超出 均值 ± n_std 倍标准差 的索引（True=异常）"""
    mean, std = series.mean(), series.std()
    if std == 0:
        return pd.Series(False, index=series.index)
    return (series < mean - n_std * std) | (series > mean + n_std * std)


def remove_outliers_df(
    df: pd.DataFrame,
    column: str,
    n_std: float = STD_MULT,
    inplace: bool = False,
) -> pd.DataFrame:
    """剔除指定列的异常值（按均值±n_std标准差）"""
    if not inplace:
        df = df.copy()
    mask = ~detect_outliers(df[column], n_std)
    return df.loc[mask].reset_index(drop=True)


def integrate_price_weather(
    price_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    date_col: str = "record_date",
    region_key_price: str = "origin",
    region_key_weather: str = "origin",
) -> pd.DataFrame:
    """数据集成：按 日期+地区 关联价格与天气。地区字段统一为 origin。"""
    price_df = price_df.copy()
    weather_df = weather_df.copy()
    price_df[date_col] = pd.to_datetime(price_df[date_col]).dt.normalize()
    weather_df[date_col] = pd.to_datetime(weather_df[date_col]).dt.normalize()
    merged = price_df.merge(
        weather_df,
        left_on=[date_col, region_key_price],
        right_on=[date_col, region_key_weather],
        how="left",
    )
    return merged
