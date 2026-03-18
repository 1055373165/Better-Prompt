# BetterPrompt Development TODOs

## North Star

这份文档的北极星目标只有一个：

- 让另一个模型在打开这个项目后，不需要重新理解上下文，也能继续往下开发

因此，这不是普通待办清单。

它同时承担四个职责：

1. 当前状态快照
2. 已完成工作的登记簿
3. 下一步开发顺序
4. 模型接力时的最小操作手册

## First Read

如果你是第一次接手这个仓库，请按这个顺序阅读：

1. 本文档 `TODOS.md`
2. [README.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/README.md)
3. [betterprompt-product-reframe-v2-ceo-review.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-product-reframe-v2-ceo-review.md)
4. [betterprompt-v2-v4-product-structure-and-data-model-plan-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-v4-product-structure-and-data-model-plan-v1.md)
5. V2/V3/V4 对应的 `PRD + API + migration/schema task list`

如果你要直接继续写代码，优先看：

1. [betterprompt-pr1-data-foundation-file-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-pr1-data-foundation-file-task-list-v1.md)
2. [betterprompt-v2-workflow-assets-migration-schema-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-workflow-assets-migration-schema-task-list-v1.md)
3. 当前后端 `models / schemas / alembic` 目录

## Current Snapshot

### Repo

- Repo root: `/Users/smy/go/just-for-test-only-once/Better-Prompt`
- Current branch: `main`
- Active app: `betterprompt/`

### Current Product Thesis

BetterPrompt 不是单纯的 prompt 优化器。

当前锁定的主线是：

```text
V1  Prompt Library + Optimization Workbench
V2  Workflow Assets
V3  Domain Workspaces
V4  Freshness-Aware Agents
```

### Current Runtime Backbone

以下对象已被确定为后续版本持续复用的运行主干：

- `prompt_sessions`
- `prompt_iterations`

以下对象已被确定为基础资产层：

- `prompt_categories`
- `prompt_assets`
- `prompt_asset_versions`

## Important Working Rules

### Rule 1

不要把 `V2 / V3 / V4` 混着开发。

推荐顺序必须保持：

1. 先把 `V1` 做完整
2. 再把 `V2 workflow assets` 做成真实能力
3. 再进入 `V3 workspace`
4. 最后才进入 `V4 agent runtime`

### Rule 2

不要把 `agent` 理解成聊天机器人。

后续所有设计都应坚持：

- high-control
- evidence-aware
- freshness-aware
- traceable

### Rule 3

不要为了“通用”过早合并成一个大表。

明确不要做：

- 泛化 `assets` mega-table
- 泛化 `workspaces` team 协作表

### Rule 4

在当前 dirty worktree 上开发时：

- 不要回滚无关改动
- 不要覆盖已有文档
- 不要删除 `.run/logs` 这类运行时文件，除非用户明确要求

## Done

### Product / Design / Architecture Docs

- 已完成 `CEO reframe`
  - [betterprompt-product-reframe-v2-ceo-review.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-product-reframe-v2-ceo-review.md)
- 已完成 `V1 Library + Workbench` 设计稿
  - [betterprompt-prompt-library-workbench-design-plan-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-prompt-library-workbench-design-plan-v1.md)
- 已完成 `V1` 工程执行计划
  - [betterprompt-library-workbench-eng-execution-plan-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-library-workbench-eng-execution-plan-v1.md)
- 已完成 `V2~V4` 产品结构与数据模型主稿
  - [betterprompt-v2-v4-product-structure-and-data-model-plan-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-v4-product-structure-and-data-model-plan-v1.md)

### V2 Docs

- 已完成 `V2 PRD`
  - [betterprompt-v2-workflow-assets-prd-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-workflow-assets-prd-v1.md)
- 已完成 `V2 API 设计`
  - [betterprompt-v2-workflow-assets-api-design-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-workflow-assets-api-design-v1.md)
- 已完成 `V2 migration/schema task list`
  - [betterprompt-v2-workflow-assets-migration-schema-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-workflow-assets-migration-schema-task-list-v1.md)

### V3 Docs

- 已完成 `V3 PRD`
  - [betterprompt-v3-domain-workspaces-prd-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v3-domain-workspaces-prd-v1.md)
- 已完成 `V3 API 设计`
  - [betterprompt-v3-domain-workspaces-api-design-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v3-domain-workspaces-api-design-v1.md)
- 已完成 `V3 migration/schema task list`
  - [betterprompt-v3-domain-workspaces-migration-schema-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v3-domain-workspaces-migration-schema-task-list-v1.md)

### V4 Docs

- 已完成 `V4 PRD`
  - [betterprompt-v4-freshness-aware-agents-prd-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v4-freshness-aware-agents-prd-v1.md)
- 已完成 `V4 API 设计`
  - [betterprompt-v4-freshness-aware-agents-api-design-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v4-freshness-aware-agents-api-design-v1.md)
- 已完成 `V4 migration/schema task list`
  - [betterprompt-v4-freshness-aware-agents-migration-schema-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v4-freshness-aware-agents-migration-schema-task-list-v1.md)

### Backend Foundation

- 已完成 `PR-1 Data Foundation`
  - env-driven DB config
  - Alembic scaffold
  - baseline migration
  - `prompt_categories / prompt_assets / prompt_asset_versions`
- 对应任务单：
  - [betterprompt-pr1-data-foundation-file-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-pr1-data-foundation-file-task-list-v1.md)

### V2 Schema Foundation

以下代码已经开始落地：

- 新增 models
  - [context_pack.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/context_pack.py)
  - [context_pack_version.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/context_pack_version.py)
  - [evaluation_profile.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/evaluation_profile.py)
  - [evaluation_profile_version.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/evaluation_profile_version.py)
  - [workflow_recipe.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/workflow_recipe.py)
  - [workflow_recipe_version.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/workflow_recipe_version.py)
  - [run_preset.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/run_preset.py)
- 已扩展 session schema / request schema
  - [prompt_session.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/models/prompt_session.py)
  - [prompt_agent.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/schemas/prompt_agent.py)
  - [prompt_session.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/schemas/prompt_session.py)
  - [workflow_asset.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/schemas/workflow_asset.py)
- 已新增 migration
  - [20260318_0002_v2_workflow_assets.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/alembic/versions/20260318_0002_v2_workflow_assets.py)

## Verified

这些验证已经实际跑过：

- `compileall` 通过
- 临时库成功执行 `alembic upgrade head`
- 临时库已确认存在：
  - `context_packs`
  - `context_pack_versions`
  - `evaluation_profiles`
  - `evaluation_profile_versions`
  - `workflow_recipes`
  - `workflow_recipe_versions`
  - `run_presets`
- `prompt_sessions` 已确认新增字段：
  - `run_kind`
  - `run_preset_id`
  - `workflow_recipe_version_id`

## Current In Progress

当前真正进入开发阶段的点是：

- `V2 schema foundation`

当前还没有完成的部分：

- V2 CRUD routes
- V2 service layer
- V2 preset launch behavior
- prompt-agent 对 workflow asset refs 的真正消费逻辑
- V2 frontend selector / manager pages

## Next Actions

### Highest Priority

下一位模型接手时，最应该继续的是：

1. `V2 backend behavior`

具体顺序建议：

1. 新增 V2 API routes
   - `app/api/v1/context_packs.py`
   - `app/api/v1/evaluation_profiles.py`
   - `app/api/v1/workflow_recipes.py`
   - `app/api/v1/run_presets.py`
2. 新增对应 services
3. 将新 routers 注册到 [main.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/main.py)
4. 实现最小 CRUD
5. 再实现 `run preset launch`

### Second Priority

等 V2 backend 可用后，再做：

1. Workbench 选择 workflow assets
2. Library 页增加这四类对象管理
3. Session 页面展示 preset / recipe provenance

### Third Priority

只有在 V2 真正可用后，再进入：

- V3 schema foundation
- V3 backend behavior

### Explicitly Do Not Start Yet

在下面这些点还没完成前，不要开始：

- V4 scheduler / monitor runtime
- watchlist UI
- alert feed
- 股票专用 agent 自动化

前置条件是：

- V2 可用
- V3 workspace substrate 成型

## Master Checklist

### Phase A: Stabilize Current Foundation

- [ ] 整理当前 worktree，确认哪些改动需要提交
- [ ] 为 V2 schema foundation 增加最小单元测试或迁移测试
- [ ] 更新 README roadmap，让它和当前真实路线一致

### Phase B: V2 Backend

- [x] V2 PRD / API / schema task list
- [x] V2 schema foundation
- [ ] Context Pack CRUD routes + service
- [ ] Evaluation Profile CRUD routes + service
- [ ] Workflow Recipe CRUD routes + service
- [ ] Run Preset CRUD routes + service
- [ ] Run Preset launch endpoint
- [ ] prompt-agent 真正接收并记录 V2 refs
- [ ] prompt-sessions 列表/详情展示 provenance
- [ ] V2 backend tests

### Phase C: V2 Frontend

- [ ] Library 新增四类资产入口
- [ ] Workbench selector 接线
- [ ] Save as Run Preset UI
- [ ] Session 历史展示 preset / recipe 来源
- [ ] V2 frontend tests

### Phase D: V3 Foundation

- [x] V3 PRD / API / schema task list
- [ ] V3 schema foundation
- [ ] V3 backend CRUD
- [ ] V3 frontend workspace shell

### Phase E: V4 Foundation

- [x] V4 PRD / API / schema task list
- [ ] V4 schema foundation
- [ ] V4 monitor / run / alert backend contracts
- [ ] V4 runtime trigger design

## Canonical Docs By Phase

### V1

- [betterprompt-library-workbench-eng-execution-plan-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-library-workbench-eng-execution-plan-v1.md)
- [betterprompt-prompt-library-workbench-design-plan-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-prompt-library-workbench-design-plan-v1.md)

### V2

- [betterprompt-v2-workflow-assets-prd-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-workflow-assets-prd-v1.md)
- [betterprompt-v2-workflow-assets-api-design-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-workflow-assets-api-design-v1.md)
- [betterprompt-v2-workflow-assets-migration-schema-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v2-workflow-assets-migration-schema-task-list-v1.md)

### V3

- [betterprompt-v3-domain-workspaces-prd-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v3-domain-workspaces-prd-v1.md)
- [betterprompt-v3-domain-workspaces-api-design-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v3-domain-workspaces-api-design-v1.md)
- [betterprompt-v3-domain-workspaces-migration-schema-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v3-domain-workspaces-migration-schema-task-list-v1.md)

### V4

- [betterprompt-v4-freshness-aware-agents-prd-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v4-freshness-aware-agents-prd-v1.md)
- [betterprompt-v4-freshness-aware-agents-api-design-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v4-freshness-aware-agents-api-design-v1.md)
- [betterprompt-v4-freshness-aware-agents-migration-schema-task-list-v1.md](/Users/smy/go/just-for-test-only-once/Better-Prompt/docs/plans/betterprompt-v4-freshness-aware-agents-migration-schema-task-list-v1.md)

## Useful Commands

### Start Dev

```bash
./dev up
./dev status
./dev logs
```

### Backend Only

```bash
cd betterprompt/backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend Only

```bash
cd betterprompt/frontend
npm run dev
```

### Validate Python Imports

```bash
betterprompt/backend/.venv/bin/python -m compileall betterprompt/backend/app betterprompt/backend/alembic
```

### Validate Migrations On Temp DB

```bash
BETTERPROMPT_DATABASE_URL=sqlite+aiosqlite:////tmp/betterprompt-check.db \
betterprompt/backend/.venv/bin/alembic -c betterprompt/backend/alembic.ini upgrade head
```

## Handoff Checklist For Another Model

如果你是下一位继续开发的模型，开始前请先确认：

- [ ] 先读完本文件和对应 phase 的三份主文档
- [ ] 先看 `git status --short`，不要误回滚已有改动
- [ ] 先确认当前目标属于 `V2 / V3 / V4` 哪一层
- [ ] 先做最小正确实现，不要提前跨层
- [ ] 做完代码后至少跑一次 `compileall`
- [ ] 只要动了 migration，就跑一次临时库升级验证

## Final Reminder

这个仓库现在最需要的不是更多新方向，而是：

- 顺着既有路线继续把系统做实

优先级必须始终是：

```text
先把 V2 真实可用
-> 再把 V3 变成工作区
-> 最后才进入 V4 agent runtime
```

只要按这个顺序推进，换模型继续开发也不会乱。
