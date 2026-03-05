"""异常预警：列表、已读"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.alert import AlertResponse
from app.services.alert_service import list_alerts
from app.services.auth import get_current_user
from app.models.user import User
from app.models.alert import AlertRecord

router = APIRouter(prefix="/alerts", tags=["异常预警"])


@router.get("", response_model=list[AlertResponse])
def get_alerts(
    product_name: Optional[str] = None,
    is_read: Optional[int] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """预警列表"""
    return list_alerts(db, product_name=product_name, is_read=is_read, limit=limit)


@router.patch("/{alert_id}/read")
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记已读"""
    a = db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()
    if not a:
        return {"ok": False, "detail": "未找到"}
    a.is_read = 1
    db.commit()
    return {"ok": True}
