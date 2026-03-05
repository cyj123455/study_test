"""异常预警：价格异常检测、涨幅跌幅 - PRD 3.4"""
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.price import PriceRecord
from app.models.weather import WeatherRecord
from app.models.alert import AlertRecord
from app.config import get_settings

settings = get_settings()
RISE_PCT = settings.ALERT_RISE_PCT   # 单日涨幅≥20%
DROP_PCT = settings.ALERT_DROP_PCT   # 单日跌幅≥15%
STD_MULT = settings.OUTLIER_STD_MULTIPLIER


def _price_stats(db: Session, product_name: str, before_date: date) -> tuple[float, float]:
    """某产品在 before_date 之前的均价与标准差"""
    sub = (
        db.query(func.avg(PriceRecord.price), func.stddev(PriceRecord.price))
        .filter(PriceRecord.product_name == product_name, PriceRecord.record_date < before_date)
        .first()
    )
    if not sub or sub[1] is None:
        return 0.0, 0.0
    return float(sub[0]), float(sub[1])


def check_out_of_range(
    db: Session,
    product_name: str,
    record_date: date,
    price: float,
) -> tuple[bool, str]:
    """是否超出正常区间（均值±3倍标准差），返回 (是否异常, 原因描述)"""
    mean_p, std_p = _price_stats(db, product_name, record_date)
    if std_p == 0:
        return False, ""
    low, high = mean_p - STD_MULT * std_p, mean_p + STD_MULT * std_p
    if price < low or price > high:
        return True, f"价格 {price} 超出历史正常区间 [{low:.2f}, {high:.2f}]（均值±{STD_MULT}倍标准差）"
    return False, ""


def check_daily_change(
    db: Session,
    product_name: str,
    record_date: date,
    price: float,
) -> tuple[bool, str]:
    """是否异常涨幅/跌幅"""
    prev_date = record_date - timedelta(days=1)
    prev = (
        db.query(PriceRecord.price)
        .filter(
            PriceRecord.product_name == product_name,
            PriceRecord.record_date == prev_date,
        )
        .first()
    )
    if not prev or prev[0] is None:
        return False, ""
    prev_p = float(prev[0])
    if prev_p == 0:
        return False, ""
    pct = (price - prev_p) / prev_p * 100
    if pct >= RISE_PCT:
        return True, f"单日涨幅 {pct:.1f}% ≥ {RISE_PCT}%"
    if pct <= -DROP_PCT:
        return True, f"单日跌幅 {-pct:.1f}% ≥ {DROP_PCT}%"
    return False, ""


def _get_weather_reason(db: Session, origin: str, d: date) -> str:
    """关联产区天气，用于预警原因"""
    w = (
        db.query(WeatherRecord.extreme_weather)
        .filter(WeatherRecord.origin == origin, WeatherRecord.record_date == d)
        .first()
    )
    if w and w[0] and w[0] != "无极端天气":
        return f"，关联产区{w[0]}天气"
    return ""


def run_alert_check(db: Session, product_name: str, record_date: date, price: float, origin: str | None = None) -> list[AlertRecord]:
    """执行检测并写入预警记录，返回本次新增的预警列表"""
    added = []
    # 1) 超出区间
    is_out, reason = check_out_of_range(db, product_name, record_date, price)
    if is_out:
        reason += _get_weather_reason(db, origin or "", record_date)
        alert = AlertRecord(
            product_name=product_name,
            record_date=record_date,
            price=Decimal(str(round(price, 2))),
            alert_type="超出区间",
            reason=reason,
        )
        db.add(alert)
        added.append(alert)
    # 2) 涨跌幅
    is_change, reason2 = check_daily_change(db, product_name, record_date, price)
    if is_change:
        reason2 += _get_weather_reason(db, origin or "", record_date)
        alert2 = AlertRecord(
            product_name=product_name,
            record_date=record_date,
            price=Decimal(str(round(price, 2))),
            alert_type="异常涨跌",
            reason=reason2,
        )
        db.add(alert2)
        added.append(alert2)
    db.commit()
    for a in added:
        db.refresh(a)
    return added


def list_alerts(
    db: Session,
    product_name: str | None = None,
    is_read: int | None = None,
    limit: int = 50,
) -> list[AlertRecord]:
    """查询预警列表"""
    q = db.query(AlertRecord).order_by(AlertRecord.created_at.desc())
    if product_name:
        q = q.filter(AlertRecord.product_name == product_name)
    if is_read is not None:
        q = q.filter(AlertRecord.is_read == is_read)
    return q.limit(limit).all()
