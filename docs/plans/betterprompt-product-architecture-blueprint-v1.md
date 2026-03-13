# 《BetterPrompt 产品化架构蓝图 v1》

## 1. 文档目标

本文定义 `BetterPrompt` 从当前原型骨架演进为**可上线产品**的目标架构，覆盖：

- **产品边界**
- **系统分层**
- **前后端模块设计**
- **核心数据模型**
- **接口设计原则**
- **模型调用与策略编排**
- **安全、观测、部署**
- **分阶段落地路线**

本文定位为 **v1 母版蓝图**，用于指导后续实施拆解、研发排期与架构收口。

# 2. 产品定义

## 2.1 产品定位

`BetterPrompt` 是一个面向知识工作者、开发者、分析师与内容创作者的 **Prompt 生产与优化平台**。

它不只是“生成一句 Prompt”，而是提供完整的 Prompt 生命周期工具链：

- **生成**
  - 从模糊目标生成高质量 Prompt

- **诊断**
  - 分析现有 Prompt 的结构缺陷与失败模式

- **评估**
  - 对 Prompt 或输出进行质量评分与定位问题

- **继续优化**
  - 基于既有结果做增量打磨，而不是每次推倒重来

- **资产化**
  - 把 Prompt 从一次性文本，升级为可保存、可追踪、可复用的资产

## 2.2 目标用户

- **个人用户**
  - 需要高质量 Prompt 的普通用户、内容创作者、开发者

- **专业用户**
  - 频繁进行分析、写作、代码协作、调研的高级用户

- **团队用户**
  - 需要沉淀模板、共享标准、统一输出质量的团队

## 2.3 产品核心价值

- **降低 Prompt 设计门槛**
- **提高 Prompt 输出质量稳定性**
- **沉淀可复用 Prompt 资产**
- **形成优化闭环与版本链路**
- **支撑后续团队协作与商业化**

# 3. 非目标与边界

## 3.1 v1 非目标

以下能力不纳入 v1 的第一优先级：

- **复杂多 Agent 工作流编排平台**
- **通用聊天产品**
- **全文档知识库 RAG 平台**
- **低代码自动化平台**
- **团队权限矩阵的重型企业方案**

## 3.2 v1 边界

v1 只聚焦：

- Prompt 生产
- Prompt 诊断
- Prompt 评估
- Prompt 继续优化
- 结果保存与版本追踪
- 模板沉淀
- 用户个人工作流闭环

# 4. 目标系统架构总览

## 4.1 总体形态

推荐采用 **前后端分离 + 单体服务优先 + 清晰领域模块化** 的架构。

原因：

- 当前产品仍在快速迭代
- 团队尚未体现强烈微服务需求
- Prompt 领域逻辑需要高内聚
- 先控制复杂度，再逐步拆分

## 4.2 高层架构

```text
Web Frontend
    |
    v
API Gateway / Backend App
    |
    +-- Auth & User Context
    +-- Prompt Session Domain
    +-- Prompt Asset Domain
    +-- Template Domain
    +-- Evaluation Domain
    +-- LLM Orchestration Domain
    +-- Observability / Billing / Quota
    |
    v
Postgres + Redis + Object Storage + LLM Providers
```

## 4.3 核心原则

- **单体优先**
  - 用一个后端服务承载主要业务

- **领域隔离**
  - 代码层面按 domain 分层，不按技术碎片散落

- **契约清晰**
  - 前后端通过显式 schema 对齐

- **产品优先**
  - 围绕用户工作流建模，而不是围绕 demo 页面建模

- **智能能力可替换**
  - LLM provider、策略规则、评分器都应可替换

# 5. 前端架构蓝图

## 5.1 技术建议

建议使用：

- **React**
- **TypeScript**
- **Vite**
- **React Router**
- **TanStack Query**
- **Tailwind CSS**
- **Zod**
- **React Hook Form**

## 5.2 前端目标目录结构

```text
frontend/
  src/
    app/
      App.tsx
      router.tsx
      providers.tsx
    pages/
      home/
      workspace/
      history/
      templates/
      settings/
    features/
      prompt-workbench/
      prompt-history/
      prompt-templates/
      auth/
      billing/
    entities/
      prompt-session/
      prompt-asset/
      user/
      template/
    shared/
      api/
      ui/
      hooks/
      lib/
      config/
      types/
    styles/
```

## 5.3 v1 核心页面

- **工作台页**
- **历史记录页**
- **结果详情页**
- **模板页**
- **设置页**

# 6. 后端架构蓝图

## 6.1 技术建议

建议使用：

- **FastAPI**
- **Pydantic**
- **SQLAlchemy 2.x**
- **Alembic**
- **PostgreSQL**
- **Redis**
- **Structlog / 标准化 logging**
- **OpenTelemetry**

## 6.2 后端目标目录结构

```text
backend/
  app/
    main.py
    core/
      config.py
      logging.py
      security.py
      errors.py
      middleware.py
    api/
      deps.py
      routers/
        auth.py
        prompt_sessions.py
        prompt_assets.py
        templates.py
        evaluations.py
        health.py
    domain/
      prompt_session/
      prompt_asset/
      template/
      evaluation/
      llm/
      auth/
      quota/
      analytics/
    db/
      base.py
      session.py
      migrations/
    workers/
      tasks/
    tests/
```

# 7. 领域建模蓝图

v1 推荐至少拆出 5 个核心领域：

- **Prompt Session Domain**
- **Prompt Asset Domain**
- **Template Domain**
- **Evaluation Domain**
- **LLM Orchestration Domain**

# 8. 目标数据模型

v1 推荐的最小数据模型：

- `users`
- `prompt_sessions`
- `prompt_iterations`
- `prompt_assets`
- `prompt_asset_versions`
- `templates`
- `template_versions`
- `evaluation_records`
- `usage_records`

# 9. API 架构蓝图

## 9.1 v1 推荐接口分组

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/prompt-sessions`
- `GET /api/v1/prompt-sessions`
- `GET /api/v1/prompt-sessions/{id}`
- `POST /api/v1/prompt-sessions/{id}/generate`
- `POST /api/v1/prompt-sessions/{id}/debug`
- `POST /api/v1/prompt-sessions/{id}/evaluate`
- `POST /api/v1/prompt-sessions/{id}/continue`
- `POST /api/v1/prompt-assets`
- `GET /api/v1/prompt-assets`
- `GET /api/v1/prompt-assets/{id}`
- `POST /api/v1/prompt-assets/{id}/versions`
- `PATCH /api/v1/prompt-assets/{id}`
- `GET /api/v1/templates`
- `POST /api/v1/templates`
- `GET /api/v1/templates/{id}`
- `POST /api/v1/templates/{id}/versions`
- `GET /api/v1/evaluations/{id}`
- `GET /api/v1/health`
- `GET /api/v1/usage/me`

# 10. LLM 编排架构蓝图

v1 至少应具备：

- **Provider 抽象**
- **Model Policy**
- **Prompt Compiler**
- **Structured Output Parser**
- **Retry / Fallback**
- **Cost Control**

## 10.1 推荐编排流水线

### Generate Pipeline

```text
Input Validation
 -> Session Context Load
 -> Task Classification
 -> Strategy Selection
 -> Prompt Compilation
 -> LLM Call
 -> Output Parse
 -> Post Validation
 -> Persistence
 -> Response
```

### Debug Pipeline

```text
Input Validation
 -> Existing Prompt Analysis
 -> Failure Mode Diagnosis
 -> Fix Strategy Selection
 -> Rewrite Prompt Compilation
 -> LLM Call
 -> Parse and Persist
 -> Response
```

### Evaluate Pipeline

```text
Input Validation
 -> Evaluation Rubric Selection
 -> LLM Evaluation / Rule Hybrid Evaluation
 -> Score Normalization
 -> Result Persistence
 -> Response
```

### Continue Pipeline

```text
Load Previous Iteration
 -> Preserve Effective Structure
 -> Apply Incremental Goal
 -> LLM Rewrite
 -> Parse and Persist
 -> Return New Iteration
```

# 11. 安全架构蓝图

基础安全要求：

- **认证**
- **权限**
- **限流**
- **输入限制**
- **密钥管理**
- **审计**

# 12. 可观测性蓝图

至少监控：

- 请求量
- 成功率
- 平均耗时
- provider 失败率
- token 使用量
- 估算成本
- 各 mode 使用占比
- 用户留存行为
- Continue 使用率
- 模板保存率

# 13. 部署架构蓝图

## 13.1 v1 推荐部署方式

- **前端**
  - Vercel / Netlify / CDN 静态部署

- **后端**
  - 单容器 FastAPI 服务

- **数据库**
  - PostgreSQL

- **缓存**
  - Redis

- **对象存储**
  - S3 兼容存储

# 14. 开发与测试蓝图

测试分层：

- **单元测试**
- **集成测试**
- **前端测试**
- **E2E**

# 15. 从当前代码迁移到目标架构的映射建议

- 保留 `prompt_agent` 的领域概念
- 保留 `orchestrator` 作为编排器角色定位
- 保留前端 `prompt-agent` feature 的页面交互方向
- 重构 API client
- 将 router 从功能接口升级为资源型 session 接口
- 将 engine 升级为真实 LLM pipeline

# 16. 分阶段实施路线

- **Phase 1：独立可运行原型**
- **Phase 2：可内测产品**
- **Phase 3：可上线产品**
- **Phase 4：平台化升级**

# 17. v1 关键决策

- **前后端分离**
- **后端单体优先**
- **PostgreSQL 作为主库**
- **Redis 作为缓存**
- **以 `session + iteration + asset` 作为核心模型**
- **使用 provider abstraction**
- **使用混合评估模型**

# 18. 推荐的首批实施清单

- 补全前端工程骨架
- 补全 FastAPI app 与路由注册
- 设计并落地 `prompt_sessions` / `prompt_iterations` 表
- 重构当前 `/prompt-agent/*` 为 session 驱动接口
- 接入第一个真实 LLM provider
- 把 generate/debug/evaluate/continue 改造为 pipeline
- 收口前端 API client 与 feature 边界
- 增加历史记录与结果详情页
- 增加统一日志、错误结构、health check
- 增加基础集成测试和 E2E

# 19. 最终结论

`BetterPrompt` 的正确产品化方向，不是把当前骨架“补一补就上线”，而是要围绕：

- **会话**
- **版本**
- **资产**
- **评估**
- **模型编排**

重新建立一套真正可运行、可沉淀、可追踪、可扩展的产品架构。
