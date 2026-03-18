# BetterPrompt V4 Freshness-Aware Agents API Design v1

## 1. 文档目标

本文定义 `V4 Freshness-Aware Agents` 的 API 设计边界。

目标是明确：

1. watchlist / monitor / run / alert / freshness 的资源接口
2. 对 `prompt-sessions` 的最小扩展
3. 哪些 agent 行为必须可追溯

## 2. 设计原则

### 2.1 Agent Runtime 是显式资源，不是隐式后台黑盒

V4 必须把这些对象暴露为清晰资源：

- `watchlists`
- `agent-monitors`
- `agent-runs`
- `agent-alerts`
- `freshness-records`

### 2.2 运行记录优先于对话体验

任何一次 rerun，都应能查到：

- 为什么触发
- 何时触发
- 运行结果是什么
- 触发后有什么变化

### 2.3 Session 仍是底层执行主干

agent run 不替代 `prompt_sessions`。

更合理的关系是：

- `agent_run -> prompt_session -> prompt_iterations`

## 3. 资源总览

```text
/api/v1/watchlists
/api/v1/watchlists/{watchlist_id}/items
/api/v1/agent-monitors
/api/v1/agent-monitors/{monitor_id}/runs
/api/v1/agent-runs/{run_id}
/api/v1/agent-alerts
/api/v1/freshness-records

/api/v1/prompt-sessions/*
  + agent provenance
```

## 4. Watchlists API

## 4.1 获取列表

### `GET /api/v1/watchlists`

支持查询参数：

- `workspace_id`

## 4.2 创建

### `POST /api/v1/watchlists`

#### Request

```json
{
  "workspace_id": "workspace_uuid",
  "name": "美股核心观察",
  "description": "重点跟踪高权重科技股"
}
```

## 4.3 更新

### `PATCH /api/v1/watchlists/{watchlist_id}`

## 4.4 添加 item

### `POST /api/v1/watchlists/{watchlist_id}/items`

```json
{
  "subject_id": "subject_uuid"
}
```

## 5. Agent Monitors API

## 5.1 获取列表

### `GET /api/v1/agent-monitors`

支持查询参数：

- `workspace_id`
- `subject_id`
- `status`

## 5.2 创建

### `POST /api/v1/agent-monitors`

#### Request

```json
{
  "workspace_id": "workspace_uuid",
  "watchlist_id": "watchlist_uuid",
  "subject_id": null,
  "run_preset_id": "preset_uuid",
  "workflow_recipe_version_id": "wrv_uuid",
  "monitor_type": "schedule",
  "trigger_config": {
    "cadence": "daily"
  },
  "alert_policy": {
    "only_material_change": true
  }
}
```

## 5.3 更新

### `PATCH /api/v1/agent-monitors/{monitor_id}`

允许更新：

- `status`
- `trigger_config`
- `alert_policy`

## 5.4 手动触发

### `POST /api/v1/agent-monitors/{monitor_id}/trigger`

用途：

- 手动触发一次 rerun

## 6. Agent Runs API

## 6.1 获取 monitor 下的 runs

### `GET /api/v1/agent-monitors/{monitor_id}/runs`

## 6.2 获取 run 详情

### `GET /api/v1/agent-runs/{run_id}`

返回应包含：

- `trigger_kind`
- `run_status`
- `prompt_session_id`
- `prompt_iteration_id`
- `input_freshness`
- `change_summary`
- `conclusion_summary`

## 7. Agent Alerts API

## 7.1 获取 alert feed

### `GET /api/v1/agent-alerts`

支持查询参数：

- `workspace_id`
- `subject_id`
- `status`

## 7.2 标记已读

### `PATCH /api/v1/agent-alerts/{alert_id}`

允许更新：

- `status`

## 8. Freshness Records API

## 8.1 查询 freshness

### `GET /api/v1/freshness-records`

支持查询参数：

- `workspace_id`
- `subject_id`
- `source_id`
- `status`

说明：

- freshness records 主要由系统内部产生
- 对外优先提供查询接口

## 9. Prompt Sessions API 扩展

V4 建议在 `prompt_sessions` 上增加：

- `agent_monitor_id`
- `trigger_kind`
- `run_kind=agent_run`

### `GET /api/v1/prompt-sessions`

新增过滤参数：

- `agent_monitor_id`
- `trigger_kind`

### `GET /api/v1/prompt-sessions/{session_id}`

新增返回字段：

- `agent_monitor_id`
- `trigger_kind`

## 10. 错误码建议

```text
WATCHLIST_NOT_FOUND
WATCHLIST_ITEM_NOT_FOUND
AGENT_MONITOR_NOT_FOUND
AGENT_MONITOR_TRIGGER_INVALID
AGENT_RUN_NOT_FOUND
AGENT_ALERT_NOT_FOUND
FRESHNESS_RECORD_NOT_FOUND
AGENT_TRIGGER_FAILED
AGENT_RUN_DIFF_INVALID
```

## 11. 最终判断

V4 API 的核心不在“多智能”，而在“可追溯”。

所以最重要的不是让 monitor 看起来聪明，而是让所有 rerun、diff、alert 都能被明确记录和追查。
