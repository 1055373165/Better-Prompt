# BetterPrompt V3 Domain Workspaces Migration / Schema Task List v1

## Objective

这份任务单只覆盖 `V3 Domain Workspaces` 的 schema 与契约基础层。

本轮任务应只做：

- 新增 workspace 相关表
- 扩展 `prompt_sessions` 以表达 workspace provenance
- 新增 ORM models
- 新增或扩展 Pydantic schemas
- 新增 Alembic migration

本轮不应做：

- watchlist / monitor / alert 表
- 完整 route / service 行为
- 前端 workspace 页实现

## Scope Lock

V3 本轮新增对象：

- `domain_workspaces`
- `workspace_subjects`
- `research_sources`
- `research_reports`
- `research_report_versions`

以及对 `prompt_sessions` 的扩展：

- `domain_workspace_id`
- `subject_id`

## File-by-File Tasks

### Docs

- `docs/plans/betterprompt-v3-domain-workspaces-prd-v1.md`
- `docs/plans/betterprompt-v3-domain-workspaces-api-design-v1.md`
- `docs/plans/betterprompt-v3-domain-workspaces-migration-schema-task-list-v1.md`

### ORM Models

- `betterprompt/backend/app/models/domain_workspace.py`
- `betterprompt/backend/app/models/workspace_subject.py`
- `betterprompt/backend/app/models/research_source.py`
- `betterprompt/backend/app/models/research_report.py`
- `betterprompt/backend/app/models/research_report_version.py`

- `betterprompt/backend/app/models/prompt_session.py`
  - 增加 `domain_workspace_id`
  - 增加 `subject_id`

- `betterprompt/backend/app/models/__init__.py`
  - 注册新 models

### Pydantic Schemas

- `betterprompt/backend/app/schemas/domain_workspace.py`
  - 定义 workspace、subject、source、report、report version 的请求/响应 schema

- `betterprompt/backend/app/schemas/prompt_agent.py`
  - 在 V2 refs 基础上增加：
    - `domain_workspace_id`
    - `subject_id`

- `betterprompt/backend/app/schemas/prompt_session.py`
  - 在 detail / summary 中增加：
    - `domain_workspace_id`
    - `subject_id`

### Alembic

- `betterprompt/backend/alembic/versions/20260318_0003_v3_domain_workspaces.py`
  - 新增 V3 schema migration
  - 建表：
    - `domain_workspaces`
    - `workspace_subjects`
    - `research_sources`
    - `research_reports`
    - `research_report_versions`
  - 变更：
    - `prompt_sessions`

## Table-Level Rules

### `domain_workspaces`

- `workspace_type` 为显式列
- `config_json` 保存默认 preset / recipe 等绑定
- 支持软归档

### `workspace_subjects`

- `subject_type` 为显式列
- `external_key` 可为空
- 同一 workspace 下应能按 subject_type 和 external_key 查询

### `research_sources`

- `source_type` 为显式列
- `content_json` 保存主体内容
- `source_timestamp` 可为空

### `research_reports`

- `latest_version_id` 为显式列
- 支持软归档

### `research_report_versions`

- 唯一约束 `(report_id, version_number)`
- 可选 `source_session_id`
- 可选 `source_iteration_id`

### `prompt_sessions`

- `domain_workspace_id` 可为空
- `subject_id` 可为空
- 兼容已有 V1/V2 session 数据

## Suggested Indexes

- `domain_workspaces (user_id, workspace_type, updated_at desc)`
- `workspace_subjects (workspace_id, subject_type, updated_at desc)`
- `research_sources (workspace_id, subject_id, updated_at desc)`
- `research_reports (workspace_id, subject_id, updated_at desc)`
- `research_report_versions (report_id, created_at desc)`
- `prompt_sessions (domain_workspace_id)`
- `prompt_sessions (subject_id)`

## Acceptance Checklist

- 所有 V3 表在 metadata 中可见
- Alembic migration 可接在 V2 之后执行
- `prompt_sessions` 的 workspace provenance 字段可为空且兼容旧数据
- 本轮没有引入 V4 agent runtime 表

## Deferred To Later PRs

- `app/api/v1/domain_workspaces.py`
- 对应 service / repository 层
- workspace UI
- monitor / alert / freshness 机制

## Final Lock

V3 schema 的目标是让 BetterPrompt 具备“工作区语义”，而不是先把 agent runtime 提前塞进来。
