"""机器学习预测：训练、预测、模型对比"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionItem,
    ModelMetrics,
    TrainRequest,
    MultiPredictionRequest,
    MultiPredictionResponse,
    SingleModelPrediction,
)
from app.services.ml_service import (
    train_and_evaluate,
    train_and_evaluate_ensemble,
    predict_future,
    predict_future_ensemble,
    list_supported_models,
    BASE_MODEL_MAP,
    ENSEMBLE_MODEL_NAME,
)
from app.services.auth import get_current_user
from app.models.user import User
from app.models.prediction import PredictionRecord, ModelRun
from decimal import Decimal

router = APIRouter(prefix="/predict", tags=["机器学习预测"])


@router.post("/train")
def train_models(
    body: TrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """训练多模型并返回 MAE/RMSE/MAPE 对比"""
    results = []
    for model_name in body.models:
        if model_name == ENSEMBLE_MODEL_NAME:
            base_models = body.ensemble_base_models
            if not base_models:
                base_models = [m for m in body.models if m != ENSEMBLE_MODEL_NAME]
            res = train_and_evaluate_ensemble(
                db,
                body.product_name,
                base_models=base_models,
                train_ratio=body.train_ratio,
                use_weather=True,
            )
        else:
            if model_name not in BASE_MODEL_MAP:
                continue
            res = train_and_evaluate(
                db,
                body.product_name,
                model_name,
                train_ratio=body.train_ratio,
                use_weather=True,
            )
        if "error" in res:
            results.append({"model_name": model_name, "error": res["error"]})
            continue
        # 持久化 ModelRun
        mr = ModelRun(
            product_name=body.product_name,
            model_name=model_name,
            mae=Decimal(str(res["mae"])),
            rmse=Decimal(str(res["rmse"])),
            mape=Decimal(str(res["mape"])),
        )
        db.add(mr)
        db.commit()
        results.append({
            "model_name": model_name,
            "mae": res["mae"],
            "rmse": res["rmse"],
            "mape": res["mape"],
        })
    return {"results": results}


@router.post("/predict", response_model=PredictionResponse)
def predict(
    body: PredictionRequest,
    db: Session = Depends(get_db),
):
    """短期预测：1/3/7 天，返回预测价格及置信区间"""
    if body.model_name == ENSEMBLE_MODEL_NAME:
        res = train_and_evaluate_ensemble(
            db,
            body.product_name,
            base_models=None,
            use_weather=body.use_weather,
        )
    else:
        res = train_and_evaluate(
            db,
            body.product_name,
            body.model_name,
            use_weather=body.use_weather,
        )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    if body.model_name == ENSEMBLE_MODEL_NAME:
        preds = predict_future_ensemble(res, steps=body.predict_days)
    else:
        preds = predict_future(res, steps=body.predict_days)
    items = [PredictionItem(**p) for p in preds]
    metrics = ModelMetrics(
        model_name=body.model_name,
        mae=res["mae"],
        rmse=res["rmse"],
        mape=res["mape"],
    )
    return PredictionResponse(
        product_name=body.product_name,
        model_name=body.model_name,
        metrics=metrics,
        predictions=items,
    )


@router.post("/predict-multi", response_model=MultiPredictionResponse)
def predict_multi(
    body: MultiPredictionRequest,
    db: Session = Depends(get_db),
):
    results: List[SingleModelPrediction] = []
    for model_name in body.model_names:
        if model_name == ENSEMBLE_MODEL_NAME:
            res = train_and_evaluate_ensemble(
                db,
                body.product_name,
                base_models=body.ensemble_base_models,
                use_weather=body.use_weather,
            )
            if "error" in res:
                continue
            preds = predict_future_ensemble(res, steps=body.predict_days)
            items = [PredictionItem(**p) for p in preds]
            metrics = ModelMetrics(
                model_name=model_name,
                mae=res["mae"],
                rmse=res["rmse"],
                mape=res["mape"],
            )
            results.append(SingleModelPrediction(model_name=model_name, metrics=metrics, predictions=items, meta=res.get("weights")))
        else:
            if model_name not in BASE_MODEL_MAP:
                continue
            res = train_and_evaluate(
                db,
                body.product_name,
                model_name,
                use_weather=body.use_weather,
            )
            if "error" in res:
                continue
            preds = predict_future(res, steps=body.predict_days)
            items = [PredictionItem(**p) for p in preds]
            metrics = ModelMetrics(
                model_name=model_name,
                mae=res["mae"],
                rmse=res["rmse"],
                mape=res["mape"],
            )
            results.append(SingleModelPrediction(model_name=model_name, metrics=metrics, predictions=items))
    return MultiPredictionResponse(product_name=body.product_name, results=results)


@router.get("/models")
def list_models():
    """支持的模型列表"""
    return {"models": list_supported_models()}
