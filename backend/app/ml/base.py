"""模型基类与数据准备"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from abc import ABC, abstractmethod


def prepare_ts(
    df: pd.DataFrame,
    target_col: str = "price",
    date_col: str = "record_date",
    lag_days: int = 7,
    weather_cols: Optional[list] = None,
) -> Tuple[np.ndarray, np.ndarray, Optional[pd.DataFrame]]:
    """
    准备时间序列：目标列 + 滞后特征 + 可选天气特征。
    返回 X, y, feature_names（用于需要特征名的模型）。
    """
    df = df.sort_values(date_col).reset_index(drop=True)
    df = df.dropna(subset=[target_col])
    y = df[target_col].values
    features = []
    for i in range(1, lag_days + 1):
        features.append(df[target_col].shift(i).values)
    X_lag = np.column_stack(features)
    if weather_cols:
        for c in weather_cols:
            if c in df.columns:
                features.append(df[c].fillna(df[c].mean()).values)
        X = np.column_stack(features)
    else:
        X = X_lag
    # 去掉前 lag_days 行（无滞后）
    X, y = X[lag_days:], y[lag_days:]
    return X, y, None


class BasePredictor(ABC):
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "BasePredictor":
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        pass
