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

### V2 Backend Behavior

以下最小后端能力已经落地：

- 已新增 API routes
  - [context_packs.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/api/v1/context_packs.py)
  - [evaluation_profiles.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/api/v1/evaluation_profiles.py)
  - [workflow_recipes.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/api/v1/workflow_recipes.py)
  - [run_presets.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/api/v1/run_presets.py)
- 已新增 service layer
  - [workflow_asset_service.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/workflow_asset_service.py)
- 已注册 routers
  - [main.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/main.py)
- 已补充 V2 version/detail schemas
  - [workflow_asset.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/schemas/workflow_asset.py)
- 已补充 session 过滤能力
  - [prompt_sessions.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/api/v1/prompt_sessions.py)
  - [prompt_session_service.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/prompt_session_service.py)
  - `prompt-sessions` list/detail 现已返回
    - `run_preset_name`
    - `workflow_recipe_name`
    - `workflow_recipe_version_number`
- 已实现 `run preset launch`
  - [run_presets.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/api/v1/run_presets.py)
  - [run_preset_launch_service.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/run_preset_launch_service.py)
  - `run preset definition.mode` 现在也可作为默认 launch mode
- `prompt-agent` 已开始真实消费 workflow refs
  - [workflow_context.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/prompt_agent/workflow_context.py)
  - [orchestrator.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/prompt_agent/orchestrator.py)
  - [evaluate_engine.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/prompt_agent/evaluate_engine.py)
  - [debug_engine.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/prompt_agent/debug_engine.py)
- 已补主链路 session / iteration 持久化
  - [persistence.py](/Users/smy/go/just-for-test-only-once/Better-Prompt/betterprompt/backend/app/services/prompt_agent/persistence.py)
  - `generate / debug / evaluate / continue`
  - `generate/stream / continue/stream` 的 done event 也已返回 `session_id / iteration_id`
- 已修复本地运行时 DB 路径漂移
  - [config.py](/Users/smy/project/better-prompt/betterprompt/backend/app/core/config.py)
  - 默认 SQLite 路径已固定到 `betterprompt/backend/betterprompt.db`
  - 不再因为从 repo root / backend cwd 启动而连到不同的 `betterprompt.db`
- 已补后端启动前 schema fail-fast
  - [init_db.py](/Users/smy/project/better-prompt/betterprompt/backend/app/db/init_db.py)
  - 缺表时会在 startup 直接失败并提示运行 `alembic upgrade head`
- 已补开发脚本自动 migration
  - [betterprompt-dev.sh](/Users/smy/project/better-prompt/scripts/betterprompt-dev.sh)
  - `start` 现在会先跑 `alembic upgrade head` 再起 backend

### V2 Frontend Workbench

当前 workbench 侧已经完成第一轮接线：

- 已接入 workflow asset catalog 拉取
  - [use-workflow-asset-catalog.ts](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/hooks/use-workflow-asset-catalog.ts)
- 已接入 run preset detail / launch hooks
  - [use-run-preset-detail.ts](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/hooks/use-run-preset-detail.ts)
  - [use-run-preset-launch.ts](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/hooks/use-run-preset-launch.ts)
- Workbench 已可选择 workflow assets 并把 refs 传给 prompt-agent
  - [index.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/index.tsx)
  - [workflow-assets-panel.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/components/workflow-assets-panel.tsx)
- 结果桌面已显示 provenance
  - [result-panel.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/components/result-panel.tsx)
- continue optimization 已继承 session / iteration / workflow refs
  - [use-prompt-agent-continue.ts](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/hooks/use-prompt-agent-continue.ts)
  - [use-prompt-agent-generate-stream.ts](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/hooks/use-prompt-agent-generate-stream.ts)
- 已接入 Save as Run Preset UI
  - [workflow-assets-panel.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/components/workflow-assets-panel.tsx)
  - [index.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/index.tsx)
- 已修复 preset deeplink 绑定同步
  - [index.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/index.tsx)
  - `prompt-agent?preset=...&mode=...` 现在会把 preset 里的 recipe / profile / context pack refs 同步到当前 workbench 状态

### V2 Frontend Library

当前已经补出最小 Library 管理页：

- 已新增共享页面壳与路由
  - [app-shell.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/components/app-shell.tsx)
  - [router.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/app/router.tsx)
- 已新增 workflow library 页面
  - [index.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/workflow-library/index.tsx)
  - [page-shell.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/workflow-library/page-shell.tsx)
  - [index.test.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/workflow-library/index.test.tsx)
- 四类 V2 assets 已可：
  - 列表查看
  - 详情查看
  - 新建
  - `context pack / evaluation profile / workflow recipe` 新增版本
  - `run preset` 更新 definition
  - 当前资产类型内搜索
  - 通过 `kind / id / recipe_version / q` URL 参数 deeplink
  - 从 `run preset / workflow recipe` 直接跳到 Workbench 或 Sessions

### V2 Frontend Sessions

当前已经补出最小 Sessions / Runs 页面：

- 已新增 sessions route
  - [router.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/app/router.tsx)
- 已新增 sessions 页面
  - [index.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/session-history/index.tsx)
  - [page-shell.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/session-history/page-shell.tsx)
  - [index.test.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/session-history/index.test.tsx)
- 当前已支持：
  - `run_kind / run_preset / workflow_recipe` 过滤
  - 通过 `run_kind / run_preset_id / workflow_recipe_version_id / q` URL 参数 deeplink
  - 当前结果内本地搜索
  - session 列表查看
  - session 详情查看
  - provenance 基础字段展示
  - metadata JSON 展示
  - 优先使用后端返回的 `preset / recipe` 展示字段，不再依赖前端猜当前版本名称
  - 从 session 直接跳到 Workbench / Library 对应资产

### V2 Frontend Tests

当前已补最小前端测试基座：

- 已接入 `Vitest + jsdom`
  - [package.json](/Users/smy/project/better-prompt/betterprompt/frontend/package.json)
  - [vite.config.ts](/Users/smy/project/better-prompt/betterprompt/frontend/vite.config.ts)
- 已新增测试辅助
  - [setup.ts](/Users/smy/project/better-prompt/betterprompt/frontend/src/test/setup.ts)
  - [render.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/test/render.tsx)
- 已覆盖的高价值行为：
  - Workflow Library deeplink 进入态
  - Workflow Library quick links
  - Sessions deeplink 过滤
  - Sessions provenance quick links
  - Prompt Agent preset deeplink 绑定同步

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
- V2 workflow assets smoke 通过
  - `context pack -> evaluation profile -> workflow recipe -> run preset` 创建与读取链路通过
  - `run preset` 引用校验已实际跑通
- `run preset launch` smoke 通过
  - 可从 preset 解析 launch request
  - 可创建 `prompt_session`
  - 可写入 `prompt_iteration`
  - 可更新 `run_presets.last_used_at`
- `definition.mode` preset smoke 通过
  - [smoke_v2_preset_workflows.py](/Users/smy/project/better-prompt/scripts/smoke_v2_preset_workflows.py)
  - 已确认 `definition.mode` 会作为默认 launch mode
  - 已确认 save-as-run-preset 形状的 `generate / debug / evaluate` definitions 可被 launch service 消费
  - 已确认 `prompt_sessions` 过滤可返回对应 preset session
- stream provenance smoke 通过
  - `generate/stream` done event 已带 `session_id / iteration_id`
  - `continue/stream` 在 fake LLM client 下确认可写入 iteration 链路
- frontend TypeScript 校验通过
  - `./node_modules/.bin/tsc -p tsconfig.json --pretty false`
- frontend Vite build smoke 通过
  - `./node_modules/.bin/vite build --outDir /tmp/betterprompt-frontend-smoke`
- frontend Vitest 通过
  - `npm test`
- backend unittest 通过
  - `cd betterprompt/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_*.py'`
  - 已覆盖 `workflow assets / run preset launch / init_db fail-fast / V3 schema foundation`
- backend startup schema check 通过
  - `PYTHONPATH=/Users/smy/project/better-prompt/betterprompt/backend .venv/bin/python - <<... init_db() ...`
- V2 手工 smoke 通过
  - `Library` 能加载真实 V2 assets，并渲染 preset quick links
  - `Workbench` 能消费 `preset / mode` deeplink，preset 绑定同步已在真实页面确认
  - `Sessions` 已确认能展示 smoke preset session 与 provenance quick links
- V2 全栈自动验收脚本通过
  - [verify_v2_stack.py](/Users/smy/project/better-prompt/scripts/verify_v2_stack.py)
  - 已确认 `dev stack / backend health / frontend load / V2 assets create / preset launch / prompt_sessions provenance`
- V3 Alembic migration 通过
  - `cd betterprompt/backend && .venv/bin/alembic -c alembic.ini upgrade head`
  - 已确认 `20260318_0003_v3_domain_workspaces.py` 可接在 V2 之后执行
- V3 backend CRUD unittest 通过
  - `DomainWorkspace / WorkspaceSubject / ResearchSource / ResearchReport / ResearchReportVersion`
  - 已确认 workspace config 校验、report versioning、`workspace_run` session provenance
- V3 backend HTTP smoke 通过
  - 已确认 `domain-workspaces / subjects / sources / reports / report versions`
  - 已确认 `prompt-agent/debug` 在 workspace refs 下会落成 `workspace_run`
- V3 frontend workspace shell 通过
  - 已上线 `Workspaces` 页，接通 `domain-workspaces / subjects / sources / reports / report versions`
  - 已确认 workspace quick links 可跳到 `Workbench / Sessions`
  - 已确认 report latest version / version timeline 可直接跳回来源 `Sessions`
  - 已确认 `Prompt Agent` 会消费 `domain_workspace_id / subject_id` 并展示 workspace provenance
  - 已确认 `Sessions` 能按 `workspace_run / domain_workspace_id / subject_id` 过滤，并跳回 `Workspaces / Workbench`
- V3 frontend TypeScript 校验通过
  - `cd betterprompt/frontend && ./node_modules/.bin/tsc -p tsconfig.json --pretty false`
- V3 frontend Vitest 通过
  - `cd betterprompt/frontend && npm test`
  - 已补 [prompt-agent/index.test.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/prompt-agent/index.test.tsx)
  - 已补 [workspace-shell/index.test.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/workspace-shell/index.test.tsx)
  - 已补 [session-history/index.test.tsx](/Users/smy/project/better-prompt/betterprompt/frontend/src/features/session-history/index.test.tsx)
  - 已确认 `Prompt Agent` 在 `workspace + workflow refs` deeplink 下，直接 `Debug` 提交会把 provenance payload 带进 hook
  - 已确认 `Run Preset launch -> Continue Optimization` 会继承 `session / iteration / workspace / workflow refs`
  - 已确认 `Workspace` report/version provenance quick links 会跳回来源 `Sessions`
  - 已确认 `Sessions` 会展示 `agent_run / agent_monitor_id / trigger_kind`，并保留 Workbench quick links
- V3 frontend Vite build smoke 通过
  - `cd betterprompt/frontend && ./node_modules/.bin/vite build --outDir /tmp/betterprompt-frontend-smoke`
- V3 frontend manual smoke 通过
  - 已在临时 `8003 / 5177` 栈上确认 `Workspaces -> Workbench -> Sessions` 真实页面链路
  - 已确认 workspace detail、report timeline、workbench workspace focus、sessions provenance quick links 都能显示真实 smoke 数据
- V3 全栈自动验收脚本通过
  - [verify_v3_stack.py](/Users/smy/project/better-prompt/scripts/verify_v3_stack.py)
  - 已确认健康本地栈发现会优先命中真正暴露 `domain-workspaces` 的 V3 backend
  - 已确认 `workspace -> subject -> source -> report -> report version -> prompt-agent/debug -> prompt-sessions`
  - 已确认 frontend `workspaces / prompt-agent / sessions` workspace deeplink 路径都能返回页面
- V4 schema foundation 通过
  - 已新增 `watchlists / watchlist_items / agent_monitors / agent_runs / agent_alerts / freshness_records`
  - 已扩展 `prompt_sessions.agent_monitor_id / trigger_kind`
  - 已新增 [agent_runtime.py](/Users/smy/project/better-prompt/betterprompt/backend/app/schemas/agent_runtime.py)
  - 已确认 Alembic `20260319_0004_v4_freshness_agents.py` 可接在 V3 后执行
- V4 backend unittest 通过
  - `cd betterprompt/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_*.py'`
  - 已确认 V4 metadata tables、runtime CRUD/list contracts 与 prompt-session agent provenance round-trip
- V4 backend compileall 通过
  - `cd betterprompt/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m compileall app tests`
- V4 Alembic migration 通过
  - `cd betterprompt/backend && .venv/bin/alembic -c alembic.ini upgrade head`
- V4 backend contracts 通过
  - 已新增 [agent_runtime_service.py](/Users/smy/project/better-prompt/betterprompt/backend/app/services/agent_runtime_service.py) 与 [agent_runtime.py](/Users/smy/project/better-prompt/betterprompt/backend/app/api/v1/agent_runtime.py)
  - 已接通 `watchlists / watchlist items / agent monitors / agent runs / agent alerts / freshness records`
  - 已确认 `agent_monitor trigger -> agent_run -> prompt_session` provenance 链路
  - 已新增 [test_v4_backend_contracts.py](/Users/smy/project/better-prompt/betterprompt/backend/tests/test_v4_backend_contracts.py)
- V4 HTTP smoke 脚本通过
  - [verify_v4_backend_contracts.py](/Users/smy/project/better-prompt/scripts/verify_v4_backend_contracts.py)
  - 已确认 `workspace -> subject -> watchlist -> monitor -> agent run -> prompt sessions` 真实接口链路
  - 已确认 `watchlists / agent-monitors / agent-runs / agent-alerts / freshness-records` 路径均可返回有效契约响应
- V4 runtime trigger design 通过
  - 已让 `agent_monitor` 手动 trigger 真实执行 `run_preset -> prompt_agent`
  - 已确认 `agent_run` 会回填 `running/completed/failed`、`prompt_session_id`、`prompt_iteration_id`
  - 已确认 `prompt_session.run_kind=agent_run`、`agent_monitor_id`、`trigger_kind` 不会被后续 persistence 覆盖丢失
  - 已补 `trigger failure` 回归，确保无 `run_preset_id` 的 monitor 也会留下 `failed` run 记录

## Current In Progress

当前真正进入开发阶段的点是：

- `V3` 更完整的前后端集成 / 回归测试

当前还没有完成的部分：

- 暂无阻塞 `V2 / V3` 主链路的未完成项

## Next Actions

### Highest Priority

下一位模型接手时，最应该继续的是：

1. `V3` 补更完整的前后端集成 / 回归测试
2. 只在产品目标明确后，再继续 `V4 scheduler / freshness / alert production` 设计

具体顺序建议：

1. 补 `V3 Workspaces / Workbench / Sessions` 的更完整 HTTP / UI 集成回归
2. 收口 `prompt-sessions` 在 V2/V3/V4 三条链路上的 provenance 展示契约
3. 保持 `V4 scheduler / monitor runtime`、`watchlist UI`、`alert feed` 继续冻结，直到目标重新确认

### Second Priority

等 V2 backend 可用后，再做：

1. 补后端 / 前端集成测试
2. 收口 prompt-sessions provenance 展示契约
3. 再开始 V3 schema foundation

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
- [x] 更新 README roadmap，让它和当前真实路线一致

### Phase B: V2 Backend

- [x] V2 PRD / API / schema task list
- [x] V2 schema foundation
- [x] Context Pack CRUD routes + service
- [x] Evaluation Profile CRUD routes + service
- [x] Workflow Recipe CRUD routes + service
- [x] Run Preset CRUD routes + service
- [x] Run Preset launch endpoint
- [x] prompt-agent 真正接收并记录 V2 refs
- [x] prompt-sessions 列表/详情展示 provenance
- [x] V2 backend tests

### Phase C: V2 Frontend

- [x] Library 新增四类资产入口
- [x] Workbench selector 接线
- [x] Workbench run preset launch / provenance
- [x] Save as Run Preset UI
- [x] Session 历史展示 preset / recipe 来源
- [x] V2 frontend tests
- [x] Library / Workbench / Sessions 手工 smoke

### Phase D: V3 Foundation

- [x] V3 PRD / API / schema task list
- [x] V3 schema foundation
- [x] V3 backend CRUD
- [x] V3 frontend workspace shell

### Phase E: V4 Foundation

- [x] V4 PRD / API / schema task list
- [x] V4 schema foundation
- [x] V4 monitor / run / alert backend contracts
- [x] V4 runtime trigger design

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

### V2 Preset Workflow Smoke

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Users/smy/project/better-prompt/betterprompt/backend \
betterprompt/backend/.venv/bin/python scripts/smoke_v2_preset_workflows.py
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
