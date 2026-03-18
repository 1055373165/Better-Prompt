# BetterPrompt V3 Domain Workspaces API Design v1

## 1. 文档目标

本文定义 `V3 Domain Workspaces` 的 API 边界。

目标是明确：

1. 新增哪些 workspace 资源
2. 现有 `prompt-agent` 与 `prompt-sessions` 需要怎样扩展
3. 哪些接口明确留给 `V4`

## 2. 设计原则

### 2.1 Workspace-first

V3 的核心资源是 `domain-workspaces`，其他对象围绕它展开。

### 2.2 领域对象嵌套表达

以下资源推荐采用“workspace 下挂载”的表达方式：

- subjects
- sources
- reports

### 2.3 执行仍复用 prompt-agent

V3 不应新造自己的生成引擎。

工作区内发起运行，底层仍应走：

- `/api/v1/prompt-agent/*`

### 2.4 V3 不引入 agent runtime API

这些接口留给 V4：

- watchlists
- agent-monitors
- agent-runs
- agent-alerts

## 3. 资源总览

```text
/api/v1/domain-workspaces
/api/v1/domain-workspaces/{workspace_id}/subjects
/api/v1/domain-workspaces/{workspace_id}/sources
/api/v1/domain-workspaces/{workspace_id}/reports
/api/v1/research-reports/{report_id}/versions

/api/v1/prompt-agent/*
  + optional workspace refs

/api/v1/prompt-sessions/*
  + workspace / subject provenance
```

## 4. Domain Workspaces API

## 4.1 获取工作区列表

### `GET /api/v1/domain-workspaces`

支持查询参数：

- `workspace_type`
- `page`
- `page_size`

## 4.2 创建工作区

### `POST /api/v1/domain-workspaces`

#### Request

```json
{
  "workspace_type": "stock_analysis",
  "name": "美股核心观察",
  "description": "跟踪核心科技股",
  "config": {
    "default_run_preset_id": null,
    "default_recipe_version_id": null
  }
}
```

## 4.3 获取详情

### `GET /api/v1/domain-workspaces/{workspace_id}`

返回：

- workspace meta
- config
- high-level counts

## 4.4 更新

### `PATCH /api/v1/domain-workspaces/{workspace_id}`

允许更新：

- `name`
- `description`
- `config`
- `archived_at`

## 5. Subjects API

## 5.1 获取 subject 列表

### `GET /api/v1/domain-workspaces/{workspace_id}/subjects`

支持查询参数：

- `subject_type`
- `q`

## 5.2 创建 subject

### `POST /api/v1/domain-workspaces/{workspace_id}/subjects`

#### Request

```json
{
  "subject_type": "ticker",
  "external_key": "AAPL",
  "display_name": "Apple"
}
```

## 5.3 更新 subject

### `PATCH /api/v1/workspace-subjects/{subject_id}`

允许更新：

- `display_name`
- `metadata`
- `status`

## 6. Sources API

## 6.1 获取 source 列表

### `GET /api/v1/domain-workspaces/{workspace_id}/sources`

支持查询参数：

- `subject_id`
- `source_type`
- `page`
- `page_size`

## 6.2 创建 source

### `POST /api/v1/domain-workspaces/{workspace_id}/sources`

#### Request

```json
{
  "subject_id": "subject_uuid",
  "source_type": "url",
  "canonical_uri": "https://example.com/report",
  "title": "Q2 earnings call notes",
  "content": {
    "summary": "...",
    "body": "...",
    "structured_fields": {}
  },
  "source_timestamp": "2026-03-18T00:00:00Z"
}
```

## 6.3 更新 source

### `PATCH /api/v1/research-sources/{source_id}`

## 7. Reports API

## 7.1 获取 report 列表

### `GET /api/v1/domain-workspaces/{workspace_id}/reports`

支持查询参数：

- `subject_id`
- `report_type`
- `page`
- `page_size`

## 7.2 创建 report

### `POST /api/v1/domain-workspaces/{workspace_id}/reports`

#### Request

```json
{
  "subject_id": "subject_uuid",
  "report_type": "equity_thesis",
  "title": "Apple investment thesis",
  "content": {
    "thesis": "...",
    "bull_case": [],
    "bear_case": [],
    "key_risks": [],
    "evidence_refs": []
  },
  "source_session_id": "session_uuid",
  "source_iteration_id": "iteration_uuid",
  "summary_text": "核心观点摘要"
}
```

## 7.3 获取详情

### `GET /api/v1/research-reports/{report_id}`

## 7.4 更新 report 元数据

### `PATCH /api/v1/research-reports/{report_id}`

## 7.5 获取版本列表

### `GET /api/v1/research-reports/{report_id}/versions`

## 7.6 创建 report 新版本

### `POST /api/v1/research-reports/{report_id}/versions`

## 8. Prompt Agent API 扩展

V3 在 V2 refs 基础上，再增加：

- `domain_workspace_id`
- `subject_id`

适用接口：

- `POST /api/v1/prompt-agent/generate`
- `POST /api/v1/prompt-agent/debug`
- `POST /api/v1/prompt-agent/evaluate`
- `POST /api/v1/prompt-agent/continue`
- 对应 streaming 接口

## 9. Prompt Sessions API 扩展

### `GET /api/v1/prompt-sessions`

新增过滤参数：

- `domain_workspace_id`
- `subject_id`
- `run_kind=workspace_run`

### `GET /api/v1/prompt-sessions/{session_id}`

新增返回字段：

- `domain_workspace_id`
- `subject_id`

## 10. 错误码建议

```text
DOMAIN_WORKSPACE_NOT_FOUND
WORKSPACE_SUBJECT_NOT_FOUND
RESEARCH_SOURCE_NOT_FOUND
RESEARCH_REPORT_NOT_FOUND
RESEARCH_REPORT_VERSION_NOT_FOUND
WORKSPACE_SOURCE_INVALID
WORKSPACE_RUN_INVALID
```

## 11. V3 明确不做的 API

- `/watchlists/*`
- `/agent-monitors/*`
- `/agent-runs/*`
- `/agent-alerts/*`
- `/freshness-records/*`

这些明确属于 V4。

## 12. 最终判断

V3 的 API 不是为了让 BetterPrompt 更像“工具箱”，而是为了让它开始像“工作区”。

但这层仍然应建立在：

- 现有 prompt-agent 执行主干
- V2 workflow assets

之上，而不是平行重建一套系统。
