# 《BetterPrompt 目录结构与数据库设计草案 v1》

## 1. 文档目标

本文给出 `BetterPrompt` 面向产品化落地的：

- **目录结构建议**
- **模块职责边界**
- **数据库核心表设计**
- **表关系与演进策略**
- **关键建模取舍**

# 2. 设计原则

- **按领域组织，而不是按技术碎片组织**
- **前后端都要体现产品边界**
- **避免继续沿用当前抽离残留结构**
- **为 session / iteration / asset / template 留清晰位置**

# 3. 推荐仓库目录结构

```text
better-prompt/
  README.md
  docs/
    architecture/
    product/
    api/
    db/
  frontend/
  backend/
  scripts/
  .env.example
  docker-compose.yml
```

# 4. 前端目录结构草案

```text
frontend/
  package.json
  tsconfig.json
  vite.config.ts
  index.html
  public/
  src/
    app/
      App.tsx
      router.tsx
      providers.tsx
      error-boundary.tsx
    pages/
      workbench/
        index.tsx
      history/
        index.tsx
        detail.tsx
      assets/
        index.tsx
        detail.tsx
      templates/
        index.tsx
        detail.tsx
      settings/
        index.tsx
      auth/
        login.tsx
    features/
      prompt-workbench/
        components/
        hooks/
        api/
        types.ts
      prompt-history/
        components/
        hooks/
        api/
        types.ts
      prompt-assets/
        components/
        hooks/
        api/
        types.ts
      prompt-templates/
        components/
        hooks/
        api/
        types.ts
      auth/
        components/
        hooks/
        api/
        types.ts
    entities/
      prompt-session/
        model.ts
        ui/
      prompt-iteration/
        model.ts
        ui/
      prompt-asset/
        model.ts
        ui/
      template/
        model.ts
        ui/
      user/
        model.ts
        ui/
    shared/
      api/
        client.ts
        error.ts
      config/
        env.ts
      hooks/
      lib/
      ui/
      types/
    styles/
      globals.css
```

# 5. 后端目录结构草案

```text
backend/
  pyproject.toml
  alembic.ini
  app/
    main.py
    core/
      config.py
      logging.py
      security.py
      middleware.py
      errors.py
      constants.py
    api/
      deps.py
      routers/
        auth.py
        prompt_sessions.py
        prompt_assets.py
        templates.py
        usage.py
        health.py
    db/
      base.py
      session.py
      models/
        user.py
        prompt_session.py
        prompt_iteration.py
        prompt_asset.py
        prompt_asset_version.py
        template.py
        template_version.py
        usage_record.py
      migrations/
    domain/
      auth/
        schemas.py
        service.py
      prompt_session/
        schemas.py
        repository.py
        service.py
      prompt_iteration/
        schemas.py
        repository.py
        service.py
      prompt_asset/
        schemas.py
        repository.py
        service.py
      template/
        schemas.py
        repository.py
        service.py
      evaluation/
        schemas.py
        service.py
      llm/
        schemas.py
        providers/
          base.py
          openai_provider.py
          anthropic_provider.py
        orchestration/
          prompt_workflow_service.py
          prompt_compiler.py
          model_policy.py
          output_parser.py
          fallback.py
        evaluators/
          rule_evaluator.py
          llm_evaluator.py
    workers/
      tasks/
    tests/
      unit/
      integration/
      e2e/
```

# 6. 数据库总体设计

## 6.1 核心实体关系图

```text
User
  ├── PromptSession
  │      └── PromptIteration (1:N, self-parent)
  ├── PromptAsset
  │      └── PromptAssetVersion (1:N)
  ├── Template
  │      └── TemplateVersion (1:N)
  └── UsageRecord
```

# 7. 核心表设计草案

## 7.1 `users`

```text
id                  uuid pk
email               varchar unique not null
name                varchar not null
avatar_url          varchar null
status              varchar not null default 'active'
password_hash       varchar null
provider            varchar null
provider_subject    varchar null
created_at          timestamptz not null
updated_at          timestamptz not null
last_login_at       timestamptz null
```

## 7.2 `prompt_sessions`

```text
id                      uuid pk
user_id                 uuid not null fk users(id)
title                   varchar not null
entry_mode              varchar not null
status                  varchar not null default 'active'
source_template_id      uuid null fk templates(id)
latest_iteration_id     uuid null
pinned_asset_id         uuid null fk prompt_assets(id)
metadata_json           jsonb not null default '{}'
created_at              timestamptz not null
updated_at              timestamptz not null
archived_at             timestamptz null
```

## 7.3 `prompt_iterations`

```text
id                      uuid pk
session_id              uuid not null fk prompt_sessions(id)
parent_iteration_id     uuid null fk prompt_iterations(id)
mode                    varchar not null
status                  varchar not null
input_text              text null
output_text             text null
input_payload_json      jsonb not null default '{}'
output_payload_json     jsonb not null default '{}'
diagnosis_json          jsonb not null default '{}'
evaluation_json         jsonb not null default '{}'
optimization_goal       varchar null
artifact_type           varchar null
provider                varchar null
model                   varchar null
temperature             numeric(4,2) null
tokens_input            integer null
tokens_output           integer null
latency_ms              integer null
error_code              varchar null
error_message           text null
started_at              timestamptz null
completed_at            timestamptz null
created_at              timestamptz not null
```

## 7.4 `prompt_assets`

```text
id                      uuid pk
user_id                 uuid not null fk users(id)
source_session_id       uuid null fk prompt_sessions(id)
name                    varchar not null
description             text null
artifact_type           varchar not null
current_version_id      uuid null
is_favorite             boolean not null default false
visibility              varchar not null default 'private'
tags_json               jsonb not null default '[]'
metadata_json           jsonb not null default '{}'
created_at              timestamptz not null
updated_at              timestamptz not null
deleted_at              timestamptz null
```

## 7.5 `prompt_asset_versions`

```text
id                      uuid pk
asset_id                uuid not null fk prompt_assets(id)
version_number          integer not null
title                   varchar null
content                 text not null
source_iteration_id     uuid null fk prompt_iterations(id)
change_summary          text null
metadata_json           jsonb not null default '{}'
created_at              timestamptz not null
```

## 7.6 `templates`

```text
id                      uuid pk
owner_type              varchar not null
owner_id                uuid null
name                    varchar not null
description             text null
category                varchar not null
artifact_type           varchar not null
visibility              varchar not null default 'private'
current_version_id      uuid null
is_official             boolean not null default false
metadata_json           jsonb not null default '{}'
created_at              timestamptz not null
updated_at              timestamptz not null
```

## 7.7 `template_versions`

```text
id                      uuid pk
template_id             uuid not null fk templates(id)
version_number          integer not null
content                 text not null
schema_json             jsonb not null default '{}'
metadata_json           jsonb not null default '{}'
created_at              timestamptz not null
```

## 7.8 `usage_records`

```text
id                      uuid pk
user_id                 uuid not null fk users(id)
iteration_id            uuid null fk prompt_iterations(id)
provider                varchar not null
model                   varchar not null
tokens_input            integer not null default 0
tokens_output           integer not null default 0
estimated_cost_usd      numeric(12,6) not null default 0
request_type            varchar not null
created_at              timestamptz not null
```

# 8. 核心索引建议

- `idx_prompt_sessions_user_id_created_at`
- `idx_prompt_sessions_user_id_updated_at`
- `idx_prompt_sessions_latest_iteration_id`
- `idx_prompt_iterations_session_id_created_at`
- `idx_prompt_iterations_parent_iteration_id`
- `idx_prompt_iterations_mode`
- `idx_prompt_iterations_status`
- `idx_prompt_iterations_provider_model`
- `idx_prompt_assets_user_id_updated_at`
- `idx_prompt_assets_user_id_is_favorite`
- `idx_usage_records_user_id_created_at`
- `idx_usage_records_iteration_id`

# 9. 关键关系与建模取舍

- `session` 是过程容器
- `iteration` 是操作节点
- `asset` 是沉淀成果
- `template` 是标准复用能力

## 9.1 为什么 `session` 和 `iteration` 必须拆开

如果不拆：

- 历史追踪困难
- continue 链路难建
- debug/evaluate/continue 结果会互相覆盖
- 很难支持版本时间线

## 9.2 为什么 `asset` 不应直接等于 `session`

因为不是每个 session 都会产出有价值成果。

## 9.3 为什么 `template` 和 `asset` 要分开

- `asset` 偏用户工作成果
- `template` 偏复用标准、产品入口、官方能力沉淀

# 10. v1 推荐枚举值草案

## 10.1 `prompt_sessions.entry_mode`

```text
generate
debug
evaluate
```

## 10.2 `prompt_sessions.status`

```text
active
archived
deleted
```

## 10.3 `prompt_iterations.mode`

```text
generate
debug
evaluate
continue
```

## 10.4 `prompt_iterations.status`

```text
pending
running
succeeded
failed
cancelled
```

## 10.5 `prompt_assets.visibility`

```text
private
shared
```

## 10.6 `templates.owner_type`

```text
system
user
workspace
```

## 10.7 `artifact_type`

```text
system_prompt
task_prompt
analysis_workflow
conversation_prompt
```

# 11. v1 不建议过早建的表

- `tags`
- `workspaces`
- `memberships / roles`
- `prompt_feedback`
- `model_policies` 配置表

# 12. 数据迁移建议

- **批次 1**
  - `users`
  - `prompt_sessions`
  - `prompt_iterations`

- **批次 2**
  - `prompt_assets`
  - `prompt_asset_versions`

- **批次 3**
  - `templates`
  - `template_versions`

- **批次 4**
  - `usage_records`
  - 可选 `evaluation_records`

# 13. 首批建库建议

第一版只建以下 5 张表：

- `users`
- `prompt_sessions`
- `prompt_iterations`
- `prompt_assets`
- `prompt_asset_versions`

# 14. 最终结论

这份草案的核心结论是：

- 前端按 `app/pages/features/entities/shared` 分层
- 后端按 `core/api/db/domain` 分层
- 用 `session` 表示过程容器
- 用 `iteration` 表示具体操作节点
- 用 `asset` 表示沉淀成果
- 用 `template` 表示标准复用能力
- 当前 demo 式功能接口应收敛到 `session + iteration` 资源模型
