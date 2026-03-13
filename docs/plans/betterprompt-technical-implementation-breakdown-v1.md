# 《BetterPrompt 技术实施拆解清单 v1》

## 1. 文档目标

本文将《BetterPrompt 产品化架构蓝图 v1》落到可执行层，输出一版用于研发排期、人员分工、里程碑管理的实施拆解清单。

聚焦：

- **阶段划分**
- **模块拆解**
- **优先级**
- **交付物**
- **依赖关系**
- **验收标准**
- **风险提示**

# 2. 实施总原则

- **先跑通**
- **再闭环**
- **再稳定**
- **最后扩展**

# 3. 总体阶段规划

- **Phase A：工程落地与可运行原型**
- **Phase B：主流程产品闭环**
- **Phase C：稳定性与上线准备**
- **Phase D：平台化与商业化增强**

# 4. Phase A：工程落地与可运行原型

## A1. 仓库结构重组

任务：

- 确认最终 monorepo 结构
- 补齐 `frontend` 工程文件
- 补齐 `backend` 工程文件
- 统一本地启动方式

交付物：

- 可运行前端工程
- 可运行后端工程
- 根目录启动说明

## A2. 后端应用骨架搭建

任务：

- 建立 `main.py`
- 建立 `core/config.py`
- 建立 `core/errors.py`
- 建立 `api/deps.py`
- 建立 `health` 路由

## A3. 数据库基础设施

任务：

- 接入 PostgreSQL
- 建立 SQLAlchemy Base / Session
- 集成 Alembic
- 建立第一批表
- 建立基础 repository 模式

## A4. 前端工作台骨架

任务：

- 建立 `app/providers` 完整版本
- 建立工作台主页面
- 重构 API client
- 定义前端 API types
- 建立表单校验

## A5. 最小智能链路

任务：

- 定义 LLM provider 抽象接口
- 实现第一个 provider adapter
- 实现最小 prompt compiler
- 实现统一 LLM 调用封装
- 将当前 rule/template engine 改造成辅助层

# 5. Phase B：主流程产品闭环

## B1. Session 资源化改造

任务：

- 设计 `prompt_sessions` API
- 设计 `prompt_iterations` 读写链路
- 将 generate/debug/evaluate/continue 绑定 session
- 每次操作都落库 iteration

## B2. 历史记录能力

任务：

- 后端实现 session 列表 / 详情接口
- 前端实现历史记录页
- 前端实现会话详情页
- 提供筛选能力

## B3. Prompt 资产沉淀

任务：

- 建立 `prompt_assets` / `prompt_asset_versions`
- 支持从 iteration 保存为 asset
- 支持重命名、描述、打标签、收藏
- 前端实现“保存为资产”动作

## B4. Continue 优化链升级

任务：

- 支持 parent iteration 关联
- 记录 continue 的来源与目标
- 展示版本链与祖先关系
- 支持从任一历史版本继续优化

## B5. 模型与策略配置基础能力

任务：

- 抽象 `ModelPolicy`
- 区分不同 mode 的默认模型配置
- 支持 provider/model 配置注入
- 支持请求级 metadata 记录

# 6. Phase C：稳定性与上线准备

## C1. 统一错误与异常治理

任务：

- 定义错误码体系
- 区分参数错误/鉴权错误/provider 错误/超时错误/限流错误/系统错误
- 前端统一错误提示映射

## C2. 日志与可观测性

任务：

- 接入结构化日志
- 为每个请求生成 request id
- 记录 session id / iteration id / user id
- 增加接口耗时与 provider 调用日志
- 接入错误上报

## C3. 安全与限流

任务：

- 增加认证机制
- 增加用户隔离
- 增加接口限流
- 增加输入限制

## C4. 测试体系

任务：

- 单元测试
- 集成测试
- 前端组件测试
- E2E 测试

## C5. 部署与环境治理

任务：

- 环境变量管理规范化
- 建立 Dockerfile / 部署脚本
- 建立 staging 环境
- 建立 migration 发布流程
- 建立发布检查清单

# 7. Phase D：平台化与商业化增强

## D1. 模板系统

- 建立模板表与版本表
- 支持系统模板 / 用户模板
- 支持分类、搜索、收藏
- 支持从资产保存为模板

## D2. 额度与计费

- 建立 usage_records
- 统计 token 使用与估算成本
- 增加用户配额限制
- 预留订阅等级模型

## D3. 团队能力

- workspace 模型
- 团队模板与共享资产
- 成员关系与权限基础模型

## D4. 评估与策略配置化

- rubric 配置化
- prompt policy 配置化
- 模型策略配置化
- 实验开关与灰度能力

# 8. 模块级实施拆解

## 8.1 前端模块

- 工作台模块
- 历史模块
- 资产模块
- 模板模块
- 设置模块

## 8.2 后端模块

- API 模块
- Session Domain
- Asset Domain
- Evaluation Domain
- LLM Domain

## 8.3 平台模块

- DB / Migration
- Logging / Monitoring
- Security
- CI/CD

# 9. 建议的任务优先级矩阵

- **P0**
  - 工程骨架
  - FastAPI app
  - DB 接入
  - 前端工作台
  - 首个 provider 接入
  - 最小 generate/debug/evaluate/continue 闭环

- **P1**
  - session / iteration 持久化
  - 历史页
  - asset 保存
  - 错误治理
  - 日志
  - 测试

- **P2**
  - auth
  - rate limit
  - usage records
  - staging 部署
  - 基本监控
  - 发布流程

- **P3**
  - 模板系统
  - 额度与计费
  - 团队共享
  - 配置化策略
  - 实验系统

# 10. 人员分工建议

- **前端工程**
- **后端工程**
- **AI / Prompt 工程**
- **平台 / DevOps**

# 11. 关键依赖关系

- 前端联调依赖后端 app 可启动
- session 持久化依赖数据库与 migration 完成
- 历史页依赖 session/iteration 落库
- 资产页依赖 asset 表设计完成
- 上线准备依赖错误治理 + 日志 + auth + 限流
- 模板系统依赖资产沉淀模型稳定
- 计费配额依赖 usage_records 落库

# 12. 风险清单

- **范围膨胀**
- **智能层过度理想化**
- **数据模型过晚设计**
- **沿用当前 demo 接口过久**
- **测试与观测滞后**

# 13. 建议的首批 Sprint 拆法

- **Sprint 1**
  - 项目可跑起来

- **Sprint 2**
  - 最小 generate/debug/evaluate/continue 联调

- **Sprint 3**
  - 主流程可追踪

- **Sprint 4**
  - 结果可沉淀为资产

- **Sprint 5**
  - 具备内测条件

# 14. 里程碑验收定义

- **M1：可运行原型**
- **M2：可内测试用**
- **M3：可灰度上线**
- **M4：可持续迭代平台**

# 15. 最终建议

建议按下面顺序执行：

- 先确认 `session + iteration + asset` 数据模型
- 先补齐可运行工程骨架
- 接入第一个真实模型 provider
- 重构当前接口为 session 驱动接口
- 完成历史、资产、继续优化版本链
- 补 auth、日志、限流、测试、部署
