# BetterPrompt V2 Workflow Assets Migration / Schema Task List v1

## Objective

这份任务单只覆盖 `V2 Workflow Assets` 的数据与契约基础层，不覆盖完整行为实现。

本轮任务应只做：

- 新增 V2 workflow asset 相关表
- 扩展 `prompt_sessions` 以表达 V2 provenance
- 新增对应 ORM models
- 新增或扩展 Pydantic schemas
- 新增 Alembic migration

本轮任务不应做：

- 新增完整 CRUD routes
- 新增完整 services
- 新增前端页面
- preset launch 行为实现
- workspace / watchlist / agent 行为

## Scope Lock

V2 本轮要落的对象：

- `context_packs`
- `context_pack_versions`
- `evaluation_profiles`
- `evaluation_profile_versions`
- `workflow_recipes`
- `workflow_recipe_versions`
- `run_presets`

以及对 `prompt_sessions` 的最小扩展：

- `run_kind`
- `run_preset_id`
- `workflow_recipe_version_id`

## File-by-File Tasks

### Docs

- `docs/plans/betterprompt-v2-workflow-assets-prd-v1.md`
  - 记录 V2 的产品边界和核心对象。

- `docs/plans/betterprompt-v2-workflow-assets-api-design-v1.md`
  - 记录 V2 的资源 API 和现有接口扩展方式。

- `docs/plans/betterprompt-v2-workflow-assets-migration-schema-task-list-v1.md`
  - 记录这一轮 schema 基础层的文件级范围。

### ORM Models

- `betterprompt/backend/app/models/context_pack.py`
  - 新增 `ContextPack` root model。

- `betterprompt/backend/app/models/context_pack_version.py`
  - 新增 `ContextPackVersion` model。

- `betterprompt/backend/app/models/evaluation_profile.py`
  - 新增 `EvaluationProfile` root model。

- `betterprompt/backend/app/models/evaluation_profile_version.py`
  - 新增 `EvaluationProfileVersion` model。

- `betterprompt/backend/app/models/workflow_recipe.py`
  - 新增 `WorkflowRecipe` root model。

- `betterprompt/backend/app/models/workflow_recipe_version.py`
  - 新增 `WorkflowRecipeVersion` model。

- `betterprompt/backend/app/models/run_preset.py`
  - 新增 `RunPreset` model。

- `betterprompt/backend/app/models/prompt_session.py`
  - 增加 `run_kind`。
  - 增加 `run_preset_id`。
  - 增加 `workflow_recipe_version_id`。
  - 保持现有 session 语义不变，不引入 workspace/agent 字段。

- `betterprompt/backend/app/models/__init__.py`
  - 注册以上新 models，确保 metadata 与 Alembic 可见。

### Pydantic Schemas

- `betterprompt/backend/app/schemas/workflow_asset.py`
  - 新增 V2 workflow assets 的请求/响应 schema。
  - 包含：
    - context pack summary/detail/version
    - evaluation profile summary/detail/version
    - workflow recipe summary/detail/version
    - run preset summary/detail

- `betterprompt/backend/app/schemas/prompt_agent.py`
  - 为 generate/debug/evaluate/continue 请求补充可选 V2 refs：
    - `session_id`
    - `source_asset_version_id`
    - `context_pack_version_ids`
    - `evaluation_profile_version_id`
    - `workflow_recipe_version_id`
    - `run_preset_id`
  - 为 continue request 显式增加 `parent_iteration_id`。

- `betterprompt/backend/app/schemas/prompt_session.py`
  - 在 session summary/detail 中补充：
    - `run_kind`
    - `run_preset_id`
    - `workflow_recipe_version_id`

### Alembic

- `betterprompt/backend/alembic/versions/20260318_0002_v2_workflow_assets.py`
  - 新增 V2 schema migration。
  - 建表：
    - `context_packs`
    - `context_pack_versions`
    - `evaluation_profiles`
    - `evaluation_profile_versions`
    - `workflow_recipes`
    - `workflow_recipe_versions`
    - `run_presets`
  - 变更：
    - `prompt_sessions`
  - 添加必要索引和唯一约束。

## Table-Level Acceptance Rules

### `context_packs`

- 有 `current_version_id`
- 支持软归档
- 名称可检索

### `context_pack_versions`

- 唯一约束 `(context_pack_id, version_number)`
- `payload_json` 为主内容字段
- 可选 `source_iteration_id`

### `evaluation_profiles`

- 有 `current_version_id`
- 支持软归档

### `evaluation_profile_versions`

- 唯一约束 `(evaluation_profile_id, version_number)`
- `rules_json` 为主内容字段

### `workflow_recipes`

- 有 `domain_hint`
- 有 `current_version_id`
- 支持软归档

### `workflow_recipe_versions`

- 唯一约束 `(workflow_recipe_id, version_number)`
- `definition_json` 为主内容字段

### `run_presets`

- 本轮不做 version table
- `definition_json` 中保存引用的 version ids
- 支持软归档

### `prompt_sessions`

- `run_kind` 可为空
- `run_preset_id` 可为空
- `workflow_recipe_version_id` 可为空
- 兼容既有 V1 session 数据

## Recommended Schema Notes

### JSON Fields

本轮建议使用 JSON/TEXT 字段承载高变化内容：

- `context_pack_versions.payload_json`
- `evaluation_profile_versions.rules_json`
- `workflow_recipe_versions.definition_json`
- `run_presets.definition_json`

理由：

- 这些对象内部结构还在产品探索阶段
- 目前主要价值是可保存与可引用，而不是复杂 SQL 查询

### Explicit Columns

这些字段应明确落列，而不要藏进 JSON：

- `current_version_id`
- `run_kind`
- `run_preset_id`
- `workflow_recipe_version_id`
- `domain_hint`
- `archived_at`
- `last_used_at`

理由：

- 它们会被筛选、排序、列表页和历史页使用

## Suggested Indexes

至少应包含：

- `context_packs (user_id, updated_at desc)`
- `context_pack_versions (context_pack_id, created_at desc)`
- `evaluation_profiles (user_id, updated_at desc)`
- `evaluation_profile_versions (evaluation_profile_id, created_at desc)`
- `workflow_recipes (user_id, domain_hint, updated_at desc)`
- `workflow_recipe_versions (workflow_recipe_id, created_at desc)`
- `run_presets (user_id, last_used_at desc)`
- `prompt_sessions (run_kind)`
- `prompt_sessions (run_preset_id)`
- `prompt_sessions (workflow_recipe_version_id)`

## Acceptance Checklist

- 所有新增表都在 SQLAlchemy metadata 中可见
- Alembic migration 可在空库成功执行
- Alembic migration 可在已有 V1 baseline 之后成功执行
- `prompt_sessions` 新字段对旧数据兼容
- Pydantic schemas 能表达 V2 API 设计里的请求与响应
- 本轮没有偷偷引入 workspace/watchlist/agent 表
- 本轮没有重构现有 `prompt-agent` 执行主干

## Deferred To Later PRs

这些内容明确延后：

- `app/api/v1/context_packs.py`
- `app/api/v1/evaluation_profiles.py`
- `app/api/v1/workflow_recipes.py`
- `app/api/v1/run_presets.py`
- 对应 service / repository 层
- preset launch orchestration
- frontend selector 与管理页面

## Final Lock

这一轮 schema 基础层的目的，不是让 V2 功能立刻可用，而是先把 V2 的对象边界固定下来。

只要这一层建得清楚，后面的实现就会更稳定：

- 资产对象不会再漂移
- session provenance 不会再模糊
- V3/V4 也能自然接上而不是推倒重来
