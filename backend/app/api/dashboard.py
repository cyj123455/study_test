"""综合仪表盘：当日价格、预测准确率 TOP3、异常预警条数"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from datetime import date
from sqlalchemy import func, desc
from datetime import date
from sqlalchemy import nulls_last, asc
from app.database import get_db
from app.models.price import PriceRecord
from app.models.prediction import ModelRun
from app.models.alert import AlertRecord

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("")
def dashboard(db: Session = Depends(get_db)):
    today = date.today()
    # 当日白菜/土豆价格（各取一条或均价）
    price_cabbage = db.query(func.avg(PriceRecord.price)).filter(
        PriceRecord.product_name.in_(["矮脚白菜", "本地白菜", "小塘白菜"]),
        PriceRecord.record_date == today,
    ).scalar()
    price_potato = db.query(func.avg(PriceRecord.price)).filter(
        PriceRecord.product_name == "土豆",
        PriceRecord.record_date == today,
    ).scalar()
    # 预测准确率 TOP3（按 MAPE 升序）
    top_models = (
        db.query(ModelRun)
        # .order_by(nulls_last(asc(ModelRun.mape)))
        .order_by(
            case((ModelRun.mape.is_(None), 1), else_=0),  # NULL值排在最后
            ModelRun.mape.asc()  # 非NULL值按升序排列
        )
        .limit(3)
        .all()
    )
    # 未读预警条数
    alert_count = db.query(func.count(AlertRecord.id)).filter(AlertRecord.is_read == 0).scalar() or 0
    return {
        "today_cabbage_price": float(price_cabbage) if price_cabbage is not None else None,
        "today_potato_price": float(price_potato) if price_potato is not None else None,
        "top3_models": [
            {"product_name": m.product_name, "model_name": m.model_name, "mape": float(m.mape) if m.mape else None}
            for m in top_models
        ],
        "alert_unread_count": alert_count,
    }
