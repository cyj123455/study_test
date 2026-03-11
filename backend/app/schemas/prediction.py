from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date


class PredictionRequest(BaseModel):
    product_name: str
    model_name: str  # ARIMA / LSTM / SVR / 随机森林
    predict_days: int = 7  # 1 / 3 / 7 天
    use_weather: bool = True
    use_extreme_weather: bool = True
    eval_mode: str = "walk_forward"
    cv_folds: int = 5


class ModelMetrics(BaseModel):
    model_name: str
    mae: float
    rmse: float
    mape: float


class PredictionItem(BaseModel):
    predict_date: date
    price_pred: float
    confidence_low: Optional[float] = None
    confidence_high: Optional[float] = None


class PredictionResponse(BaseModel):
    product_name: str
    model_name: str
    metrics: Optional[ModelMetrics] = None
    predictions: List[PredictionItem]


class SingleModelPrediction(BaseModel):
    model_name: str
    metrics: Optional[ModelMetrics] = None
    predictions: List[PredictionItem]
    meta: Optional[Dict[str, float]] = None


class MultiPredictionRequest(BaseModel):
    product_name: str
    model_names: List[str]
    predict_days: int = 7
    use_weather: bool = True
    ensemble_base_models: Optional[List[str]] = None
    eval_mode: str = "walk_forward"
    cv_folds: int = 5


class MultiPredictionResponse(BaseModel):
    product_name: str
    results: List[SingleModelPrediction]


class TrainRequest(BaseModel):
    product_name: str
    models: List[str]  # 可多选
    train_ratio: float = 0.8
    cv_folds: int = 5
    ensemble_base_models: Optional[List[str]] = None
    eval_mode: str = "walk_forward"
