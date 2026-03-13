# 《BetterPrompt Sprint 1 实施任务单 v1》

## 1. Sprint 目标

本 Sprint 的目标不是完成完整产品，而是完成 **工程可运行 + 最小联调可行 + 后续开发底座搭建完成**。

Sprint 1 结束时，项目应满足：

- **前端可启动**
- **后端可启动**
- **数据库可连接**
- **健康检查接口可访问**
- **前后端可完成最小联调**
- **工程结构与基础规范收口完成**

## 2. Sprint 范围

本 Sprint 只覆盖以下范围：

- 工程骨架补齐
- 基础目录结构搭建
- 后端 FastAPI app 启动
- 前端 Vite app 启动
- PostgreSQL 基础接入
- 最小数据模型落地
- 健康检查与基础错误结构
- API 基础联调准备

本 Sprint 不覆盖：

- 完整 LLM 能力上线
- 用户系统正式完成
- 历史记录页面
- 资产沉淀页面
- 模板系统
- 计费与额度

## 3. Sprint 成功标准

满足以下条件即视为 Sprint 完成：

- **后端**
  - 可以启动 FastAPI 服务
  - `/api/v1/health` 正常返回
  - 数据库连接成功
  - migration 可以执行

- **前端**
  - 可以启动 Vite dev server
  - 能访问工作台基础页面
  - 能调用健康检查接口或最小 mock 接口

- **工程层**
  - 目录结构与蓝图一致
  - 环境变量模板存在
  - README 或启动说明存在

## 4. 任务拆解

### A. 仓库与工程骨架

#### A1. 前端工程初始化

- 创建 `frontend/package.json`
- 创建 `frontend/tsconfig.json`
- 创建 `frontend/vite.config.ts`
- 创建 `frontend/index.html`
- 建立 `frontend/src/app` 基础入口
- 建立 `frontend/src/shared/api/client.ts`

**交付物**

- 可启动的 Vite + React + TypeScript 工程

**验收标准**

- `frontend` 可本地启动

#### A2. 后端工程初始化

- 创建 `backend/pyproject.toml`
- 创建 `backend/app/main.py`
- 创建 `backend/app/core/config.py`
- 创建 `backend/app/api/deps.py`
- 创建 `backend/app/api/routers/health.py`
- 创建 `backend/app/core/errors.py`

**交付物**

- 可启动的 FastAPI 工程

**验收标准**

- `backend` 可本地启动
- `/api/v1/health` 可访问

### B. 数据库基础能力

#### B1. DB 基础接入

- 创建 `backend/app/db/base.py`
- 创建 `backend/app/db/session.py`
- 配置 `DATABASE_URL`
- 初始化 Alembic

**交付物**

- 可连接 PostgreSQL 的后端工程

#### B2. 第一批表结构

优先建立：

- `users`
- `prompt_sessions`
- `prompt_iterations`

**交付物**

- 第一版 migration
- ORM 模型初版

**验收标准**

- migration 可执行成功

### C. 前端工作台基础壳

#### C1. 页面与路由

- 建立 `workbench` 页面
- 建立 `App.tsx`
- 建立 `router.tsx`
- 建立基础布局与占位组件

#### C2. 基础 API 接线

- 建立统一 `api client`
- 接入健康检查请求
- 建立基础错误处理

**验收标准**

- 页面可访问
- 可成功请求后端健康检查

### D. 规范与启动文档

#### D1. 环境变量模板

- 根目录 `.env.example`
- 前端 `.env.example`
- 后端 `.env.example`

#### D2. 启动说明

- 补充 README 或 `docs/plans` 中的启动说明文档

## 5. 建议交付顺序

建议按顺序执行：

1. 后端工程初始化
2. 前端工程初始化
3. DB 接入与 migration
4. 健康检查接口
5. 前端工作台基础壳
6. 前后端联调
7. 文档补齐

## 6. 角色分工建议

### 前端

- 初始化 Vite 工程
- 接入工作台壳
- 建立 API client
- 验证联调

### 后端

- 初始化 FastAPI 工程
- 接入 DB
- 建立 health router
- 建立基础 migration

### 架构 / 产品化负责人

- 对齐目录结构
- 对齐环境变量命名
- 对齐 API path 规范
- 维护 Sprint 边界

## 7. 风险与注意事项

- 不要在 Sprint 1 就把 Generate/Debug/Evaluate 做完整
- 不要继续沿用当前残缺子项目结构做拼补
- 不要过早引入过多 provider 抽象
- 不要在没有 migration 的情况下直接硬写数据库逻辑

## 8. Sprint 1 结束产物清单

- `frontend/` 可运行工程
- `backend/` 可运行工程
- 第一版 DB migration
- `/api/v1/health` 接口
- 工作台基础页面壳
- 环境变量模板
- 启动说明文档

## 9. 完成定义

当以下全部满足时，Sprint 1 可关闭：

- 工程可启动
- 健康检查可访问
- 数据库可连接
- migration 可运行
- 前后端可联调
- 文档足够支撑 Sprint 2 开始
