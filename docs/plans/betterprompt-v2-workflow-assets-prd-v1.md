# BetterPrompt V2 Workflow Assets PRD v1

## 1. 文档目标

本文定义 `BetterPrompt` 在 `V2 Workflow Assets` 阶段的产品需求。

V2 的目标不是把产品做成 agent，也不是做成垂直工作台，而是在 `V1 Library + Workbench` 之上，把“可复用的运行配置”变成真正的产品对象。

一句话概括：

- `V1` 让用户拥有 Prompt 资产
- `V2` 让用户拥有可重复运行的 AI 工作配置

## 2. 产品定位

### V2 的产品定义

V2 是 `Workflow Assets` 层。

它回答的问题不是：

- “这个 Prompt 存在哪？”

而是：

- “我下一次怎样用同一套方法再次跑出高质量结果？”

### V2 的核心价值

V2 要解决的核心问题是：

- 用户明明已经找到过一次好方法，但下一次还得重新选 Prompt、重新补上下文、重新想评估标准、重新决定运行顺序

V2 必须把这些“围绕 Prompt 的复用信息”从临时操作升级为可保存对象。

## 3. 核心 Job To Be Done

### 主 JTBD

当用户已经有一批 Prompt 资产时，他希望：

- 不再每次从零搭一遍分析 setup
- 能把成功的运行方法保存下来
- 能在以后快速重复同一套运行方式
- 能让 Prompt、上下文、评估标准和流程组合成一个真正可复用的工作单元

### V2 的完成定义

当 V2 完成时，用户应能：

1. 保存 `Context Pack`
2. 保存 `Evaluation Profile`
3. 保存 `Workflow Recipe`
4. 保存 `Run Preset`
5. 在 Workbench 中选择上述对象发起运行
6. 在 Session 历史里看出这次运行用了哪套 preset/recipe

## 4. 目标用户

### 用户类型 A：已有可用 Prompt，但复用方式混乱

特征：

- 已经收藏了不少 Prompt
- 记得某些组合“上次很好用”
- 但说不清到底用了哪些上下文、哪套评估标准、什么运行顺序

核心需求：

- 把“方法”保存下来，而不只是保存 Prompt 文本

### 用户类型 B：重复做某类分析的个人研究者

特征：

- 会反复做某一类任务，如公司研究、市场研究、写作生成
- 对结构稳定性和重复效率比对话体验更敏感

核心需求：

- 一键复用
- 稳定输出
- 少犯 setup 层错误

### 用户类型 C：未来垂直工作台的早期用户

特征：

- 已经隐约需要“工作流”
- 但还不需要 workspace、watchlist、agent monitor

核心需求：

- 在进入垂直产品前，先拥有通用而稳定的 workflow objects

## 5. V2 核心对象

V2 只新增四个一等产品对象。

### 5.1 Context Pack

定义：

- 一个可复用的上下文包

典型内容：

- 公司背景
- 行业知识
- 分析假设
- 写作风格规则
- 术语约定
- 用户自己的长期备注

不应被理解为：

- 文件系统
- 任意知识库
- 通用 RAG 平台

### 5.2 Evaluation Profile

定义：

- 一个可复用的质量标准

典型内容：

- 证据质量要求
- 反方覆盖要求
- 风险揭示要求
- 输出结构要求
- 通过阈值

不应被理解为：

- 通用 benchmark 平台
- 多模型评分实验工具

### 5.3 Workflow Recipe

定义：

- 一个可复用的运行顺序与方法模板

典型例子：

- `generate -> evaluate -> continue`
- `generate -> debug -> continue`
- `debug only`

不应被理解为：

- 可视化 BPMN 工作流设计器
- 多 agent 编排系统

### 5.4 Run Preset

定义：

- 一个具体可执行的启动包

它绑定的是：

- 某个 Prompt 版本
- 某个或多个 Context Pack 版本
- 某个 Evaluation Profile 版本
- 某个 Workflow Recipe 版本
- 一组运行参数

它是 V2 最贴近“用户一键复用”的对象。

## 6. 关键用户故事

### 故事 1：从 Workbench 保存 Context Pack

用户在一次运行后，发现自己反复输入同样的背景说明。

他应该能：

- 把这些背景信息整理成 `Context Pack`
- 命名、描述、保存
- 在以后运行时反复选择

### 故事 2：保存一套评估标准

用户经常要判断输出是否“证据充分、结构完整、结论克制”。

他应该能：

- 创建一套 `Evaluation Profile`
- 在后续运行中重复使用

### 故事 3：保存一套运行方法

用户逐渐发现自己的最佳流程不是单次 generate，而是：

- 先生成
- 再评估
- 再继续优化

他应该能把这套顺序保存成 `Workflow Recipe`。

### 故事 4：一键复用整套 setup

用户已经有：

- 一个 Prompt
- 两个 Context Pack
- 一个 Evaluation Profile
- 一个 Workflow Recipe

他应该能把这四者打包成 `Run Preset`，之后快速重新使用。

### 故事 5：运行历史可识别

用户回看 Session 时，应该知道：

- 这是手工运行还是 preset 运行
- 用了哪个 preset
- 用了哪套 recipe

否则 V2 的“可复用工作配置”价值就不可见。

## 7. 信息架构

推荐的 V2 IA：

```text
Library
  ├── Prompts
  ├── Context Packs
  ├── Evaluation Profiles
  └── Workflow Recipes

Workbench
  ├── Prompt selector
  ├── Context pack selector
  ├── Evaluation profile selector
  ├── Workflow recipe selector
  ├── Run settings
  └── Save as Run Preset

Runs
  └── Session history
```

### 关键 IA 原则

- `Library` 仍是资产层入口
- `Workbench` 仍是执行层入口
- `Run Preset` 不需要单独成为顶层导航
- `Run Preset` 更适合作为 Workbench 与 Runs 的桥梁对象

## 8. 核心流程

### 8.1 资产创建流

```text
Workbench / Library
  -> create context pack / evaluation profile / workflow recipe
  -> save first version
  -> optional later versioning
```

### 8.2 Preset 启动流

```text
User selects Run Preset
  -> system resolves referenced versions
  -> user optionally overrides small run settings
  -> call existing prompt-agent flow
  -> create / reuse prompt_session
  -> create prompt_iteration records
  -> result page shows preset + recipe provenance
```

### 8.3 历史复用流

```text
Session history
  -> open prior run
  -> inspect prompt/context/profile/recipe refs
  -> save as new preset or rerun
```

## 9. 功能范围

### In Scope

- Context Pack CRUD
- Context Pack versioning
- Evaluation Profile CRUD
- Evaluation Profile versioning
- Workflow Recipe CRUD
- Workflow Recipe versioning
- Run Preset CRUD
- Workbench 选择上述对象发起运行
- Prompt Agent 请求携带 workflow asset refs
- Session 能记录 preset / recipe 来源

### NOT In Scope

- Domain Workspace
- 股票专用工作台
- Watchlist
- 定时 rerun
- 事件触发
- Alert feed
- 团队协作
- marketplace
- 复杂图形化流程编排器

## 10. 产品边界

### 10.1 V2 仍是用户驱动系统

V2 的所有运行都应当是：

- 用户主动发起

而不是：

- 系统自动监控后重跑

### 10.2 V2 不做“知识库产品”

Context Pack 的定位是：

- 轻量、明确、可复用的运行上下文

而不是：

- 无限堆积文档的知识仓库

### 10.3 V2 不做“流程画布产品”

Workflow Recipe 的定位是：

- 结构化流程定义

而不是：

- 泛化的工作流画布

## 11. 关键状态与边缘场景

### 11.1 空状态

- 没有 Context Pack 时，Workbench 仍可正常运行
- 没有 Evaluation Profile 时，系统应使用默认内置评估逻辑
- 没有 Workflow Recipe 时，仍可用现有单次操作模式
- 没有 Run Preset 时，应鼓励用户从一次成功运行中创建

### 11.2 删除与归档

- 已被 Preset 引用的对象不应做硬删除
- V2 优先用 `archived_at` 软归档
- 归档对象默认不出现在 selector 中，但历史 session 仍可解析来源

### 11.3 版本引用失效

当 Preset 引用的某个版本被归档或不再是 current version 时：

- 仍应允许按该具体版本运行
- 只要该版本本身还存在

因此：

- Preset 引用的是 `version id`
- 不是“当前版本”的模糊引用

### 11.4 启动前校验失败

Preset 启动时，如果某个引用对象不存在：

- 应明确报错
- 应指明是哪一个对象缺失
- 不要悄悄退回默认逻辑

### 11.5 运行中修改对象

若用户在运行后修改了 Context Pack / Evaluation Profile / Workflow Recipe：

- 已发生的 session 不应被追溯性污染
- 历史运行继续指向当时实际使用的版本

## 12. 成功指标

V2 的核心不是 DAU，而是复用率。

推荐看这几类指标：

### 12.1 资产采用指标

- 创建过至少 1 个 Context Pack 的用户占比
- 创建过至少 1 个 Evaluation Profile 的用户占比
- 创建过至少 1 个 Workflow Recipe 的用户占比
- 创建过至少 1 个 Run Preset 的用户占比

### 12.2 复用指标

- 使用 Preset 发起的运行占全部运行的比例
- 被重复使用 2 次以上的 Context Pack 占比
- 被重复使用 2 次以上的 Evaluation Profile 占比
- 被重复使用 2 次以上的 Workflow Recipe 占比

### 12.3 结果稳定性代理指标

- 同类任务平均 setup 时间下降
- 用户从历史 run 重新启动的比例上升
- Session 中带 `run_preset_id` 的比例上升

## 13. 上线验收标准

当以下条件全部满足时，V2 才算产品定义上成立：

1. 用户能创建并管理四类 workflow assets
2. Run Preset 能绑定具体版本引用
3. Workbench 能从这些资产启动运行
4. Session 历史能看到 preset / recipe 来源
5. 资产删除策略不会破坏历史运行可追溯性
6. 没有资产时，系统仍能平滑退回 V1 能力

## 14. 最终判断

V2 不是给 BetterPrompt 增加几个新资源名词。

V2 的真正作用是把：

- Prompt 的复用

推进成：

- 方法的复用

只有这一层做实，后面的 `Domain Workspace` 和 `Freshness-Aware Agent` 才不会变成空壳。 
