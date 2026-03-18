# BetterPrompt V4 Freshness-Aware Agents Migration / Schema Task List v1

## Objective

这份任务单只覆盖 `V4 Freshness-Aware Agents` 的 schema 与契约基础层。

本轮应只做：

- 新增 agent runtime 相关表
- 扩展 `prompt_sessions` 的 agent provenance 字段
- 新增 ORM models
- 新增或扩展 Pydantic schemas
- 新增 Alembic migration

本轮不应做：

- scheduler / worker 实现
- 外部行情源接入
- alert delivery channel 实现
- frontend updates feed 实现

## Scope Lock

V4 新增对象：

- `watchlists`
- `watchlist_items`
- `agent_monitors`
- `agent_runs`
- `agent_alerts`
- `freshness_records`

以及对 `prompt_sessions` 的扩展：

- `agent_monitor_id`
- `trigger_kind`

## File-by-File Tasks

### Docs

- `docs/plans/betterprompt-v4-freshness-aware-agents-prd-v1.md`
- `docs/plans/betterprompt-v4-freshness-aware-agents-api-design-v1.md`
- `docs/plans/betterprompt-v4-freshness-aware-agents-migration-schema-task-list-v1.md`

### ORM Models

- `betterprompt/backend/app/models/watchlist.py`
- `betterprompt/backend/app/models/watchlist_item.py`
- `betterprompt/backend/app/models/agent_monitor.py`
- `betterprompt/backend/app/models/agent_run.py`
- `betterprompt/backend/app/models/agent_alert.py`
- `betterprompt/backend/app/models/freshness_record.py`

- `betterprompt/backend/app/models/prompt_session.py`
  - 增加 `agent_monitor_id`
  - 增加 `trigger_kind`

- `betterprompt/backend/app/models/__init__.py`
  - 注册新 models

### Pydantic Schemas

- `betterprompt/backend/app/schemas/agent_runtime.py`
  - 定义 watchlist、monitor、run、alert、freshness 的请求/响应 schema

- `betterprompt/backend/app/schemas/prompt_session.py`
  - 增加：
    - `agent_monitor_id`
    - `trigger_kind`

### Alembic

- `betterprompt/backend/alembic/versions/20260318_0004_v4_freshness_agents.py`
  - 新增 V4 schema migration
  - 建表：
    - `watchlists`
    - `watchlist_items`
    - `agent_monitors`
    - `agent_runs`
    - `agent_alerts`
    - `freshness_records`
  - 变更：
    - `prompt_sessions`

## Table-Level Rules

### `watchlists`

- 必须绑定 `workspace_id`
- 支持软归档

### `watchlist_items`

- 唯一约束 `(watchlist_id, subject_id)`
- 有 `sort_order`

### `agent_monitors`

- `monitor_type` 为显式列
- `trigger_config_json` 保存触发细节
- `alert_policy_json` 保存告警策略
- 支持 active / paused

### `agent_runs`

- 必须绑定 `monitor_id`
- 建议记录 `previous_run_id`
- 必须可关联 `prompt_session_id`
- 必须保存 `change_summary_json`

### `agent_alerts`

- 必须可关联 `run_id`
- 有 `severity`
- 有 `status`

### `freshness_records`

- 可以挂到 `source_id`
- 也可以挂到 `subject_id`
- 必须保存 `status`
- 必须保存 `observed_at`

### `prompt_sessions`

- `agent_monitor_id` 可为空
- `trigger_kind` 可为空
- 兼容 V1/V2/V3 数据

## Suggested Indexes

- `watchlists (workspace_id, updated_at desc)`
- `watchlist_items (watchlist_id, sort_order)`
- `agent_monitors (workspace_id, status, next_run_at)`
- `agent_runs (monitor_id, started_at desc)`
- `agent_runs (workspace_id, subject_id, started_at desc)`
- `agent_alerts (workspace_id, status, created_at desc)`
- `freshness_records (workspace_id, status, observed_at desc)`
- `prompt_sessions (agent_monitor_id)`
- `prompt_sessions (trigger_kind)`

## Acceptance Checklist

- 所有 V4 表在 metadata 中可见
- Alembic migration 可接在 V3 之后执行
- `prompt_sessions` 的 agent provenance 对旧数据兼容
- 本轮没有引入外部事件总线实现
- 本轮没有把 trading / brokerage 行为塞进 schema

## Deferred To Later PRs

- scheduler / cron / worker
- external market/news source connectors
- alert delivery
- updates feed UI
- diff rendering UI

## Final Lock

V4 schema 的目的，是让 BetterPrompt 有一套可追溯的 agent runtime 结构，而不是先把自动化跑起来。

真正的 worker、trigger、delivery 可以后续实现，但底层对象必须先成型。
