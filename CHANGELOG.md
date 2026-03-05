# 变更日志 (Changelog)

本文件记录项目的所有重要变更。

## [1.0.0] - 2026-03-05

### 新增 (Added)
- 初始版本发布
- 农产品价格分析与预测系统
- 后端 API（FastAPI）
  - 用户认证与授权
  - 价格数据管理
  - 数据分析与可视化
  - 价格预测功能（ARIMA, LSTM, 机器学习模型）
  - 天气数据分析
  - 预警系统
- 前端界面（Vue 3 + TypeScript）
  - 登录/注册页面
  - 数据看板
  - 数据分析
  - 价格预测
  - 预警管理
  - 数据管理
- 机器学习模型
  - ARIMA 时间序列模型
  - LSTM 深度学习模型
  - Scikit-learn 机器学习模型
- 数据爬虫服务
- 自动化定时任务

### 技术栈 (Tech Stack)
- **后端**: FastAPI, SQLAlchemy, Pandas, NumPy, Scikit-learn, TensorFlow, Statsmodels
- **前端**: Vue 3, TypeScript, Pinia, Vue Router, Axios, ECharts
- **数据库**: MySQL / PostgreSQL
- **工具**: Vite, Python-dotenv, ReportLab

---

## 格式说明 (Format Guide)

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范。

### 版本标识说明
- `Added`：新增功能
- `Changed`：对现有功能的变更
- `Deprecated`：即将移除的功能
- `Removed`：已移除的功能
- `Fixed`：修复的 bug
- `Security`：安全性修复

### 版本号规则 (Versioning)
采用语义化版本号：`主版本号。次版本号.修订号`（MAJOR.MINOR.PATCH）
- MAJOR：不兼容的 API 变更
- MINOR：向后兼容的功能性新增
- PATCH：向后兼容的问题修正
