"""基于机器学习的农产品价格分析与预测系统 - FastAPI 主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import auth, data, analysis, predict, alerts, dashboard

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, description="农产品价格分析、短期预测与异常预警")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "农产品价格分析与预测系统 API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
