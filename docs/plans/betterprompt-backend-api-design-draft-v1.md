# 《BetterPrompt 后端 API 设计草案 v1》

## 1. 文档目标

本文定义 `BetterPrompt` 面向产品化后的后端 API 设计草案，目标是为后端工程启动、前后端联调和 session 资源化重构提供实现依据。

## 2. 设计原则

- **资源优先**
- **会话驱动**
- **统一响应结构**
- **错误码统一**
- **为历史、版本、资产留扩展空间**

## 3. 通用约定

### Base Path

```text
/api/v1
```

### Content-Type

```text
application/json
```

### 成功响应

```json
{
  "success": true,
  "data": {}
}
```

### 失败响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "request_id": "optional-request-id"
  }
}
```

## 4. 健康检查 API

### `GET /api/v1/health`

#### 用途

验证后端服务可用性。

#### 成功响应示例

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "betterprompt-backend",
    "version": "v1"
  }
}
```

## 5. Prompt Sessions API

### 5.1 创建会话

#### `POST /api/v1/prompt-sessions`

#### Request Body

```json
{
  "title": "架构分析 Prompt",
  "entry_mode": "generate",
  "source_template_id": null,
  "metadata": {}
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": "session_uuid",
    "title": "架构分析 Prompt",
    "entry_mode": "generate",
    "status": "active",
    "created_at": "2026-03-10T00:00:00Z"
  }
}
```

### 5.2 获取会话列表

#### `GET /api/v1/prompt-sessions`

支持查询参数：

- `page`
- `page_size`
- `mode`
- `q`

### 5.3 获取会话详情

#### `GET /api/v1/prompt-sessions/{session_id}`

返回：

- session 基本信息
- latest iteration
- iteration 列表摘要

## 6. Session 内操作 API

### 6.1 Generate

#### `POST /api/v1/prompt-sessions/{session_id}/generate`

#### Request Body

```json
{
  "user_input": "帮我生成一个复杂架构分析用的系统提示词",
  "show_diagnosis": true,
  "output_preference": "depth",
  "artifact_type": "system_prompt",
  "prompt_only": false,
  "context_notes": "用于代码审计"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "iteration_id": "iteration_uuid",
    "mode": "generate",
    "diagnosis": {
      "task_type": "architecture_spec",
      "output_type": "system_prompt",
      "quality_target": "depth",
      "failure_modes": ["surface_restatement", "pseudo_depth"]
    },
    "final_prompt": "...",
    "artifact_type": "system_prompt",
    "applied_modules": ["problem_redefinition", "cognitive_drill_down"],
    "optimization_strategy": "default_ultimate_template_v1",
    "optimized_input": "...",
    "prompt_only": false,
    "diagnosis_visible": true,
    "created_at": "2026-03-10T00:00:00Z"
  }
}
```

### 6.2 Debug

#### `POST /api/v1/prompt-sessions/{session_id}/debug`

#### Request Body

```json
{
  "original_task": "分析项目架构",
  "current_prompt": "...",
  "current_output": "...",
  "output_preference": "balanced"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "iteration_id": "iteration_uuid",
    "mode": "debug",
    "strengths": ["Prompt 已包含角色定位"],
    "weaknesses": ["缺少前提、边界或失效条件说明"],
    "top_failure_mode": "not_executable",
    "missing_control_layers": ["boundary_validation", "executability"],
    "minimal_fix": ["补充前提、边界与验证条件"],
    "fixed_prompt": "...",
    "created_at": "2026-03-10T00:00:00Z"
  }
}
```

### 6.3 Evaluate

#### `POST /api/v1/prompt-sessions/{session_id}/evaluate`

#### Request Body

```json
{
  "target_text": "...",
  "target_type": "prompt"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "iteration_id": "iteration_uuid",
    "mode": "evaluate",
    "score_breakdown": {
      "problem_fit": 4,
      "constraint_awareness": 3,
      "information_density": 4,
      "judgment_strength": 3,
      "executability": 2,
      "natural_style": 4,
      "overall_stability": 3
    },
    "total_score": 23,
    "top_issue": "缺少可执行步骤、验证方式或成功标准",
    "suggested_fix_layer": "executability",
    "created_at": "2026-03-10T00:00:00Z"
  }
}
```

### 6.4 Continue

#### `POST /api/v1/prompt-sessions/{session_id}/continue`

#### Request Body

```json
{
  "parent_iteration_id": "iteration_uuid",
  "previous_result": "...",
  "optimization_goal": "再提高可执行性",
  "mode": "generate"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "iteration_id": "iteration_uuid_new",
    "mode": "continue",
    "source_mode": "generate",
    "optimization_goal": "再提高可执行性",
    "refined_result": "...",
    "result_label": "优化后版本",
    "suggested_next_actions": ["再增强深度", "改成更自然的表达风格"],
    "created_at": "2026-03-10T00:00:00Z"
  }
}
```

## 7. Prompt Assets API

### 7.1 从 iteration 保存为 asset

#### `POST /api/v1/prompt-assets`

#### Request Body

```json
{
  "source_iteration_id": "iteration_uuid",
  "name": "复杂架构分析系统提示词",
  "description": "用于架构审计与代码库分析",
  "artifact_type": "system_prompt",
  "content": "..."
}
```

### 7.2 获取资产列表

#### `GET /api/v1/prompt-assets`

### 7.3 获取资产详情

#### `GET /api/v1/prompt-assets/{asset_id}`

### 7.4 新建资产版本

#### `POST /api/v1/prompt-assets/{asset_id}/versions`

## 8. Templates API

### v1 可预留，不要求 Sprint 1 落地

- `GET /api/v1/templates`
- `POST /api/v1/templates`
- `GET /api/v1/templates/{template_id}`
- `POST /api/v1/templates/{template_id}/versions`

## 9. 错误码草案

建议至少定义：

- `VALIDATION_ERROR`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `NOT_FOUND`
- `RATE_LIMITED`
- `PROVIDER_TIMEOUT`
- `PROVIDER_ERROR`
- `MODEL_OUTPUT_INVALID`
- `DATABASE_ERROR`
- `INTERNAL_SERVER_ERROR`

## 10. 与数据库的映射建议

- `POST /prompt-sessions`
  - 创建 `prompt_sessions`

- `POST /prompt-sessions/{id}/generate|debug|evaluate|continue`
  - 创建 `prompt_iterations`
  - 更新 `prompt_sessions.latest_iteration_id`
  - 记录 `usage_records`

- `POST /prompt-assets`
  - 创建 `prompt_assets`
  - 创建 `prompt_asset_versions`

## 11. Sprint 1 推荐落地范围

Sprint 1 只强制实现：

- `GET /api/v1/health`
- `POST /api/v1/prompt-sessions`
- `GET /api/v1/prompt-sessions/{id}`
- Session schema 基础定义
- 统一 response envelope
- 统一 error shape

Generate/Debug/Evaluate/Continue 可以先完成 schema 和接口占位，再在 Sprint 2 接真实逻辑。

## 12. 最终结论

v1 后端 API 的核心不是继续维持孤立的 `/prompt-agent/*` 功能接口，而是以 **`prompt_sessions` 为核心资源**，用 `iteration` 承载每一次生成、调试、评估和继续优化操作，从而支撑历史、版本、资产沉淀和后续商业化扩展。 “}}]}{Jsiifunctions.write_to_file.commentary to=file:///Users/smy/project/better-prompt/docs/plans/betterprompt-sprint-1-execution-plan-v1.md code_content= # 《BetterPrompt Sprint 1 实施任务单 v1》  ## 1. Sprint 目标  本 Sprint 的目标不是完成完整产品，而是完成 **工程可运行 + 最小联调可行 + 后续开发底座搭建完成**。  Sprint 1 结束时，项目应满足：  - **前端可启动** - **后端可启动** - **数据库可连接** - **健康检查接口可访问** - **前后端可完成最小联调** - **工程结构与基础规范收口完成**  ## 2. Sprint 范围  本 Sprint 只覆盖以下范围：  - 工程骨架补齐 - 基础目录结构搭建 - 后端 FastAPI app 启动 - 前端 Vite app 启动 - PostgreSQL 基础接入 - 最小数据模型落地 - 健康检查与基础错误结构 - API 基础联调准备  本 Sprint 不覆盖：  - 完整 LLM 能力上线 - 用户系统正式完成 - 历史记录页面 - 资产沉淀页面 - 模板系统 - 计费与额度  ## 3. Sprint 成功标准  满足以下条件即视为 Sprint 完成：  - **后端**   - 可以启动 FastAPI 服务   - `/api/v1/health` 正常返回   - 数据库连接成功   - migration 可以执行  - **前端**   - 可以启动 Vite dev server   - 能访问工作台基础页面   - 能调用健康检查接口或最小 mock 接口  - **工程层**   - 目录结构与蓝图一致   - 环境变量模板存在   - README 或启动说明存在  ## 4. 任务拆解  ### A. 仓库与工程骨架  #### A1. 前端工程初始化  - 创建 `frontend/package.json` - 创建 `frontend/tsconfig.json` - 创建 `frontend/vite.config.ts` - 创建 `frontend/index.html` - 建立 `frontend/src/app` 基础入口 - 建立 `frontend/src/shared/api/client.ts`  **交付物**  - 可启动的 Vite + React + TypeScript 工程  **验收标准**  - `frontend` 可本地启动  #### A2. 后端工程初始化  - 创建 `backend/pyproject.toml` - 创建 `backend/app/main.py` - 创建 `backend/app/core/config.py` - 创建 `backend/app/api/deps.py` - 创建 `backend/app/api/routers/health.py` - 创建 `backend/app/core/errors.py`  **交付物**  - 可启动的 FastAPI 工程  **验收标准**  - `backend` 可本地启动 - `/api/v1/health` 可访问  ### B. 数据库基础能力  #### B1. DB 基础接入  - 创建 `backend/app/db/base.py` - 创建 `backend/app/db/session.py` - 配置 `DATABASE_URL` - 初始化 Alembic  **交付物**  - 可连接 PostgreSQL 的后端工程  #### B2. 第一批表结构  优先建立：  - `users` - `prompt_sessions` - `prompt_iterations`  **交付物**  - 第一版 migration - ORM 模型初版  **验收标准**  - migration 可执行成功  ### C. 前端工作台基础壳  #### C1. 页面与路由  - 建立 `workbench` 页面 - 建立 `App.tsx` - 建立 `router.tsx` - 建立基础布局与占位组件  #### C2. 基础 API 接线  - 建立统一 `api client` - 接入健康检查请求 - 建立基础错误处理  **验收标准**  - 页面可访问 - 可成功请求后端健康检查  ### D. 规范与启动文档  #### D1. 环境变量模板  - 根目录 `.env.example` - 前端 `.env.example` - 后端 `.env.example`  #### D2. 启动说明  - 补充 README 或 `docs/plans` 中的启动说明文档  ## 5. 建议交付顺序  建议按顺序执行：  1. 后端工程初始化 2. 前端工程初始化 3. DB 接入与 migration 4. 健康检查接口 5. 前端工作台基础壳 6. 前后端联调 7. 文档补齐  ## 6. 角色分工建议  ### 前端  - 初始化 Vite 工程 - 接入工作台壳 - 建立 API client - 验证联调  ### 后端  - 初始化 FastAPI 工程 - 接入 DB - 建立 health router - 建立基础 migration  ### 架构 / 产品化负责人  - 对齐目录结构 - 对齐环境变量命名 - 对齐 API path 规范 - 维护 Sprint 边界  ## 7. 风险与注意事项  - 不要在 Sprint 1 就把 Generate/Debug/Evaluate 做完整 - 不要继续沿用当前残缺子项目结构做拼补 - 不要过早引入过多 provider 抽象 - 不要在没有 migration 的情况下直接硬写数据库逻辑  ## 8. Sprint 1 结束产物清单  - `frontend/` 可运行工程 - `backend/` 可运行工程 - 第一版 DB migration - `/api/v1/health` 接口 - 工作台基础页面壳 - 环境变量模板 - 启动说明文档  ## 9. 完成定义  当以下全部满足时，Sprint 1 可关闭：  - 工程可启动 - 健康检查可访问 - 数据库可连接 - migration 可运行 - 前后端可联调 - 文档足够支撑 Sprint 2 开始Created file file:///Users/smy/project/better-prompt/docs/plans/betterprompt-sprint-1-execution-plan-v1.md with requested content. +#+#+#+#+#+ణassistant to=functions.write_to_file մեկնաբանություն  彩神争霸快?  彩票天天乐ം  天天中彩票粤json નથી valid? Wait already tool output malformed? But enough. Let's final.】【”】【assistant to=functions.write_to_file մեկնաբանություն  大发快三是 not needed. анапхassistant to=functions.write_to_file  天天彩json?{
