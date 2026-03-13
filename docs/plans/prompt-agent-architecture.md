# Prompt Agent Architecture

## 一 文档目标

本文件定义 `Prompt Agent` 的系统架构。目标不是描述一个普通的 prompt 生成器，而是定义一个围绕 `Generate / Debug / Evaluate / Continue Optimization` 四个核心能力运行的个人 Prompt Agent。

该架构应满足以下要求：

- 面向独立 Prompt 产品
- 支持多模式 agent 编排
- 支持多轮优化闭环
- 支持控制模块装配
- 支持结构化评估
- 支持可解释输出
- 支持后续演化为更强的 agent 系统

## 二 总体架构定位

Prompt Agent 本质上是一个任务定向 agent，而不是开放式聊天 agent。

它不是让模型无限制自由发挥，而是让模型在明确的工作流、状态和输出契约内执行任务。产品的核心不是“多聪明地聊天”，而是“多稳定地把用户需求转化成高质量 Prompt，并在需要时继续优化”。

因此，架构上不应采用完全无边界的 autonomous agent 模式，而应采用更可控的：

**structured agent orchestration**

也就是：

- 明确模式
- 明确状态
- 明确步骤
- 明确中间产物
- 明确输出契约

## 三 业界 agent 最佳实践的引入原则

为了让 Prompt Agent 具备产品级稳定性，架构上应显式采纳以下最佳实践。

### 1. Agent 不应无限自由，而应有清晰边界

开放式 agent 常常会产生漂移、重复、失控或过度推断。Prompt Agent 属于生产工具，应优先选择可控编排而不是完全自治。

### 2. 将复杂任务拆成有明确职责的子阶段

不要让一个大模型在单步中同时完成识别、诊断、装配、修复和评估。应拆分为明确子任务，并使用结构化中间对象连接。

### 3. 中间状态必须显式化

高质量 agent 的关键不是最后一句话，而是过程中的中间表示，例如：

- 任务类型
- 输出类型
- 质量目标
- 失败模式
- 控制模块
- 修复建议
- 评分结果

这些都应该是结构化对象，而不是只在模型脑内隐式完成。

### 4. 工具调用要服务于流程，而不是为了显得 agent 化

Prompt Agent 不需要为了“像 agent”而堆工具。工具只应围绕业务闭环存在，例如：

- 生成器
- 诊断器
- 调试器
- 评估器
- 历史存储
- 版本比较

### 5. 记忆分层，而不是一锅端

多轮优化时，系统需要记忆，但不是把所有历史都塞进上下文。应做分层记忆：

- 会话短期记忆
- Prompt 版本记忆
- 用户偏好记忆
- 模块资产记忆

### 6. 评估必须内置，而不是附加功能

真正产品化的 agent 不能只会生成，还必须能评估自己的输出是否足够好，并据此驱动下一轮优化。

## 四 高层架构图

可以将 Prompt Agent 抽象为以下结构：

```text
User Input
-> Mode Selector
-> Agent Orchestrator
   -> Task Understanding Layer
   -> Diagnosis Layer
   -> Module Routing Layer
   -> Prompt Assembly / Debug / Evaluation Engine
   -> Memory Layer
   -> Result Formatter
-> UI Output
-> Continue Optimization Trigger
-> Agent Orchestrator (next round)
```

## 五 核心架构组件

### 1. Mode Selector

负责明确当前用户请求处于哪种模式：

- Generate
- Debug
- Evaluate
- Continue Optimization

这是整个 agent 的第一道分流器。如果模式不明确，整个后续路径就会混乱。

### 2. Agent Orchestrator

这是核心控制器，不直接负责生成最终结果，而是负责：

- 接收模式与输入
- 调度子引擎
- 维护状态机
- 管理中间产物
- 触发下一步
- 形成最终响应

它是整个 Prompt Agent 的大脑，但不是内容生成本身。

### 3. Task Understanding Layer

职责：

- 识别任务类型
- 识别输出产物
- 识别质量目标
- 识别是否需要可执行性、批判性、自然文风等偏好

输出结构建议：

```json
{
  "task_type": "source_code_analysis",
  "output_type": "analysis_prompt",
  "quality_target": "depth",
  "preferences": ["natural_style"]
}
```

### 4. Diagnosis Layer

职责：

- 预判高风险失败模式
- 判断当前 Prompt 或输出的结构缺口
- 在 Debug / Evaluate 模式中识别主要问题

输出结构建议：

```json
{
  "failure_modes": ["surface_restatement", "template_tone"],
  "missing_layers": ["problem_redefinition", "cognitive_drill_down"]
}
```

### 5. Module Routing Layer

职责：

- 根据任务类型加载默认控制模块
- 根据失败模式追加修复模块
- 根据质量目标调整模块权重

它不是简单映射，而是系统真正的 Prompt 结构编排层。

### 6. Prompt Engines

根据模式不同，可拆成三个引擎：

#### Generate Engine

负责将：

- 任务理解
- 模块集合
- 质量偏好

装配成完整 Prompt。

#### Debug Engine

负责将：

- 原始任务
- 当前 Prompt
- 当前输出

转化为：

- 失败模式判断
- 最小必要修复
- 修复后的 Prompt

#### Evaluation Engine

负责将 Prompt 或输出转化为：

- 分项评分
- 总分
- 核心缺陷
- 建议补层

### 7. Memory Layer

这是 agent 化的关键部分之一。

建议采用四层记忆。

#### a. Session Memory

记录当前会话中：

- 用户输入
- 当前模式
- 最近一次结果
- 继续优化链路

#### b. Prompt Version Memory

记录 Prompt 的迭代版本，例如：

- v1 初版生成
- v2 调试修复
- v3 评估后优化

#### c. User Preference Memory

记录用户长期偏好，例如：

- 更偏自然文风
- 更偏深度分析
- 更偏可执行性

#### d. Module Asset Memory

记录稳定有效的控制模块和高频组合，为后续预设和推荐做准备。

### 8. Result Formatter

负责将结构化结果转成前端友好的结果格式，例如：

- Generate 结果卡
- Debug 结果卡
- Evaluate 结果卡
- Continue Optimization 建议动作

## 六 四种核心工作流

### 工作流 1：Generate

```text
User Input
-> Mode = Generate
-> Task Understanding
-> Failure Prediction
-> Module Routing
-> Generate Engine
-> Result Formatter
-> Output: Diagnosis + Final Prompt
```

### 工作流 2：Debug

```text
User Input + Current Prompt + Current Output
-> Mode = Debug
-> Diagnosis Layer
-> Missing Layer Detection
-> Debug Engine
-> Result Formatter
-> Output: Strengths + Weaknesses + Fixes + Fixed Prompt
```

### 工作流 3：Evaluate

```text
Prompt or Output
-> Mode = Evaluate
-> Evaluation Engine
-> Result Formatter
-> Output: Scores + Total + Top Issue + Suggested Fix Layer
```

### 工作流 4：Continue Optimization

```text
Previous Result
-> User Chooses Continue Optimization
-> Session Memory loads prior state
-> Orchestrator decides next sub-goal
-> Route to Generate / Debug / Evaluate enhancement path
-> Produce improved artifact
```

Continue Optimization 是从工具走向 agent 的关键。

## 七 状态机设计

Prompt Agent 应当显式拥有状态机，而不是每次都当作无状态请求处理。

推荐状态：

```text
IDLE
UNDERSTANDING
DIAGNOSING
ROUTING
GENERATING
DEBUGGING
EVALUATING
FORMATTING
READY
ERROR
```

### 状态流示意

```text
IDLE
-> UNDERSTANDING
-> DIAGNOSING
-> ROUTING
-> GENERATING / DEBUGGING / EVALUATING
-> FORMATTING
-> READY
```

如果用户点击继续优化，则从 `READY` 进入下一轮：

```text
READY
-> UNDERSTANDING (with memory)
-> ...
```

## 八 Continue Optimization 设计

这是 Prompt Agent 区别于普通工具的核心。

在结果返回后，系统应主动给出下一步动作，而不是只等用户自己思考。

### Generate 后建议动作

- 再增强深度
- 再增强可执行性
- 再降低 AI 味
- 改成更适合某任务的系统提示词

### Debug 后建议动作

- 继续修复最低质量层
- 改成更强版本
- 保留原意但增强结构

### Evaluate 后建议动作

- 自动修复最低分项
- 基于评估重生成一版
- 做对比优化

这些动作应由 agent 根据当前结果自动生成建议，而不是固定死菜单。

## 九 Prompt 资产与版本管理

即使 MVP 不做完整资产系统，架构上也应预留：

- Prompt 版本链
- 版本差异摘要
- 最优版本标记
- 用户手动收藏

因为一旦进入多轮优化，Prompt 就不再是单一文本，而是一个持续演化的资产。

## 十 安全与约束边界

虽然这是 Prompt 产品，但仍需有 agent 边界控制。

### 1. 不允许模式漂移

Generate 不应偷偷变成直接做任务。

Debug 不应绕开分析直接重写一切。

Evaluate 不应无根据给出高分。

### 2. 不允许过度编造任务上下文

如果用户输入极少，系统可以补结构，但不应虚构大量具体事实。

### 3. 不允许以解释替代产物

Generate 的主产物必须是 Prompt。

Debug 的主产物必须是修复后的 Prompt。

Evaluate 的主产物必须是结构化评估结论。

### 4. 优先最小必要修复

这是 Debug 模式的重要原则，防止 agent 总是推倒重来。

## 十一 后端实现建议

建议服务端采用明确编排层 + 多引擎结构，而不是一个巨大 service。

推荐抽象：

- `PromptAgentOrchestrator`
- `TaskUnderstandingEngine`
- `PromptDiagnosisEngine`
- `PromptModuleRouter`
- `PromptGenerateEngine`
- `PromptDebugEngine`
- `PromptEvaluationEngine`
- `PromptMemoryService`
- `PromptResultFormatter`

这样做的好处是：

- 每层职责清晰
- 易于单测
- 易于逐步替换底层模型策略
- 易于演化成更复杂 agent

## 十二 前端实现建议

前端不应模拟聊天产品，而应表现为一个 agent 工作台。

建议核心交互结构：

```text
Prompt Agent Workspace
├── Input Composer
├── Mode Selector
├── Result Workspace
├── Suggested Next Actions
└── Version / Session Context
```

关键点在于：

- 结果不是聊天气泡，而是结构化卡片
- 继续优化动作要显式存在
- 当前会话的 Prompt 版本链最好可见

## 十三 MVP Agent 最佳实践落地清单

为了确保“引入业界 agent 最佳实践”不是口号，建议 MVP 明确落地以下实践：

### 必落地

- 明确模式分流
- 明确状态机
- 明确中间对象
- 模块化控制层路由
- 会话记忆
- 多轮继续优化
- 结构化评估
- 最小必要修复原则

### MVP 可先不做

- 自主长期规划 agent
- 多 agent 复杂协作
- 复杂外部工具链编排
- 自治式长链决策

Prompt Agent 更适合 **high-control agent**，而不是完全自治 agent。

## 十四 演进路线

### V1

单用户 Prompt Agent，支持 Generate / Debug / Evaluate / Continue Optimization。

### V1.5

加入 Prompt 版本链、历史记录、偏好记忆。

### V2

加入 Prompt 资产管理、预设工作流、模块可视化、更多 agent 策略。

### V3

加入团队协作、共享模块库、跨任务 Prompt 资产复用和更高级评估闭环。

## 十五 最终判断

Prompt Agent 的最佳形态，不是一个会聊天的 Prompt 工具，而是一个在明确边界内持续优化 Prompt 的个人 agent。

要实现这一点，关键不是让模型更自由，而是让系统更有结构。

因此，架构上必须坚持：

- 强编排
- 明确模式
- 显式状态
- 结构化中间产物
- 记忆分层
- 评估内置
- 继续优化闭环

只有这样，这个产品才会真正体现“agent 最佳实践”，而不是只是在 UI 上贴一个 agent 标签。
