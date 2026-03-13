# 《BetterPrompt Sprint 4 实施任务单 v1》

## 1. Sprint 目标

Sprint 4 的目标是从“结果可沉淀”升级到“产品具备可内测的基础能力与可受控扩展边界”。

Sprint 4 结束时，项目应满足：

- **模板体系具备最小可用能力**
- **基础鉴权能力接入**
- **使用统计与额度预留开始落地**
- **内测所需的基础控制能力具备**
- **产品从单纯功能流转向可管理、可控制的内测形态**

## 2. Sprint 范围

本 Sprint 覆盖：

- `templates` 与 `template_versions` 数据模型落地
- 从 asset 创建 template 的主流程
- 基础 auth 能力接入
- 基础 usage 记录与 quota 预留
- 内测期基础访问控制与错误治理增强
- 模板页与模板详情页基础版

本 Sprint 不覆盖：

- 完整团队协作能力
- 完整计费与订阅系统
- 复杂 RBAC
- 多 provider 动态策略平台
- 完整实验与灰度系统

## 3. Sprint 成功标准

- 用户可将 asset 转化为 template
- 系统可区分 user template 与 official template
- 基础登录态或用户上下文能力可工作
- 主流程请求可记录 usage 基础数据
- quota 规则有明确检查入口，即使先用简单策略
- 产品具备最小内测封闭运行条件

## 4. 任务拆解

### A. 数据层：模板与使用统计

#### A1. 模板表落地

建立：

- `templates`
- `template_versions`

字段至少支持：

- `owner_type`
- `owner_id`
- `name`
- `description`
- `category`
- `artifact_type`
- `current_version_id`
- `is_official`

#### A2. usage 记录表落地

建立：

- `usage_records`

字段至少支持：

- `user_id`
- `iteration_id`
- `provider`
- `model`
- `tokens_input`
- `tokens_output`
- `estimated_cost_usd`
- `request_type`

**交付物**

- 模板相关 migration
- usage 相关 migration
- ORM 模型与 repository 初版

**验收标准**

- template/version 可正常写入
- usage record 可按请求落库

### B. 后端：模板主流程

#### B1. 从 asset 创建 template

实现：

- `POST /api/v1/templates`

支持输入：

- `source_asset_id`
- `name`
- `description`
- `category`
- `artifact_type`
- `content`

#### B2. 模板查询

实现：

- `GET /api/v1/templates`
- `GET /api/v1/templates/{id}`

#### B3. 模板版本追加

实现：

- `POST /api/v1/templates/{id}/versions`

#### B4. 官方模板与用户模板区分

至少在查询层支持：

- `owner_type=system`
- `owner_type=user`

**交付物**

- Template service
- Template repository
- Template router
- Asset -> Template 转化逻辑

**验收标准**

- 可从 asset 创建 template
- 可查询 template 列表与详情
- 可追加 template version

### C. 后端：基础 auth 与用户上下文

#### C1. 登录态方案落位

Sprint 4 可选其一：

- 简易 email/password
- 简易开发态 mock user
- 轻量 session / JWT 占位

要求：

- 不必一步做到完整生产级
- 但必须形成稳定的 `current_user` 依赖入口

#### C2. 用户数据隔离

保证：

- session 只能访问自己的
- asset 只能访问自己的
- template 至少区分自己的和官方的

**交付物**

- `auth` router / service 初版
- `current_user` dependency
- 数据访问过滤

**验收标准**

- API 能基于用户上下文返回数据
- 非本人资源不可访问

### D. 后端：usage 与 quota 预留

#### D1. usage 记录

在以下请求链路中记录 usage：

- generate
- debug
- evaluate
- continue

即使当前 provider 数据不完整，也应预留字段并记录基础 metadata。

#### D2. quota 检查入口

建立：

- `QuotaService`

Sprint 4 可先做简单规则：

- 单用户每日请求数限制
- 单次请求输入长度限制

**交付物**

- usage 记录逻辑
- quota 检查入口

**验收标准**

- usage 可按用户聚合
- quota 逻辑有明确插入点

### E. 前端：模板页与内测形态

#### E1. 模板列表页

展示：

- 模板名称
- 分类
- artifact_type
- 来源类型（官方 / 用户）
- 更新时间

#### E2. 模板详情页

展示：

- 基本信息
- 当前版本内容
- 版本列表
- 来源 asset（如有）

#### E3. 从 asset 创建 template

在 asset 详情页中增加：

- 创建 template 入口
- 简单表单
- 成功反馈

#### E4. 基础登录态表现

前端至少支持：

- mock 登录态
- 当前用户上下文接入
- 未登录时的受限提示或简单跳转策略

**验收标准**

- 用户可浏览模板
- 用户可从 asset 转为 template
- 前端对登录态具备基础感知

### F. 内测准备与错误治理增强

#### F1. 错误码增强

至少补齐：

- `UNAUTHORIZED`
- `FORBIDDEN`
- `RATE_LIMITED`
- `QUOTA_EXCEEDED`

#### F2. 内测控制

Sprint 4 可选实现简单内测策略：

- 白名单邮箱
- 开发环境全开放，测试环境限白名单

#### F3. 关键日志增强

增加：

- user_id
- session_id
- iteration_id
- provider
- request_type
- quota decision

**验收标准**

- 内测期可对访问和请求做基本控制
- 排障日志具备基本上下文

## 5. 交付物

- `templates` / `template_versions` migration
- `usage_records` migration
- Template API 初版
- Asset -> Template 主流程
- 基础 auth / current_user 能力
- usage / quota 预留逻辑
- 模板列表页与详情页基础版
- 内测基础控制能力

## 6. 验收标准

### 数据层

- template 与 version 关系正确
- usage records 可按请求落库

### 后端

- 可从 asset 创建 template
- 可查询 template 列表与详情
- 可获取当前用户上下文
- usage 能按请求记录
- quota 有明确检查入口

### 前端

- 可从 asset 发起创建 template
- 可浏览模板页
- 具备基础登录态或 mock 登录态行为

## 7. 风险与注意事项

- 不要在 Sprint 4 做完整正式 auth 平台，保持最小可用
- 不要把 quota 做成复杂计费系统，先留简单规则入口
- 不要在模板页中混入过多 marketplace 能力
- 不要跳过数据隔离，否则内测阶段风险很高
- 不要让 usage 只停留在日志里，必须有落库能力

## 8. 建议交付顺序

1. Template migration
2. Usage migration
3. Template service / API
4. Asset -> Template 转化主流程
5. current_user 与基础 auth 依赖
6. usage 记录与 quota 检查入口
7. 模板页与详情页
8. 内测控制与错误码增强

## 9. Sprint 4 结束产物清单

- `templates` / `template_versions`
- `usage_records`
- Template API 初版
- Asset -> Template 主流程
- 基础 auth 能力
- usage / quota 预留
- 模板页面基础版
- 内测控制基础能力

## 10. 完成定义

当以下全部满足时，Sprint 4 可关闭：

- asset 可转化为 template
- 模板具备最小版本能力
- 用户上下文已进入主链路
- usage 与 quota 已有落地入口
- 产品具备基础内测条件
- 为 Sprint 5 的稳定性、上线准备和监控治理打下基础
