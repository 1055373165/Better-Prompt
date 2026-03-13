# 《BetterPrompt Sprint 5 实施任务单 v1》

## 1. Sprint 目标

Sprint 5 的目标是从“具备内测条件”升级到“具备可灰度上线的基础稳定性与交付能力”。

Sprint 5 结束时，项目应满足：

- **核心主流程具备基础测试覆盖**
- **日志、错误治理、监控与告警能力具备最小闭环**
- **部署与环境管理进入可发布状态**
- **内测环境可稳定运行并支持问题追踪**
- **项目具备灰度上线前的最小工程质量门槛**

## 2. Sprint 范围

本 Sprint 覆盖：

- 单元测试、集成测试、关键 E2E 基础落地
- 统一错误码与统一错误响应增强
- 结构化日志、request id、关键链路日志补齐
- 错误上报与基础监控接入
- staging / pre-prod 部署流程
- 环境变量与配置治理
- 发布检查清单与回滚预案

本 Sprint 不覆盖：

- 大规模性能压测优化
- 完整商业化计费系统
- 团队权限高级模型
- 多区域部署
- 复杂实验平台

## 3. Sprint 成功标准

- generate/debug/evaluate/continue 核心链路具备自动化测试
- 日志足以定位一次失败请求的关键上下文
- staging 环境可稳定部署并验证主流程
- 错误上报可覆盖关键失败场景
- 发布流程具备基本可重复性

## 4. 任务拆解

### A. 测试体系建设

#### A1. 后端单元测试

覆盖重点：

- schema 校验
- session / iteration service 核心逻辑
- asset / template service 核心逻辑
- quota 检查逻辑
- 错误映射逻辑

#### A2. 后端集成测试

覆盖重点：

- `POST /api/v1/prompt-sessions`
- `GET /api/v1/prompt-sessions/{id}`
- `POST /api/v1/prompt-sessions/{id}/generate`
- `POST /api/v1/prompt-sessions/{id}/debug`
- `POST /api/v1/prompt-sessions/{id}/evaluate`
- `POST /api/v1/prompt-sessions/{id}/continue`
- `POST /api/v1/prompt-assets`
- `POST /api/v1/templates`

#### A3. 前端组件与页面测试

覆盖重点：

- 工作台表单提交流程
- session detail 展示
- asset 保存流程
- template 创建流程
- 错误状态展示

#### A4. 关键 E2E 测试

至少覆盖：

- 创建 session
- Generate
- Continue
- 保存为 asset
- 从 asset 创建 template

**交付物**

- 测试目录结构
- 测试用例初版
- CI 可执行测试任务

**验收标准**

- 核心主流程具备自动化回归能力

### B. 错误治理与响应统一

#### B1. 错误码体系收口

至少统一：

- `VALIDATION_ERROR`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `NOT_FOUND`
- `RATE_LIMITED`
- `QUOTA_EXCEEDED`
- `PROVIDER_TIMEOUT`
- `PROVIDER_ERROR`
- `MODEL_OUTPUT_INVALID`
- `DATABASE_ERROR`
- `INTERNAL_SERVER_ERROR`

#### B2. 错误响应统一

保证所有 API 返回一致 error shape：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "request_id": "request-id"
  }
}
```

#### B3. 前端错误提示映射

前端至少能区分：

- 参数错误
- 登录失效
- 权限不足
- 配额不足
- provider 超时
- 系统错误

**验收标准**

- 核心 API 错误结构一致
- 前端能展示合理错误信息

### C. 日志与可观测性

#### C1. 结构化日志

后端关键日志字段至少包含：

- `request_id`
- `user_id`
- `session_id`
- `iteration_id`
- `request_path`
- `request_type`
- `provider`
- `model`
- `latency_ms`
- `status`
- `error_code`

#### C2. request id 贯穿

- API 入口生成 request id
- request id 写入响应头或错误体
- 所有关键日志行带 request id

#### C3. 错误上报

接入基础错误上报工具：

- 如 Sentry

#### C4. 基础指标

至少监控：

- 请求量
- 成功率
- 平均耗时
- provider 失败率
- quota 拒绝数
- 主要 API 错误分布

**验收标准**

- 能通过 request id 追踪一次失败请求
- 关键异常能进入错误上报系统

### D. 部署与环境治理

#### D1. 环境变量治理

明确并收口：

- `APP_ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `DEFAULT_PROVIDER`
- `DEFAULT_MODEL`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `SENTRY_DSN`
- `FRONTEND_APP_URL`
- `BACKEND_API_URL`

#### D2. Docker / 部署脚本

至少具备：

- 后端 Dockerfile
- 前端构建脚本
- staging 启动方案

#### D3. staging 环境准备

要求：

- 能部署前端
- 能部署后端
- 能连接 staging DB
- 能运行主流程验证

#### D4. migration 发布流程

明确：

- 迁移执行顺序
- 发布前检查
- 回滚处理方式

**验收标准**

- staging 部署可重复执行
- migration 发布路径清晰

### E. 发布与运维准备

#### E1. 发布检查清单

至少包含：

- migration 是否已验证
- 环境变量是否配置
- staging 主流程是否已回归
- 错误上报是否可用
- 日志是否可检索
- quota 与 auth 是否工作

#### E2. 回滚预案

至少明确：

- 前端回滚方式
- 后端回滚方式
- migration 回滚策略
- provider 配置故障应急方案

#### E3. 运维手册初版

建议补充：

- 如何查看日志
- 如何检查健康状态
- 如何验证 provider 连通性
- 如何定位 quota / auth 问题

**验收标准**

- 发布前后有明确检查路径
- 线上出问题时有最小排障手册

## 5. 交付物

- 单元测试 / 集成测试 / E2E 初版
- 统一错误码与 error shape
- 结构化日志与 request id
- 错误上报接入
- staging 部署方案
- 环境变量治理文档
- 发布检查清单
- 回滚预案初版

## 6. 验收标准

### 测试层

- 核心主流程至少有自动化回归
- 改动后可通过 CI 验证

### 可观测性层

- 关键 API 请求可追踪
- 异常可上报
- 主要失败有统计入口

### 部署层

- staging 可重复部署
- migration 可按规范执行

### 产品层

- 内测环境可稳定演示与验证主流程
- 为灰度上线准备完成

## 7. 风险与注意事项

- 不要把 Sprint 5 变成全面性能优化 Sprint
- 不要跳过测试直接进入上线
- 不要只做日志不做错误码体系
- 不要忽视 staging 环境质量，避免把生产当测试环境
- 不要让部署步骤只存在口头流程，必须文档化

## 8. 建议交付顺序

1. 错误码与 error shape 收口
2. 结构化日志与 request id
3. 后端单测与集成测试
4. 前端关键流程测试
5. E2E 初版
6. 错误上报与基础指标
7. staging 部署与环境治理
8. 发布清单与回滚预案

## 9. Sprint 5 结束产物清单

- 测试体系初版
- 日志与监控基础能力
- 错误治理收口
- staging 部署流程
- 发布清单
- 回滚预案
- 最小运维手册

## 10. 完成定义

当以下全部满足时，Sprint 5 可关闭：

- 核心主流程可通过自动化测试回归
- staging 环境可稳定部署与验证
- 错误、日志、监控、发布流程具备最小闭环
- 项目具备灰度上线前的基础工程质量门槛
- 后续阶段可进入性能优化、商业化和更正式的上线筹备
