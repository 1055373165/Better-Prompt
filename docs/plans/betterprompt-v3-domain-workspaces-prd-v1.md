# BetterPrompt V3 Domain Workspaces PRD v1

## 1. 文档目标

本文定义 `V3 Domain Workspaces` 的产品需求。

V3 的任务不是继续堆更多 workflow asset 类型，而是把 `V2 Workflow Assets` 包装成真正可工作的领域界面。

一句话概括：

- `V2` 解决“方法怎么复用”
- `V3` 解决“这些方法应该在哪个领域语境里被使用”

## 2. 产品定位

V3 是 `Domain Workspace Layer`。

它提供的不是：

- 通用聊天页
- 通用文件夹页
- 团队协作平台

而是：

- 面向某个研究任务的单用户工作空间

## 3. 核心 JTBD

当用户已经拥有 Prompt、Context Pack、Evaluation Profile、Workflow Recipe 和 Run Preset 后，他希望：

- 在一个更像真实工作区的界面里工作
- 把分析对象、资料、报告放在一起
- 不再从“裸 Prompt 资产”视角理解整个系统

## 4. V3 核心对象

V3 新增四个一等对象：

1. `Domain Workspace`
2. `Workspace Subject`
3. `Research Source`
4. `Research Report`

定义如下：

- `Domain Workspace`：一个领域工作区，如股票分析、公司研究、深度研究
- `Workspace Subject`：工作区中的研究对象，如 ticker、company、topic
- `Research Source`：URL、文件、转录、手写笔记等证据输入
- `Research Report`：绑定 subject 的用户可复用研究结论

## 5. 产品策略锁定

### 5.1 先做一个底座，不做三个产品

V3 不应同时做成三套独立系统。

正确顺序是：

1. 做通用 `DomainWorkspace` 底座
2. 先落一个最强工作区
3. 再复用到底座上的其他 domain

推荐优先级：

1. `Stock Analysis Workspace`
2. `Company Research Workspace`
3. `Deep Research Workspace`

### 5.2 V3 仍是单用户优先

V3 workspace 的语义是：

- 单用户研究工作区

不是：

- 团队 workspace
- 协作项目空间

## 6. 关键用户故事

### 故事 1：创建一个股票研究工作区

用户应能：

- 创建 `Stock Analysis Workspace`
- 给它命名
- 为其绑定默认 run preset / recipe

### 故事 2：向工作区添加研究对象

用户应能：

- 添加 `AAPL`
- 添加 `NVDA`
- 添加某个公司或主题

### 故事 3：把资料沉淀到工作区

用户应能：

- 保存网页链接
- 保存电话会纪要
- 保存自己的备注
- 将它们挂到具体 subject 上

### 故事 4：从工作区发起运行

用户应能：

- 直接在工作区内选择 subject
- 调用默认 preset / recipe
- 生成研究输出

### 故事 5：将结果沉淀为研究报告

用户应能：

- 将一次运行结果保存为 `Research Report`
- 在后续继续追加新版本

## 7. 信息架构

```text
Workspaces
  ├── Workspace Home
  ├── Subjects
  ├── Sources
  ├── Reports
  └── Run Panel

Library
  └── 继续作为资产源

Workbench
  └── 继续作为底层执行壳
```

关键原则：

- `Library` 不消失
- `Workbench` 不消失
- `Workspace` 是在上层打包，而不是替换前两者

## 8. 功能范围

### In Scope

- Domain Workspace CRUD
- Subject CRUD
- Source CRUD
- Report CRUD
- Report versioning
- 从 workspace 发起 prompt-agent run
- session 记录 workspace / subject provenance

### NOT In Scope

- watchlist
- 自动 rerun
- alerts
- team collaboration
- org / membership / roles
- trading execution

## 9. 关键状态与边缘场景

### 9.1 空工作区

- 没有 subject 时，仍可创建 workspace
- 没有 source 时，仍可运行，但应提示研究上下文较弱

### 9.2 source 与 report 的归属

- source 可挂在 workspace 级别
- 也可挂在具体 subject 上
- report 默认应绑定 subject

### 9.3 历史版本

- report 新版本不覆盖旧版本
- report history 必须能回看来源 session / iteration

### 9.4 删除策略

- subject、source、report 优先软归档
- 已被历史 run 使用的对象不应硬删

## 10. 成功指标

- 创建过至少 1 个 workspace 的用户占比
- 每个 workspace 的平均 subject 数
- 每个 workspace 的平均 report 数
- 由 workspace 发起的运行占比
- report version 被追加的比例

## 11. 上线验收标准

V3 只有在以下条件全部成立时才算完成：

1. 用户能创建工作区并管理 subject
2. 用户能在工作区中保存 research source
3. 用户能在工作区中发起运行
4. 用户能将结果保存为 report 并继续 versioning
5. session 能表达 workspace / subject provenance

## 12. 最终判断

V3 的本质不是加一个新导航入口。

它的本质是把：

- workflow assets

升级成：

- domain-native working environment

这一步做实之后，V4 的 watchlist、monitor、alert 才有承载体。
