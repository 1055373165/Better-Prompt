# 《BetterPrompt Sprint 2 实施任务单 v1》

## 1. Sprint 目标

Sprint 2 的目标是从“工程可运行”升级到“主流程可用”。

Sprint 2 结束时，项目应满足：

- **session 主流程接口成型**
- **generate/debug/evaluate/continue 具备后端接口骨架**
- **session 与 iteration 落库完整**
- **前端工作台可以驱动主流程请求**
- **可查看某个 session 的 iteration 结果**

## 2. Sprint 范围

本 Sprint 覆盖：

- `prompt_sessions` 资源化接口
- `prompt_iterations` 落库链路
- generate/debug/evaluate/continue schema 与接口实现
- 前端工作台与 session 接口联调
- session 详情页基础展示

本 Sprint 不覆盖：

- 正式 auth 完成
- Prompt 资产页面完整版本
- 模板系统
- 计费能力
- 完整多 provider 策略

## 3. Sprint 成功标准

- 可创建 session
- 可在 session 内发起 generate/debug/evaluate/continue
- 每次操作都生成一条 iteration
- session 详情可展示 iteration 列表
- 前端工作台可完成主流程演示

## 4. 任务拆解

### A. 后端 Session API

#### A1. 创建 session 接口

- `POST /api/v1/prompt-sessions`
- `GET /api/v1/prompt-sessions/{id}`
- `GET /api/v1/prompt-sessions`

#### A2. Session 内动作接口

- `POST /api/v1/prompt-sessions/{id}/generate`
- `POST /api/v1/prompt-sessions/{id}/debug`
- `POST /api/v1/prompt-sessions/{id}/evaluate`
- `POST /api/v1/prompt-sessions/{id}/continue`

### B. 后端数据落库

#### B1. iteration 创建逻辑

- 每次调用主流程接口都创建一条 iteration
- 写入 `mode`
- 写入 `input_payload_json`
- 写入 `output_payload_json`
- 更新 `prompt_sessions.latest_iteration_id`

#### B2. continue 链路

- 支持 `parent_iteration_id`
- 正确建立版本链关系

### C. 领域逻辑对接

#### C1. 先保留现有 rule/template engine 作为过渡实现

- 允许继续使用当前 generate/debug/evaluate/continue 的规则逻辑
- 但必须包进新的 session/iteration 流程中

#### C2. 抽出统一 workflow service

建议建立：

- `PromptWorkflowService`

负责：

- 接口请求编排
- iteration 创建
- 结果保存
- response 输出

### D. 前端工作台联调

#### D1. 创建 session

- 工作台初次进入时可创建 session
- 或在首次提交时懒创建 session

#### D2. 主流程请求接入

- Generate 面板接入 session API
- Debug 面板接入 session API
- Evaluate 面板接入 session API
- Continue 操作接入 session API

#### D3. Session 详情基础展示

- 展示 session 标题
- 展示 latest result
- 展示 iteration 时间线简表

## 5. 交付物

- Session API 初版
- Generate/Debug/Evaluate/Continue session 化接口
- Iteration 落库能力
- 前端工作台联调完成
- Session 详情基础页

## 6. 验收标准

### 后端

- 可以创建 session
- 可以查询 session
- 主流程接口均能创建 iteration
- continue 能记录 parent iteration

### 前端

- 可从工作台发起主流程请求
- 请求结果可展示
- 可以查看某个 session 的历史 iteration

### 数据层

- `prompt_sessions` 与 `prompt_iterations` 数据关系正确
- `latest_iteration_id` 能正确更新

## 7. 风险与注意事项

- 不要在 Sprint 2 过早重做全部 prompt engine
- 不要把 session 创建逻辑散落在前端多个组件里
- 不要让 continue 脱离 iteration 链路单独存在
- 不要为了赶进度跳过数据落库，否则 Sprint 3 会返工

## 8. 建议交付顺序

1. Session schema 和 repository
2. Session API
3. iteration 写入逻辑
4. Generate/Debug/Evaluate/Continue 接口改造成 session 内动作
5. 前端联调
6. Session 详情页

## 9. Sprint 2 结束产物清单

- `prompt_sessions` API
- `prompt_iterations` 读写链路
- 主流程 session 化
- 工作台联调
- session 详情基础页

## 10. 完成定义

当以下全部满足时，Sprint 2 可关闭：

- session 主流程跑通
- iteration 可追踪
- continue 有版本链
- 前端能完整演示主流程
- 为 Sprint 3 的 asset/template 扩展打好接口与数据基础
