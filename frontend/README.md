# 农产品价格分析与预测系统 - 前端

Vue 3 + TypeScript + Vite + ECharts 5，与后端 API 配套使用。

## 技术栈

- **Vue 3**（Composition API + script setup）
- **Vite 5**
- **Vue Router 4**
- **Pinia**
- **Axios**
- **ECharts 5**（折线图、热力图、柱状图）
- **dayjs**（可选）

## 环境

- Node 18+
- 后端服务运行在 `http://localhost:8000`（或通过代理）

## 安装与运行

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173 。  
构建：`npm run build`，预览：`npm run preview`。

## 环境变量

在项目根目录创建 `.env`（可选）：

```env
VITE_API_BASE=http://localhost:8000
```

不设置时，开发环境通过 Vite 代理将 `/api` 转发到 `http://localhost:8000`。

## 功能模块

| 路由     | 说明 |
|----------|------|
| /login   | 登录 |
| /register| 注册（角色：学生/农户/经销商/监管部门） |
| /        | 仪表盘：当日白菜/土豆价格、TOP3 模型、未读预警数 |
| /data    | 数据管理：Excel 导入价格/天气、导出、价格列表查询 |
| /analysis| 价格分析：时间序列折线图、相关性热力图、产品对比柱状图 |
| /predict | 预测：模型训练与 MAE/RMSE/MAPE 对比、短期 1/3/7 天预测及置信区间 |
| /alerts  | 异常预警列表、标记已读 |

## 与后端对接

- 所有接口以 `/api` 为前缀，需先登录获取 JWT，请求头携带 `Authorization: Bearer <token>`。
- 数据管理中的「导出」为 GET 链接，若后端对导出接口做了鉴权，需在链接上带 token 或改用前端请求 blob 再下载。
