# 农产品价格分析与预测系统 - 后端

基于 PRD 的 FastAPI 后端，提供数据管理、价格分析、机器学习预测与异常预警 API。

## 技术栈

- **框架**: FastAPI
- **数据库**: MySQL 8.0+（SQLAlchemy ORM）
- **机器学习**: statsmodels (ARIMA)、TensorFlow (LSTM)、scikit-learn (SVR、随机森林)
- **数据**: Pandas、openpyxl（Excel 导入导出）

## 环境准备

1. Python 3.10+
2. MySQL 8.0+，创建数据库：`CREATE DATABASE agri_price_db;`
3. 复制 `.env.example` 为 `.env`，填写数据库与 `SECRET_KEY`

## 安装与运行

```bash
cd backend
pip install -r requirements.txt
python scripts/init_db.py   # 初始化表结构
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：http://localhost:8000/docs

## 主要接口

| 模块     | 路径前缀     | 说明 |
|----------|--------------|------|
| 认证     | `/api/auth`  | 注册、登录（JWT） |
| 数据管理 | `/api/data`  | 价格/天气 CRUD、Excel 导入、爬虫触发、导出 |
| 价格分析 | `/api/analysis` | 时间序列、相关性热力图、产品对比 |
| 预测     | `/api/predict`  | 模型训练、短期预测（1/3/7 天）、模型列表 |
| 预警     | `/api/alerts`   | 预警列表、标记已读 |
| 仪表盘   | `/api/dashboard` | 当日价格、TOP3 模型、未读预警数 |

## 数据与模型说明

- **产品**: 矮脚白菜、本地白菜、小塘白菜、土豆
- **模型**: ARIMA、LSTM、SVR、随机森林；评估指标 MAE、RMSE、MAPE；预测置信区间 ±5%
- **预警**: 均值±3 倍标准差、单日涨幅≥20%、跌幅≥15%

爬虫模块（`app/services/crawler.py`）为占位实现，需按蔬菜网、中国天气网实际页面或接口补充抓取逻辑。
