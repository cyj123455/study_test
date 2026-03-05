"""预测结果与模型运行记录 - PRD 模型输出数据"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


# 所属模型枚举
MODEL_NAMES = ("ARIMA", "LSTM", "SVR", "随机森林")


class PredictionRecord(Base):
    """单条预测结果"""
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(32), nullable=False, index=True)   # 预测农产品
    predict_date = Column(Date, nullable=False, index=True)         # 预测日期
    price_pred = Column(Numeric(10, 2), nullable=False)              # 预测价格
    confidence_low = Column(Numeric(10, 2), nullable=True)           # 置信区间下限
    confidence_high = Column(Numeric(10, 2), nullable=True)          # 置信区间上限
    model_name = Column(String(32), nullable=False, index=True)     # ARIMA/LSTM/SVR/随机森林
    run_id = Column(Integer, nullable=True, index=True)             # 关联 ModelRun
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelRun(Base):
    """一次模型训练/评估运行"""
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(32), nullable=False, index=True)
    model_name = Column(String(32), nullable=False, index=True)
    mae = Column(Numeric(10, 4), nullable=True)
    rmse = Column(Numeric(10, 4), nullable=True)
    mape = Column(Numeric(8, 2), nullable=True)   # 百分比
    params = Column(Text, nullable=True)         # 超参数 JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
