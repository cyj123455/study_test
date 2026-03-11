"""LSTM 深度学习模型"""
import numpy as np
from typing import Optional
from app.ml.base import BasePredictor

try:
    from tensorflow import keras
    from tensorflow.keras import layers
    HAS_TF = True
except ImportError:
    HAS_TF = False


def _build_lstm(seq_len: int, n_features: int, units: int = 32) -> keras.Model:
    model = keras.Sequential([
        layers.LSTM(units, input_shape=(seq_len, n_features), return_sequences=False),
        layers.Dense(16, activation="relu"),
        layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


class LSTMPredictor(BasePredictor):
    """LSTM：输入 (samples, seq_len, features)，输出 1 步预测"""
    def __init__(self, units: int = 32, epochs: int = 50, batch_size: int = 32):
        self.units = units
        self.epochs = epochs
        self.batch_size = batch_size
        self.model_ = None
        self.seq_len_ = None
        self.n_features_ = None

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "LSTMPredictor":
        if not HAS_TF:
            raise RuntimeError("需要安装 TensorFlow")
        # X 假设为 (n, lag*features) 或 (n, lag)，转为 (n, seq_len, n_features)
        if X.ndim == 2:
            self.seq_len_ = X.shape[1]
            self.n_features_ = 1
            X_3d = X.reshape(X.shape[0], X.shape[1], 1)
        else:
            X_3d = X
            self.seq_len_ = X.shape[1]
            self.n_features_ = X.shape[2]
        self.model_ = _build_lstm(self.seq_len_, self.n_features_, self.units)
        self.model_.fit(
            X_3d, y,
            epochs=self.epochs,
            batch_size=min(self.batch_size, len(X_3d)),
            verbose=0,
        )
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model_ is None:
            raise ValueError("先调用 fit")
        if X.ndim == 2:
            X = X.reshape(X.shape[0], X.shape[1], 1)
        return self.model_.predict(X, verbose=0).flatten()
