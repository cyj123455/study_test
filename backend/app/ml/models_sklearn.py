"""SVR、随机森林 - scikit-learn"""
from typing import Optional
import numpy as np
from app.ml.base import BasePredictor

from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor


class SVRPredictor(BasePredictor):
    def __init__(self, kernel: str = "rbf", C: float = 1.0):
        self.kernel = kernel
        self.C = C
        self.model_ = SVR(kernel=kernel, C=C)

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "SVRPredictor":
        self.model_.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model_.predict(X)


class RFPredictor(BasePredictor):
    def __init__(self, n_estimators: int = 100, max_depth: Optional[int] = 10):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.model_ = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth)

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "RFPredictor":
        self.model_.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model_.predict(X)
