"""评估指标：MAE、RMSE、MAPE - PRD 验收 MAE≤0.3 元/公斤、MAPE≤8%"""
import numpy as np


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-8) -> float:
    """MAPE 百分比，避免除零"""
    return float(np.mean(np.abs((y_true - y_pred) / (y_true + eps))) * 100)


def all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "mae": round(mae(y_true, y_pred), 4),
        "rmse": round(rmse(y_true, y_pred), 4),
        "mape": round(mape(y_true, y_pred), 2),
    }
