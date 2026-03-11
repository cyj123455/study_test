"""后端离线训练脚本：训练模型并将结果写入 model_runs"""
import sys
from pathlib import Path
from argparse import ArgumentParser
from decimal import Decimal
from typing import List
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import ModelRun
from app.services.ml_service import (
    PRODUCT_NAMES,
    BASE_MODEL_MAP,
    ENSEMBLE_MODEL_NAME,
    load_product_data,
    prepare_xy_with_meta,
    train_and_evaluate,
    train_and_evaluate_ensemble,
)


def _parse_list(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="后端离线训练并保存训练结果")
    parser.add_argument("--products", type=str, default=",".join(PRODUCT_NAMES), help="农产品列表，逗号分隔")
    parser.add_argument("--models", type=str, default="ARIMA,LSTM,SVR,随机森林,组合模型", help="模型列表，逗号分隔")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="训练集占比")
    parser.add_argument("--cv-folds", type=int, default=5, help="交叉验证折数")
    parser.add_argument("--eval-mode", type=str, default="walk_forward", choices=["walk_forward", "holdout"], help="评估方式")
    parser.add_argument("--check-overfit", action="store_true", default=False, help="输出 walk_forward 与 holdout 差值")
    parser.add_argument("--use-weather", action="store_true", default=True, help="使用天气特征")
    parser.add_argument("--no-weather", action="store_false", dest="use_weather", help="不使用天气特征")
    return parser


def print_weather_diagnostics(db, product_name: str, use_weather: bool) -> None:
    df = load_product_data(db, product_name, use_weather=use_weather)
    if df.empty:
        print("[诊断] 数据为空")
        return
    print(f"[诊断] 原始样本行数: {len(df)}")
    if not use_weather:
        print("[诊断] 当前未启用天气特征")
        return
    for col in ("temp_avg", "precipitation"):
        if col not in df.columns:
            print(f"[诊断] 缺少天气列: {col}")
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        non_null = int(series.notna().sum())
        null_ratio = float(1.0 - non_null / len(series))
        processed = series.copy()
        if col == "temp_avg":
            processed = processed.ffill().bfill().fillna(0)
        else:
            processed = processed.fillna(0)
        zero_ratio = float((processed == 0).mean())
        print(
            f"[诊断] {col}: 非空 {non_null}/{len(series)}, 缺失率 {null_ratio:.2%}, "
            f"填充后0值占比 {zero_ratio:.2%}"
        )


def print_feature_diagnostics(db, product_name: str, use_weather: bool) -> None:
    df = load_product_data(db, product_name, use_weather=use_weather)
    meta = prepare_xy_with_meta(df, lag_days=7, use_weather=use_weather)
    X = meta["X"]
    y = meta["y"]
    feature_names = meta["feature_names"]
    feature_df = meta["feature_df"]
    print(f"[诊断] use_weather={use_weather}, 有效样本={len(X)}, 特征维度={X.shape[1] if len(X) else 0}")
    weather_features = [f for f in ("temp_avg_lag1", "precipitation_lag1") if f in feature_names]
    if not weather_features:
        print("[诊断] 特征中未包含天气列")
        return
    for name in weather_features:
        col = pd.to_numeric(feature_df[name], errors="coerce")
        non_zero_ratio = float((col != 0).mean()) if len(col) else 0.0
        std_val = float(col.std()) if len(col) else 0.0
        corr = 0.0
        if len(col) and std_val > 1e-12 and np.std(y) > 1e-12:
            corr = float(np.corrcoef(col.to_numpy(dtype=np.float32), y)[0, 1])
        print(
            f"[诊断] {name}: 非零占比 {non_zero_ratio:.2%}, 标准差 {std_val:.4f}, "
            f"与目标相关系数 {corr:.4f}, 样例值 {col.head(5).round(4).tolist()}"
        )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    products = _parse_list(args.products)
    models = _parse_list(args.models)
    valid_models = [m for m in models if m in BASE_MODEL_MAP or m == ENSEMBLE_MODEL_NAME]
    if not products:
        raise SystemExit("未提供有效 products")
    if not valid_models:
        raise SystemExit("未提供有效 models")

    base_models = [m for m in valid_models if m in BASE_MODEL_MAP]
    total = 0
    success = 0

    with SessionLocal() as db:
        print(f"[配置] use_weather={args.use_weather}, eval_mode={args.eval_mode}, cv_folds={args.cv_folds}, train_ratio={args.train_ratio}")
        for product in products:
            print(f"\n========== 训练农产品: {product} ==========")
            print_weather_diagnostics(db, product, args.use_weather)
            print_feature_diagnostics(db, product, args.use_weather)
            for model_name in valid_models:
                total += 1
                try:
                    if model_name == ENSEMBLE_MODEL_NAME:
                        res = train_and_evaluate_ensemble(
                            db=db,
                            product_name=product,
                            base_models=base_models if base_models else None,
                            train_ratio=args.train_ratio,
                            use_weather=args.use_weather,
                            cv_folds=args.cv_folds,
                            eval_mode=args.eval_mode,
                        )
                    else:
                        res = train_and_evaluate(
                            db=db,
                            product_name=product,
                            model_name=model_name,
                            train_ratio=args.train_ratio,
                            use_weather=args.use_weather,
                            cv_folds=args.cv_folds,
                            eval_mode=args.eval_mode,
                        )
                    if "error" in res:
                        print(f"[失败] {product} - {model_name}: {res['error']}")
                        continue

                    mr = ModelRun(
                        product_name=product,
                        model_name=model_name,
                        mae=Decimal(str(res["mae"])),
                        rmse=Decimal(str(res["rmse"])),
                        mape=Decimal(str(res["mape"])),
                    )
                    db.add(mr)
                    db.commit()
                    success += 1
                    print(
                        f"[成功] {product} - {model_name}: "
                        f"MAE={res['mae']:.4f}, RMSE={res['rmse']:.4f}, MAPE={res['mape']:.2f}"
                    )
                    if args.check_overfit and args.eval_mode == "walk_forward":
                        if model_name == ENSEMBLE_MODEL_NAME:
                            holdout_res = train_and_evaluate_ensemble(
                                db=db,
                                product_name=product,
                                base_models=base_models if base_models else None,
                                train_ratio=args.train_ratio,
                                use_weather=args.use_weather,
                                cv_folds=args.cv_folds,
                                eval_mode="holdout",
                            )
                        else:
                            holdout_res = train_and_evaluate(
                                db=db,
                                product_name=product,
                                model_name=model_name,
                                train_ratio=args.train_ratio,
                                use_weather=args.use_weather,
                                cv_folds=args.cv_folds,
                                eval_mode="holdout",
                            )
                        if "error" not in holdout_res:
                            gap = float(holdout_res["mape"]) - float(res["mape"])
                            print(
                                f"[过拟合检查] {product} - {model_name}: "
                                f"walk_forward MAPE={res['mape']:.2f}, holdout MAPE={holdout_res['mape']:.2f}, 差值={gap:.2f}"
                            )
                except Exception as exc:
                    db.rollback()
                    print(f"[异常] {product} - {model_name}: {exc}")

    print(f"\n训练完成：成功 {success}/{total}")


if __name__ == "__main__":
    main()
