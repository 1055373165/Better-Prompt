# BetterPrompt V2 Workflow Assets API Design v1

## 1. 文档目标

本文定义 `V2 Workflow Assets` 的后端 API 设计方向。

目标是为后续实现提供三类清晰约束：

1. 新增哪些资源 API
2. 现有 `prompt-agent` 与 `prompt-sessions` 需要做哪些最小扩展
3. 哪些接口和行为明确不属于 V2

## 2. 设计原则

### 2.1 资源优先

V2 的新增对象都应是清晰资源，而不是塞进一个大而全的 `/workflow` 接口。

新增资源面：

- `context-packs`
- `evaluation-profiles`
- `workflow-recipes`
- `run-presets`

### 2.2 保持执行主干不变

V2 不应新造一套完全独立的执行 API。

执行主干继续使用现有：

- `/api/v1/prompt-agent/*`
- `/api/v1/prompt-sessions/*`

V2 只是在这些请求中增加 workflow asset references。

### 2.3 版本显式

凡是会影响运行结果的可复用对象，启动时都应引用：

- 具体 version id

而不是：

- “当前版本”

### 2.4 响应风格与当前实现保持一致

当前代码中的 `prompt-agent` 接口直接返回 `response_model`，不是统一 envelope。

因此 V2 建议继续沿用当前风格：

- 单对象响应直接返回对象
- 列表响应使用 `{ "items": [...] }`

不要在 V2 同时引入 API 风格大改。

## 3. 资源总览

```text
/api/v1/context-packs
/api/v1/evaluation-profiles
/api/v1/workflow-recipes
/api/v1/run-presets

/api/v1/prompt-agent/*
  + optional V2 refs

/api/v1/prompt-sessions/*
  + V2 filters and provenance fields
```

## 4. 通用约定

### Base Path

```text
/api/v1
```

### Content-Type

```text
application/json
```

### 列表查询参数约定

所有新增列表接口建议支持：

- `page`
- `page_size`
- `q`
- `archived`

其中：

- `archived=false` 默认只返回未归档对象

## 5. Context Packs API

## 5.1 获取列表

### `GET /api/v1/context-packs`

支持查询参数：

- `page`
- `page_size`
- `q`

#### Response

```json
{
  "items": [
    {
      "id": "cp_123",
      "name": "A股公司研究基础包",
      "description": "行业背景、风险口径和写作风格",
      "current_version": {
        "id": "cpv_001",
        "version_number": 3,
        "created_at": "2026-03-18T00:00:00Z"
      },
      "updated_at": "2026-03-18T00:00:00Z"
    }
  ]
}
```

## 5.2 创建

### `POST /api/v1/context-packs`

#### Request

```json
{
  "name": "A股公司研究基础包",
  "description": "行业背景、风险口径和写作风格",
  "payload": {
    "sections": [],
    "facts": [],
    "assumptions": [],
    "style_rules": [],
    "notes": []
  },
  "source_iteration_id": null,
  "change_summary": "初始版本"
}
```

#### Response

返回新建的 detail 对象，并带 `current_version`。

## 5.3 获取详情

### `GET /api/v1/context-packs/{context_pack_id}`

返回：

- root object
- current version summary

## 5.4 更新元数据

### `PATCH /api/v1/context-packs/{context_pack_id}`

允许更新：

- `name`
- `description`
- `archived_at`

不允许直接在 root object 上修改 payload。

## 5.5 获取版本列表

### `GET /api/v1/context-packs/{context_pack_id}/versions`

#### Response

```json
{
  "items": [
    {
      "id": "cpv_003",
      "version_number": 3,
      "change_summary": "补充公司分析风格规则",
      "created_at": "2026-03-18T00:00:00Z"
    }
  ]
}
```

## 5.6 创建新版本

### `POST /api/v1/context-packs/{context_pack_id}/versions`

#### Request

```json
{
  "payload": {
    "sections": [],
    "facts": [],
    "assumptions": [],
    "style_rules": [],
    "notes": []
  },
  "source_iteration_id": "iteration_uuid",
  "change_summary": "补充两条写作风格规则"
}
```

创建后：

- 新版本成为 `current_version_id`

## 6. Evaluation Profiles API

接口结构与 `context-packs` 平行。

## 6.1 获取列表

### `GET /api/v1/evaluation-profiles`

## 6.2 创建

### `POST /api/v1/evaluation-profiles`

#### Request

```json
{
  "name": "研究结论严谨性标准",
  "description": "强调证据、反方与风险揭示",
  "rules": {
    "criteria": [],
    "weights": {},
    "pass_threshold": 0.75,
    "strictness": "balanced",
    "failure_conditions": [],
    "output_requirements": {}
  },
  "change_summary": "初始版本"
}
```

## 6.3 获取详情

### `GET /api/v1/evaluation-profiles/{evaluation_profile_id}`

## 6.4 更新元数据

### `PATCH /api/v1/evaluation-profiles/{evaluation_profile_id}`

## 6.5 获取版本列表

### `GET /api/v1/evaluation-profiles/{evaluation_profile_id}/versions`

## 6.6 创建新版本

### `POST /api/v1/evaluation-profiles/{evaluation_profile_id}/versions`

## 7. Workflow Recipes API

接口结构同样与前两类 versioned assets 保持平行。

## 7.1 获取列表

### `GET /api/v1/workflow-recipes`

支持附加查询参数：

- `domain_hint`

## 7.2 创建

### `POST /api/v1/workflow-recipes`

#### Request

```json
{
  "name": "生成-评估-继续优化",
  "description": "适合复杂分析 Prompt 的默认流程",
  "domain_hint": "general_research",
  "definition": {
    "steps": [
      { "mode": "generate" },
      { "mode": "evaluate" },
      { "mode": "continue", "target": "generate_result" }
    ],
    "required_inputs": [],
    "default_output_schema": {},
    "supports_continue": true,
    "model_policy": {}
  },
  "change_summary": "初始版本"
}
```

## 7.3 获取详情

### `GET /api/v1/workflow-recipes/{workflow_recipe_id}`

## 7.4 更新元数据

### `PATCH /api/v1/workflow-recipes/{workflow_recipe_id}`

## 7.5 获取版本列表

### `GET /api/v1/workflow-recipes/{workflow_recipe_id}/versions`

## 7.6 创建新版本

### `POST /api/v1/workflow-recipes/{workflow_recipe_id}/versions`

## 8. Run Presets API

`run_presets` 在 V2 不做 version table。

原因：

- 它更像启动绑定对象
- 生命周期更偏配置
- 真正需要版本化的是它引用的资产版本，而不是 preset 自己

## 8.1 获取列表

### `GET /api/v1/run-presets`

#### Response

```json
{
  "items": [
    {
      "id": "rp_001",
      "name": "公司研究默认运行",
      "description": "Prompt + 基础上下文 + 严谨性评估",
      "last_used_at": "2026-03-18T00:00:00Z",
      "updated_at": "2026-03-18T00:00:00Z"
    }
  ]
}
```

## 8.2 创建

### `POST /api/v1/run-presets`

#### Request

```json
{
  "name": "公司研究默认运行",
  "description": "Prompt + 基础上下文 + 严谨性评估",
  "definition": {
    "prompt_asset_version_id": "pav_001",
    "context_pack_version_ids": ["cpv_001", "cpv_002"],
    "evaluation_profile_version_id": "epv_001",
    "workflow_recipe_version_id": "wrv_001",
    "output_format": {},
    "run_settings": {}
  }
}
```

## 8.3 获取详情

### `GET /api/v1/run-presets/{run_preset_id}`

返回：

- preset metadata
- definition refs

## 8.4 更新

### `PATCH /api/v1/run-presets/{run_preset_id}`

允许更新：

- `name`
- `description`
- `definition`
- `archived_at`

## 8.5 启动 Preset

### `POST /api/v1/run-presets/{run_preset_id}/launch`

这是 V2 中最重要的便捷接口。

#### Request

```json
{
  "mode_override": null,
  "user_input_override": null,
  "run_settings_override": {}
}
```

#### Behavior

- 读取 preset
- 校验全部引用版本存在
- 生成或复用 session
- 调用对应 `prompt-agent` 能力
- 返回与目标 mode 相同的 response shape

### 关键约束

`launch` 是便捷入口，不应变成新的独立执行引擎。

## 9. Prompt Agent API 扩展

V2 需要在现有四类请求中加入 workflow asset refs。

## 9.1 Generate 扩展

### `POST /api/v1/prompt-agent/generate`

在现有字段上新增可选字段：

```json
{
  "session_id": null,
  "source_asset_version_id": null,
  "context_pack_version_ids": [],
  "evaluation_profile_version_id": null,
  "workflow_recipe_version_id": null,
  "run_preset_id": null
}
```

### 设计说明

- `session_id`: 允许继续写入既有 session
- `source_asset_version_id`: 表示本次运行从哪一个 Prompt 资产版本开始
- 其余字段为 V2 workflow refs

## 9.2 Debug 扩展

### `POST /api/v1/prompt-agent/debug`

新增相同 refs 字段：

- `session_id`
- `source_asset_version_id`
- `context_pack_version_ids`
- `evaluation_profile_version_id`
- `workflow_recipe_version_id`
- `run_preset_id`

## 9.3 Evaluate 扩展

### `POST /api/v1/prompt-agent/evaluate`

新增可选字段：

- `session_id`
- `evaluation_profile_version_id`
- `workflow_recipe_version_id`
- `run_preset_id`

## 9.4 Continue 扩展

### `POST /api/v1/prompt-agent/continue`

新增可选字段：

- `session_id`
- `parent_iteration_id`
- `source_asset_version_id`
- `context_pack_version_ids`
- `evaluation_profile_version_id`
- `workflow_recipe_version_id`
- `run_preset_id`

### 说明

当前 schema 中 `ContinuePromptRequest` 尚未显式包含 `parent_iteration_id`。

V2 建议补上，因为：

- preset/recipe 驱动下，continue 的来源链应可追踪

## 9.5 Streaming 接口

以下接口与对应非 streaming 接口共享相同请求 schema：

- `POST /api/v1/prompt-agent/generate/stream`
- `POST /api/v1/prompt-agent/continue/stream`

## 10. Prompt Sessions API 扩展

V2 不应把 session 变成 workflow asset 的主对象，但要让 session 能表达来源。

## 10.1 Session 列表过滤

### `GET /api/v1/prompt-sessions`

建议新增查询参数：

- `run_kind`
- `run_preset_id`
- `workflow_recipe_version_id`

### `run_kind` 推荐值

```text
manual_workbench
preset_run
```

## 10.2 Session 详情扩展

### `GET /api/v1/prompt-sessions/{session_id}`

应在返回中补充：

- `run_kind`
- `run_preset_id`
- `workflow_recipe_version_id`

可选补充：

- `provenance_summary`

用于前端直接展示：

- 本次运行来自哪个 preset
- 使用了哪套 workflow recipe

## 11. 错误码建议

V2 新增接口建议统一补这些业务错误：

```text
CONTEXT_PACK_NOT_FOUND
CONTEXT_PACK_VERSION_NOT_FOUND
EVALUATION_PROFILE_NOT_FOUND
EVALUATION_PROFILE_VERSION_NOT_FOUND
WORKFLOW_RECIPE_NOT_FOUND
WORKFLOW_RECIPE_VERSION_NOT_FOUND
RUN_PRESET_NOT_FOUND
RUN_PRESET_REFERENCE_INVALID
WORKFLOW_RECIPE_DEFINITION_INVALID
RUN_PRESET_LAUNCH_INVALID
```

### 错误原则

- 明确指出是哪个资源引用失效
- 不要 silently fallback
- 不要把业务错误都折叠成 500

## 12. V2 明确不做的 API

以下接口不属于 V2：

- `/domain-workspaces/*`
- `/watchlists/*`
- `/agent-monitors/*`
- `/agent-runs/*`
- `/agent-alerts/*`

这些都属于后续 `V3 / V4`。

## 13. 最终判断

V2 的 API 设计应坚持一个核心原则：

- 新增的是“可复用配置资源”
- 不是“第二套执行系统”

因此最好的做法不是重新设计一整层 orchestration API，而是：

- 增加 versioned workflow assets
- 扩展现有 `prompt-agent` 请求
- 让 `prompt-sessions` 带上足够的 provenance 信息

这样 V2 才能在最小正确架构下成立。 
