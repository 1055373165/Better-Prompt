# 《BetterPrompt Sprint 3 实施任务单 v1》

## 1. Sprint 目标

Sprint 3 的目标是从“主流程可用”升级到“结果可沉淀、历史可复用、产品结构开始成型”。

Sprint 3 结束时，项目应满足：

- **可将 iteration 保存为 Prompt 资产**
- **Prompt 资产具备基础版本能力**
- **Session 详情页具备更完整的历史展示能力**
- **可从历史结果进入资产沉淀路径**
- **为模板系统接入预留稳定边界**

## 2. Sprint 范围

本 Sprint 覆盖：

- `prompt_assets` 与 `prompt_asset_versions` 落地
- 从 iteration 保存为 asset 的主流程
- 资产详情与版本基础展示
- Session 详情页增强
- 历史结果到资产的转化入口
- 模板能力的接口预留与边界设计

本 Sprint 不覆盖：

- 完整模板系统上线
- 正式计费与额度系统
- 团队协作能力
- 多 provider 智能路由增强
- 完整权限矩阵

## 3. Sprint 成功标准

- 用户可从某次 generate/debug/continue 结果保存为 asset
- asset 至少支持一个初始版本与后续追加版本
- 用户可查看 asset 列表和 asset 详情
- session 详情页可以清晰查看 iteration 历史与关键结果
- 模板能力的接口和数据边界明确，但可以先不完全开放 UI

## 4. 任务拆解

### A. 数据层：资产模型落地

#### A1. 建立资产表与版本表

- 建立 `prompt_assets`
- 建立 `prompt_asset_versions`
- 增加必要索引与唯一约束

#### A2. 资产关系补齐

- `prompt_assets.source_session_id`
- `prompt_asset_versions.source_iteration_id`
- 可选维护 `current_version_id`

**交付物**

- 资产相关 migration
- ORM 模型
- repository 初版

**验收标准**

- asset 与 version 可正常写入
- version 编号可正确递增

### B. 后端：资产接口与服务

#### B1. 创建 asset

实现：

- `POST /api/v1/prompt-assets`

支持从 iteration 创建 asset：

- 输入 `source_iteration_id`
- 输入 `name`
- 输入 `description`
- 输入 `artifact_type`
- 输入 `content`

#### B2. 资产查询

实现：

- `GET /api/v1/prompt-assets`
- `GET /api/v1/prompt-assets/{id}`

#### B3. 资产版本追加

实现：

- `POST /api/v1/prompt-assets/{id}/versions`

#### B4. 收藏与基础更新

可选实现：

- `PATCH /api/v1/prompt-assets/{id}`

至少支持：

- 重命名
- 描述更新
- `is_favorite` 更新

**交付物**

- Asset service
- Asset repository
- Asset router
- Version create logic

**验收标准**

- 可从 iteration 成功创建 asset
- 可读取 asset 和最新 version
- 可追加新版本

### C. 前端：资产入口与页面

#### C1. 从结果保存为资产

在以下区域增加入口：

- Result Panel
- Session Detail 中的 iteration 节点

支持：

- 输入 asset 名称
- 输入描述
- 选择 artifact_type
- 保存成功反馈

#### C2. 资产列表页

页面至少展示：

- 名称
- 更新时间
- artifact_type
- 是否收藏
- 来源 session

#### C3. 资产详情页

页面至少展示：

- 基本信息
- 当前版本内容
- 版本列表
- 来源 iteration

**验收标准**

- 用户可在前端完成保存资产
- 用户可查看资产列表和详情

### D. Session 详情增强

#### D1. 时间线展示增强

在 session 详情页中展示：

- 每条 iteration 的 mode
- 创建时间
- 核心摘要
- 是否来自 continue 链路

#### D2. 结果摘要增强

不同 mode 建议展示不同摘要：

- generate
  - `final_prompt` 摘要
- debug
  - `top_failure_mode` 和 `fixed_prompt` 摘要
- evaluate
  - `total_score` 和 `top_issue`
- continue
  - `optimization_goal` 和 `refined_result` 摘要

#### D3. 操作入口增强

在 session 详情页支持：

- 复制结果
- 保存为资产
- 从某个 iteration 再次 continue

**验收标准**

- session 详情页从“能看”升级为“可追踪、可操作”

### E. 模板系统边界预留

#### E1. 后端边界设计

- 预留 `templates` router 位置
- 预留 `template` service 与 schema
- 不要求完整实现业务细节

#### E2. 前端边界设计

- 预留 `templates` 页面路由
- 允许用占位页或隐藏入口

#### E3. 资产到模板转化路径设计

先在文档和接口层定义：

- future: 从 asset 创建 template

**验收标准**

- 模板体系可在 Sprint 4 无痛接入

## 5. 交付物

- 资产相关 migration
- Asset API 初版
- Asset 列表页与详情页
- 从 iteration 保存为 asset 的前后端闭环
- Session 详情增强版
- 模板预留边界

## 6. 验收标准

### 数据层

- `prompt_assets` / `prompt_asset_versions` 数据关系正确
- 版本号递增逻辑正确

### 后端

- 可创建 asset
- 可查询 asset 列表与详情
- 可新建 asset version

### 前端

- Result Panel 可保存为 asset
- Session Detail 可保存为 asset
- 资产页可浏览结果

## 7. 风险与注意事项

- 不要把 template 和 asset 混在 Sprint 3 同时做深
- 不要只做资产表而不做版本表，否则后续返工大
- 不要把“保存为资产”做成纯前端临时状态，必须落库
- 不要忽略 session detail 的可读性，否则资产沉淀价值会下降

## 8. 建议交付顺序

1. Asset migration
2. Asset ORM / repository / service
3. Asset API
4. Session detail 增强
5. Result Panel 保存为资产入口
6. Asset 列表页与详情页
7. 模板边界预留

## 9. Sprint 3 结束产物清单

- `prompt_assets` / `prompt_asset_versions`
- Asset API 初版
- 保存为资产主流程
- Asset 列表页
- Asset 详情页
- 增强版 Session Detail
- Template 边界占位

## 10. 完成定义

当以下全部满足时，Sprint 3 可关闭：

- 用户可从历史结果沉淀出 asset
- asset 有版本能力
- session detail 具备资产化入口
- 产品从“可用主流程”进入“可沉淀成果”阶段
- Sprint 4 可在此基础上继续推进模板、额度或内测能力
