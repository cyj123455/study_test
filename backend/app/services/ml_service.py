"""机器学习预测服务：训练、评估、短期预测 - PRD 3.3"""
import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.price import PriceRecord
from app.models.weather import WeatherRecord
from app.ml.metrics import mae, rmse, mape, all_metrics
from app.ml.models_arima import ARIMAPredictor
from app.ml.models_lstm import LSTMPredictor
from app.ml.models_sklearn import SVRPredictor, RFPredictor
from app.config import get_settings

settings = get_settings()
TRAIN_RATIO = settings.TRAIN_TEST_SPLIT
CV_FOLDS = settings.CROSS_VALIDATION_FOLDS
CONFIDENCE_PCT = 0.05  # ±5% 置信区间

PRODUCT_NAMES = ("矮脚白菜", "本地白菜", "小塘白菜", "土豆")
MODEL_MAP = {
    "ARIMA": ARIMAPredictor,
    "LSTM": LSTMPredictor,
    "SVR": SVRPredictor,
    "随机森林": RFPredictor,
}


def load_product_data(
    db: Session,
    product_name: str,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    use_weather: bool = True,
) -> pd.DataFrame:
    """加载价格 + 可选天气，按 日期+地区(origin) 关联"""
    q = (
        db.query(PriceRecord.record_date, PriceRecord.price, PriceRecord.origin)
        .filter(PriceRecord.product_name == product_name)
        .order_by(PriceRecord.record_date)
    )
    if date_start:
        q = q.filter(PriceRecord.record_date >= date_start)
    if date_end:
        q = q.filter(PriceRecord.record_date <= date_end)
    rows = q.all()
    df = pd.DataFrame(rows, columns=["record_date", "price", "origin"])
    df["record_date"] = pd.to_datetime(df["record_date"])
    # 同一日多产地取均价
    df = df.groupby("record_date").agg({"price": "mean", "origin": "first"}).reset_index()
    if not use_weather or df.empty:
        return df
    origins = df["origin"].dropna().unique().tolist()
    if not origins:
        return df
    wq = db.query(
        WeatherRecord.record_date,
        WeatherRecord.origin,
        WeatherRecord.temp_avg,
        WeatherRecord.precipitation,
        WeatherRecord.humidity_avg,
    ).filter(WeatherRecord.origin.in_(origins))
    if date_start:
        wq = wq.filter(WeatherRecord.record_date >= date_start)
    if date_end:
        wq = wq.filter(WeatherRecord.record_date <= date_end)
    wrows = wq.all()
    wdf = pd.DataFrame(wrows, columns=["record_date", "origin", "temp_avg", "precipitation", "humidity_avg"])
    wdf["record_date"] = pd.to_datetime(wdf["record_date"])
    df = df.merge(wdf, left_on=["record_date", "origin"], right_on=["record_date", "origin"], how="left")
    return df


# def prepare_xy(
#     df: pd.DataFrame,
#     lag_days: int = 7,
#     use_weather: bool = True,
# ) -> tuple[np.ndarray, np.ndarray]:
#     """构造 X, y。X: 滞后价格 + 可选天气；y: 当日价格"""
#     df = df.sort_values("record_date").dropna(subset=["price"]).reset_index(drop=True)
#     y = df["price"].values[lag_days:]
#     cols = [df["price"].shift(i) for i in range(1, lag_days + 1)]
#     if use_weather and "temp_avg" in df.columns:
#         cols.append(df["temp_avg"].shift(1).bfill().ffill())
#     if use_weather and "precipitation" in df.columns:
#         cols.append(df["precipitation"].shift(1).fillna(0))
#     X = np.column_stack(cols)[lag_days:]
#     # 去掉含 NaN 的行
#     mask = ~np.isnan(X).any(axis=1)
#     X, y = X[mask].astype(np.float32), y[mask]
#     return X, y


def prepare_xy(
        df: pd.DataFrame,
        lag_days: int = 7,
        use_weather: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """构造 X, y。X: 滞后价格 + 可选天气；y: 当日价格"""
    # 数据预处理：确保数值列的类型正确
    df = df.sort_values("record_date").dropna(subset=["price"]).reset_index(drop=True)

    # 确保价格列为数值类型
    df["price"] = pd.to_numeric(df["price"], errors='coerce')
    df = df.dropna(subset=["price"])

    # 处理天气数据列
    if use_weather:
        weather_cols = ["temp_avg", "precipitation", "sunshine_hours"]
        for col in weather_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # 对于温度和降水，用前向填充和后向填充处理缺失值
                if col in ["temp_avg", "precipitation"]:
                    df[col] = df[col].fillna(method='ffill').fillna(method='bfill').fillna(0)
                else:
                    df[col] = df[col].fillna(0)

    y = df["price"].values[lag_days:]

    # 构造滞后特征
    cols = []
    for i in range(1, lag_days + 1):
        lag_col = df["price"].shift(i)
        # 确保滞后列为数值类型
        lag_col = pd.to_numeric(lag_col, errors='coerce')
        cols.append(lag_col)

    # 添加天气特征
    if use_weather and "temp_avg" in df.columns:
        temp_col = df["temp_avg"].shift(1)
        temp_col = pd.to_numeric(temp_col, errors='coerce').fillna(method='ffill').fillna(method='bfill').fillna(0)
        cols.append(temp_col)

    if use_weather and "precipitation" in df.columns:
        precip_col = df["precipitation"].shift(1)
        precip_col = pd.to_numeric(precip_col, errors='coerce').fillna(0)
        cols.append(precip_col)

    # 构造特征矩阵并确保所有列都是数值类型
    X_raw = np.column_stack(cols)

    # 移除前lag_days行（因为滞后特征需要历史数据）
    X_raw = X_raw[lag_days:]
    y = y[lag_days - len(y):] if len(y) > lag_days else y

    # 数据类型安全检查和清理
    # 将X转换为DataFrame以便更好地处理
    feature_names = [f"lag_{i}" for i in range(1, lag_days + 1)]
    if use_weather and "temp_avg" in df.columns:
        feature_names.append("temp_avg_lag1")
    if use_weather and "precipitation" in df.columns:
        feature_names.append("precipitation_lag1")

    X_df = pd.DataFrame(X_raw, columns=feature_names)

    # 确保所有列都是数值类型，并处理任何剩余的非数值数据
    for col in X_df.columns:
        X_df[col] = pd.to_numeric(X_df[col], errors='coerce')

    # 删除包含NaN的行
    X_df = X_df.dropna()

    # 确保y与X_df的索引对应
    valid_indices = X_df.index
    y_filtered = y[valid_indices] if len(y) > max(valid_indices) else y

    # 转换为numpy数组
    X = X_df.values.astype(np.float32)
    y_final = y_filtered.astype(np.float32)

    return X, y_final


def train_and_evaluate(
    db: Session,
    product_name: str,
    model_name: str,
    train_ratio: float = TRAIN_RATIO,
    lag_days: int = 7,
    use_weather: bool = True,
) -> Dict[str, Any]:
    """训练单个模型，返回指标与模型实例"""
    df = load_product_data(db, product_name, use_weather=use_weather)
    if len(df) < lag_days + 20:
        return {"error": "数据量不足"}
    X, y = prepare_xy(df, lag_days=lag_days, use_weather=use_weather)
    n = int(len(X) * train_ratio)
    X_train, X_test = X[:n], X[n:]
    y_train, y_test = y[:n], y[n:]
    if model_name not in MODEL_MAP:
        return {"error": f"未知模型 {model_name}"}
    try:
        cls = MODEL_MAP[model_name]
        if model_name == "ARIMA":
            predictor = cls().fit(None, y_train)
            f = predictor.model_.get_forecast(steps=len(y_test))
            y_pred = np.asarray(f.predicted_mean.values).flatten()
        else:
            predictor = cls().fit(X_train, y_train)
            y_pred = predictor.predict(X_test)
        # 保护：确保评价指标计算时 y_test 与 y_pred 长度一致
        min_len = min(len(y_test), len(y_pred))
        if min_len == 0:
            return {"error": "有效测试样本数量为 0，无法评估模型"}
        y_test_eval = y_test[:min_len]
        y_pred_eval = np.asarray(y_pred).reshape(-1)[:min_len]
        metrics = all_metrics(y_test_eval, y_pred_eval)
        return {
            "model_name": model_name,
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "mape": metrics["mape"],
            "predictor": predictor,
            "last_X": X[-1:] if model_name != "ARIMA" else None,
            "lag_days": lag_days,
        }
    except Exception as e:
        return {"error": str(e)}


def predict_future(
    predictor_result: Dict[str, Any],
    steps: int = 7,
) -> List[Dict[str, Any]]:
    """预测未来 steps 天，带 ±5% 置信区间"""
    preds = []
    predictor = predictor_result.get("predictor")
    model_name = predictor_result.get("model_name", "")
    if not predictor:
        return preds
    last_X = predictor_result.get("last_X")
    base_date = date.today()
    if model_name == "ARIMA":
        try:
            vals = predictor.predict(None, steps=steps)
            if not hasattr(vals, "__len__"):
                vals = [float(vals)]
            for i, v in enumerate(vals[:steps]):
                d = base_date + timedelta(days=i + 1)
                low = v * (1 - CONFIDENCE_PCT)
                high = v * (1 + CONFIDENCE_PCT)
                preds.append({"predict_date": d, "price_pred": round(float(v), 2), "confidence_low": round(low, 2), "confidence_high": round(high, 2)})
        except Exception:
            pass
    elif last_X is not None:
        try:
            X_step = last_X.copy()
            for step in range(steps):
                p = predictor.predict(X_step)[0]
                d = base_date + timedelta(days=step + 1)
                low = p * (1 - CONFIDENCE_PCT)
                high = p * (1 + CONFIDENCE_PCT)
                preds.append({"predict_date": d, "price_pred": round(float(p), 2), "confidence_low": round(low, 2), "confidence_high": round(high, 2)})
                # 滚动：新预测作为下一滞后
                if X_step.shape[1] >= 1:
                    X_step = np.column_stack([np.array([p]), X_step[:, :-1]])
        except Exception:
            pass
    return preds


DEFAULT_EVAL_MODE = "walk_forward"
ENSEMBLE_MODEL_NAME = "组合模型"
BASE_MODEL_MAP = {
    "ARIMA": ARIMAPredictor,
    "LSTM": LSTMPredictor,
    "SVR": SVRPredictor,
    "随机森林": RFPredictor,
}


def list_supported_models() -> List[str]:
    return list(BASE_MODEL_MAP.keys()) + [ENSEMBLE_MODEL_NAME]


def _fit_predictor(model_name: str, X_train: Optional[np.ndarray], y_train: np.ndarray):
    cls = BASE_MODEL_MAP[model_name]
    if model_name == "ARIMA":
        return cls().fit(None, y_train)
    return cls().fit(X_train, y_train)


def _predict_eval(model_name: str, predictor, X_test: Optional[np.ndarray], y_len: int) -> np.ndarray:
    if model_name == "ARIMA":
        f = predictor.model_.get_forecast(steps=y_len)
        return np.asarray(f.predicted_mean.values).flatten()
    return np.asarray(predictor.predict(X_test)).reshape(-1)


def _evaluate_holdout(model_name: str, X: np.ndarray, y: np.ndarray, train_ratio: float) -> Dict[str, Any]:
    if len(X) < 2:
        return {"error": f"有效样本不足，无法进行训练/测试划分 (len(X)={len(X)}, len(y)={len(y)})"}
    n = int(len(X) * train_ratio)
    n = max(1, min(len(X) - 1, n))
    if n <= 0 or n >= len(X):
        return {"error": f"训练/测试划分无效 (len(X)={len(X)}, len(y)={len(y)}, train_ratio={train_ratio}, split_index={n})"}
    X_train, X_test = X[:n], X[n:]
    y_train, y_test = y[:n], y[n:]
    predictor = _fit_predictor(model_name, X_train, y_train)
    y_pred = _predict_eval(model_name, predictor, X_test, len(y_test))
    min_len = min(len(y_test), len(y_pred))
    if min_len == 0:
        return {"error": "有效测试样本数量为 0，无法评估模型"}
    y_true_eval = y_test[:min_len]
    y_pred_eval = y_pred[:min_len]
    metrics = all_metrics(y_true_eval, y_pred_eval)
    return {
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "mape": metrics["mape"],
        "cv_std_mape": 0.0,
        "eval_y_true": y_true_eval.astype(np.float32),
        "eval_y_pred": y_pred_eval.astype(np.float32),
    }


def _evaluate_walk_forward(model_name: str, X: np.ndarray, y: np.ndarray, train_ratio: float, cv_folds: int) -> Dict[str, Any]:
    total = len(X)
    min_train = max(int(total * train_ratio), 20)
    if min_train >= total - 1:
        return _evaluate_holdout(model_name, X, y, train_ratio)
    available = total - min_train
    folds = max(2, min(int(cv_folds or CV_FOLDS), available))
    if folds < 2:
        return _evaluate_holdout(model_name, X, y, train_ratio)
    step = max(1, available // folds)
    y_true_parts: List[np.ndarray] = []
    y_pred_parts: List[np.ndarray] = []
    fold_mapes: List[float] = []
    for i in range(folds):
        start = min_train + i * step
        if start >= total:
            break
        end = total if i == folds - 1 else min(total, start + step)
        if end <= start:
            continue
        X_train, X_test = X[:start], X[start:end]
        y_train, y_test = y[:start], y[start:end]
        predictor = _fit_predictor(model_name, X_train, y_train)
        y_pred = _predict_eval(model_name, predictor, X_test, len(y_test))
        min_len = min(len(y_test), len(y_pred))
        if min_len == 0:
            continue
        y_fold = y_test[:min_len].astype(np.float32)
        p_fold = y_pred[:min_len].astype(np.float32)
        y_true_parts.append(y_fold)
        y_pred_parts.append(p_fold)
        fold_mapes.append(float(mape(y_fold, p_fold)))
    if not y_true_parts or not y_pred_parts:
        return _evaluate_holdout(model_name, X, y, train_ratio)
    y_true_eval = np.concatenate(y_true_parts)
    y_pred_eval = np.concatenate(y_pred_parts)
    metrics = all_metrics(y_true_eval, y_pred_eval)
    return {
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "mape": metrics["mape"],
        "cv_std_mape": float(np.std(fold_mapes)) if len(fold_mapes) > 1 else 0.0,
        "eval_y_true": y_true_eval.astype(np.float32),
        "eval_y_pred": y_pred_eval.astype(np.float32),
    }


def load_product_data(
    db: Session,
    product_name: str,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    use_weather: bool = True,
) -> pd.DataFrame:
    q = (
        db.query(PriceRecord.record_date, PriceRecord.price, PriceRecord.origin)
        .filter(PriceRecord.product_name == product_name)
        .order_by(PriceRecord.record_date)
    )
    if date_start:
        q = q.filter(PriceRecord.record_date >= date_start)
    if date_end:
        q = q.filter(PriceRecord.record_date <= date_end)
    rows = q.all()
    df = pd.DataFrame(rows, columns=["record_date", "price", "origin"])
    df["record_date"] = pd.to_datetime(df["record_date"])
    df["origin"] = df["origin"].astype(str).str.strip()
    df = df.groupby("record_date").agg({"price": "mean", "origin": "first"}).reset_index()
    if not use_weather or df.empty:
        return df
    wq = db.query(
        WeatherRecord.record_date,
        WeatherRecord.origin,
        WeatherRecord.temp_avg,
        WeatherRecord.precipitation,
        WeatherRecord.humidity_avg,
    )
    if date_start:
        wq = wq.filter(WeatherRecord.record_date >= date_start)
    if date_end:
        wq = wq.filter(WeatherRecord.record_date <= date_end)
    wrows = wq.all()
    wdf = pd.DataFrame(wrows, columns=["record_date", "origin", "temp_avg", "precipitation", "humidity_avg"])
    if wdf.empty:
        return df
    wdf["record_date"] = pd.to_datetime(wdf["record_date"])
    wdf["origin"] = wdf["origin"].astype(str).str.strip()
    weather_cols = ["temp_avg", "precipitation", "humidity_avg"]
    for c in weather_cols:
        if c in wdf.columns:
            wdf[c] = pd.to_numeric(wdf[c], errors="coerce")
    df["origin_key"] = df["origin"].str.replace(r"\s+", "", regex=True)
    wdf["origin_key"] = wdf["origin"].str.replace(r"\s+", "", regex=True)
    df = df.merge(
        wdf[["record_date", "origin_key", *weather_cols]],
        on=["record_date", "origin_key"],
        how="left",
    )
    daily_weather = wdf.groupby("record_date", as_index=False)[weather_cols].mean()
    daily_weather = daily_weather.rename(columns={c: f"{c}_by_date" for c in weather_cols})
    df = df.merge(daily_weather, on="record_date", how="left")
    for c in weather_cols:
        backup_col = f"{c}_by_date"
        if backup_col in df.columns:
            df[c] = df[c].where(df[c].notna(), df[backup_col])
            df.drop(columns=[backup_col], inplace=True)
    df.drop(columns=["origin_key"], inplace=True)
    return df


def prepare_xy_with_meta(df: pd.DataFrame, lag_days: int = 7, use_weather: bool = True) -> Dict[str, Any]:
    df = df.sort_values("record_date").dropna(subset=["price"]).reset_index(drop=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    feature_names = [f"lag_{i}" for i in range(1, lag_days + 1)]
    cols = [pd.to_numeric(df["price"].shift(i), errors="coerce") for i in range(1, lag_days + 1)]
    if use_weather and "temp_avg" in df.columns:
        df["temp_avg"] = pd.to_numeric(df["temp_avg"], errors="coerce").ffill().bfill().fillna(0)
        cols.append(df["temp_avg"].shift(1))
        feature_names.append("temp_avg_lag1")
    if use_weather and "precipitation" in df.columns:
        df["precipitation"] = pd.to_numeric(df["precipitation"], errors="coerce").fillna(0)
        cols.append(df["precipitation"].shift(1))
        feature_names.append("precipitation_lag1")
    X_df = pd.concat(cols, axis=1)
    X_df.columns = feature_names
    y_series = pd.to_numeric(df["price"], errors="coerce").rename("target")
    dataset = pd.concat([X_df, y_series], axis=1).dropna().reset_index(drop=True)
    if dataset.empty:
        return {
            "X": np.empty((0, len(feature_names)), dtype=np.float32),
            "y": np.empty((0,), dtype=np.float32),
            "feature_names": feature_names,
            "feature_df": pd.DataFrame(columns=feature_names),
        }
    X = dataset[feature_names].to_numpy(dtype=np.float32)
    y_final = dataset["target"].to_numpy(dtype=np.float32)
    return {
        "X": X,
        "y": y_final,
        "feature_names": feature_names,
        "feature_df": dataset[feature_names].copy(),
    }


def prepare_xy(df: pd.DataFrame, lag_days: int = 7, use_weather: bool = True) -> tuple[np.ndarray, np.ndarray]:
    meta = prepare_xy_with_meta(df, lag_days=lag_days, use_weather=use_weather)
    return meta["X"], meta["y"]


def train_and_evaluate(
    db: Session,
    product_name: str,
    model_name: str,
    train_ratio: float = TRAIN_RATIO,
    lag_days: int = 7,
    use_weather: bool = True,
    cv_folds: int = CV_FOLDS,
    eval_mode: str = DEFAULT_EVAL_MODE,
) -> Dict[str, Any]:
    df = load_product_data(db, product_name, use_weather=use_weather)
    if len(df) < lag_days + 20:
        return {"error": "数据量不足"}
    X, y = prepare_xy(df, lag_days=lag_days, use_weather=use_weather)
    if len(X) == 0 or len(y) == 0:
        return {"error": "特征构造后有效样本为 0，请检查天气数据或关闭天气特征"}
    if len(X) != len(y):
        return {"error": "特征与标签样本数量不一致"}
    if model_name not in BASE_MODEL_MAP:
        return {"error": f"未知模型 {model_name}"}
    try:
        mode = (eval_mode or DEFAULT_EVAL_MODE).lower()
        if mode == "holdout":
            eval_result = _evaluate_holdout(model_name, X, y, train_ratio)
        else:
            eval_result = _evaluate_walk_forward(model_name, X, y, train_ratio, cv_folds)
        if "error" in eval_result:
            return eval_result
        predictor = _fit_predictor(model_name, X, y)
        return {
            "model_name": model_name,
            "mae": eval_result["mae"],
            "rmse": eval_result["rmse"],
            "mape": eval_result["mape"],
            "cv_std_mape": eval_result.get("cv_std_mape", 0.0),
            "predictor": predictor,
            "last_X": X[-1:] if model_name != "ARIMA" else None,
            "lag_days": lag_days,
            "eval_y_true": eval_result.get("eval_y_true"),
            "eval_y_pred": eval_result.get("eval_y_pred"),
        }
    except Exception as e:
        return {"error": str(e)}


def _normalize_weights(raw: Dict[str, float]) -> Dict[str, float]:
    s = float(sum(max(v, 0.0) for v in raw.values()))
    if s <= 0:
        n = len(raw)
        return {k: (1.0 / n if n else 0.0) for k in raw}
    return {k: float(max(v, 0.0)) / s for k, v in raw.items()}


def train_and_evaluate_ensemble(
    db: Session,
    product_name: str,
    base_models: Optional[List[str]] = None,
    train_ratio: float = TRAIN_RATIO,
    lag_days: int = 7,
    use_weather: bool = True,
    cv_folds: int = CV_FOLDS,
    eval_mode: str = DEFAULT_EVAL_MODE,
) -> Dict[str, Any]:
    df = load_product_data(db, product_name, use_weather=use_weather)
    if len(df) < lag_days + 20:
        return {"error": "数据量不足"}
    candidates = [m for m in (base_models or list(BASE_MODEL_MAP.keys())) if m in BASE_MODEL_MAP and m != ENSEMBLE_MODEL_NAME]
    if not candidates:
        candidates = list(BASE_MODEL_MAP.keys())
    base_results: List[Dict[str, Any]] = []
    test_preds: Dict[str, np.ndarray] = {}
    test_truths: Dict[str, np.ndarray] = {}
    rmse_scores: Dict[str, float] = {}
    for model_name in candidates:
        res = train_and_evaluate(
            db,
            product_name,
            model_name,
            train_ratio=train_ratio,
            lag_days=lag_days,
            use_weather=use_weather,
            cv_folds=cv_folds,
            eval_mode=eval_mode,
        )
        if "error" in res:
            continue
        raw_pred = res.get("eval_y_pred")
        raw_true = res.get("eval_y_true")
        y_pred = np.asarray(raw_pred if raw_pred is not None else []).reshape(-1)
        y_true = np.asarray(raw_true if raw_true is not None else []).reshape(-1)
        min_len = min(len(y_true), len(y_pred))
        if min_len == 0:
            continue
        test_preds[model_name] = y_pred[:min_len]
        test_truths[model_name] = y_true[:min_len]
        rmse_scores[model_name] = float(res.get("rmse", 0.0))
        base_results.append(res)
    if not base_results or not test_preds or not test_truths:
        return {"error": "组合模型训练失败：可用基模型不足"}
    min_len_all = min(len(v) for v in test_preds.values())
    if min_len_all <= 0:
        return {"error": "组合模型训练失败：有效测试样本数量为 0"}
    inv = {m: 1.0 / (rmse_scores.get(m, 0.0) + 1e-8) for m in test_preds.keys()}
    weights = _normalize_weights(inv)
    y_ens = np.zeros((min_len_all,), dtype=np.float32)
    for m, pred in test_preds.items():
        y_ens += float(weights.get(m, 0.0)) * pred[:min_len_all].astype(np.float32)
    ref_truth = test_truths[next(iter(test_truths.keys()))][:min_len_all]
    metrics = all_metrics(ref_truth, y_ens)
    ape = np.abs((ref_truth - y_ens) / np.where(ref_truth == 0, 1e-8, ref_truth)) * 100.0
    return {
        "model_name": ENSEMBLE_MODEL_NAME,
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "mape": metrics["mape"],
        "cv_std_mape": float(np.std(ape)) if len(ape) > 1 else 0.0,
        "base_models": list(test_preds.keys()),
        "weights": weights,
        "base_results": base_results,
        "lag_days": lag_days,
        "eval_y_true": ref_truth.astype(np.float32),
        "eval_y_pred": y_ens.astype(np.float32),
    }


def predict_future_ensemble(ensemble_result: Dict[str, Any], steps: int = 7) -> List[Dict[str, Any]]:
    weights: Dict[str, float] = ensemble_result.get("weights") or {}
    base_results: List[Dict[str, Any]] = ensemble_result.get("base_results") or []
    by_model_preds: Dict[str, List[Dict[str, Any]]] = {}
    for br in base_results:
        m = br.get("model_name")
        if not m:
            continue
        by_model_preds[m] = predict_future(br, steps=steps)
    all_dates = []
    for preds in by_model_preds.values():
        for p in preds:
            d = p.get("predict_date")
            if d and d not in all_dates:
                all_dates.append(d)
    all_dates = sorted(all_dates)
    out: List[Dict[str, Any]] = []
    for d in all_dates[:steps]:
        vals: List[tuple[str, float, Optional[float], Optional[float]]] = []
        for m, preds in by_model_preds.items():
            hit = next((p for p in preds if p.get("predict_date") == d), None)
            if not hit:
                continue
            vals.append((m, float(hit["price_pred"]), hit.get("confidence_low"), hit.get("confidence_high")))
        if not vals:
            continue
        avail_w = _normalize_weights({m: float(weights.get(m, 0.0)) for m, *_ in vals})
        price = sum(avail_w[m] * v for m, v, *_ in vals)
        lows = [low for _, _, low, _ in vals if low is not None]
        highs = [high for _, _, _, high in vals if high is not None]
        low_val = None
        high_val = None
        if lows and highs:
            low_val = sum(avail_w[m] * float(low) for m, _, low, _ in vals if low is not None)
            high_val = sum(avail_w[m] * float(high) for m, _, _, high in vals if high is not None)
        out.append(
            {
                "predict_date": d,
                "price_pred": round(float(price), 2),
                "confidence_low": round(float(low_val), 2) if low_val is not None else None,
                "confidence_high": round(float(high_val), 2) if high_val is not None else None,
            }
        )
    return out


def predict_future(predictor_result: Dict[str, Any], steps: int = 7) -> List[Dict[str, Any]]:
    preds = []
    predictor = predictor_result.get("predictor")
    model_name = predictor_result.get("model_name", "")
    if not predictor:
        return preds
    last_X = predictor_result.get("last_X")
    base_date = date.today()
    if model_name == "ARIMA":
        try:
            vals = predictor.predict(None, steps=steps)
            if not hasattr(vals, "__len__"):
                vals = [float(vals)]
            for i, v in enumerate(vals[:steps]):
                d = base_date + timedelta(days=i + 1)
                low = v * (1 - CONFIDENCE_PCT)
                high = v * (1 + CONFIDENCE_PCT)
                preds.append({"predict_date": d, "price_pred": round(float(v), 2), "confidence_low": round(low, 2), "confidence_high": round(high, 2)})
        except Exception:
            pass
    elif last_X is not None:
        try:
            X_step = last_X.copy()
            for step in range(steps):
                p = predictor.predict(X_step)[0]
                d = base_date + timedelta(days=step + 1)
                low = p * (1 - CONFIDENCE_PCT)
                high = p * (1 + CONFIDENCE_PCT)
                preds.append({"predict_date": d, "price_pred": round(float(p), 2), "confidence_low": round(low, 2), "confidence_high": round(high, 2)})
                if X_step.shape[1] >= 1:
                    X_step = np.column_stack([np.array([p]), X_step[:, :-1]])
        except Exception:
            pass
    return preds
