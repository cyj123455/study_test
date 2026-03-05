"""ARIMA 时间序列模型"""
import numpy as np
import pandas as pd
from typing import Optional
from app.ml.base import BasePredictor

try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_ARIMA = True
except ImportError:
    HAS_ARIMA = False


class ARIMAPredictor(BasePredictor):
    """ARIMA(p,d,q)，仅用价格序列"""
    def __init__(self, order: tuple = (2, 0, 2)):
        self.order = order
        self.model_ = None
        self._y_series: Optional[pd.Series] = None

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "ARIMAPredictor":
        if not HAS_ARIMA:
            raise RuntimeError("需要安装 statsmodels")
        # ARIMA 用完整 y，这里 X 可能是滞后，我们只用 y 做单变量
        self._y_series = pd.Series(y)
        self.model_ = ARIMA(self._y_series, order=self.order)
        self.model_ = self.model_.fit()
        return self

    def predict(self, X: np.ndarray = None, steps: int = 1) -> np.ndarray:
        if self.model_ is None:
            raise ValueError("先调用 fit")
        f = self.model_.get_forecast(steps=steps)
        return np.asarray(f.predicted_mean.values).flatten()
