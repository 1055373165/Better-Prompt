# Prompt Optimization Layer Plan

## 一 结论

将终极模板直接接入产品执行流是一个正确方向，但不应以“硬编码进所有执行逻辑”的方式落地，而应抽象成一个独立的 `Prompt Optimization Layer`。

这样做的原因很简单：

- 我们确实希望每次用户输入后，都先经过一次 Prompt 优化
- 但我们不能把整个系统永久绑死在一个静态母模板上
- 我们还需要验证这个模板是否真的有效
- 我们还需要为未来的模板替换、A/B 对比、回退和多策略路由留下空间

因此，更合适的做法不是“直接塞模板”，而是“建立一层前置优化层”。

## 二 这一层的作用

Prompt Optimization Layer 的作用是：

在用户输入进入主 agent 执行流之前，先自动把用户的自然语言需求翻译成更适合 agent 使用的结构化 Prompt 输入。

换句话说，用户的原始输入并不是直接送给 Generate / Debug / Evaluate，而是先经过这层优化：

```text
用户原始输入
-> Prompt Optimization Layer
-> 优化后的结构化 Prompt / Diagnosis
-> 主 Agent 流程
```

这层本质上就是把你前面设计的“终极模版”产品化、系统化。

## 三 为什么这一步非常有价值

### 价值 1：开发过程本身成为实验场

如果我们让所有真实用户输入先过这层，就可以在产品开发过程中持续验证这套 Prompt 优化体系的有效性，而不是只停留在文档里。

### 价值 2：最大化利用已有 Prompt Engineering 成果

目前我们已经沉淀了：

- Playbook
- Quick Reference
- Examples
- Control Modules
- Generator
- Skill Package
- Ultimate Template

如果这些东西不进入真实执行流，就仍然只是知识资产，而不是产品能力。

### 价值 3：强化产品差异化

Prompt Agent 最核心的价值之一，就是“替普通用户把需求说专业”。Prompt Optimization Layer 恰好就是这条价值主张的技术落点。

## 四 为什么不能简单硬编码

### 风险 1：难以验证是否真的有效

如果模板直接嵌死在所有流程里，我们将无法知道：

- 是模板有效，还是其他流程有效
- 哪一类任务提升最大
- 哪一类任务反而被模板拖慢或扭曲

### 风险 2：未来难以替换

一旦后续我们要：

- 升级模板
- 引入多模板策略
- 做任务分流
- 做 A/B 对比

硬编码方案会造成高耦合。

### 风险 3：调试困难

如果用户结果不好，我们会很难定位问题究竟来自：

- 原始输入
- 优化模板
- 主 Agent 流程
- 输出格式化层

## 五 推荐实现方式

最推荐的落地方式是：

**将终极模板实现为一个可配置的 Prompt Optimization Layer，默认开启。**

### 设计原则

- 默认对所有用户输入生效
- 但保留配置开关
- 保留实验能力
- 保留回退能力
- 保留观察能力

## 六 在系统中的位置

推荐执行流如下：

```text
User Input
-> Mode Selector
-> Prompt Optimization Layer
-> Agent Orchestrator
   -> Generate / Debug / Evaluate
-> Result Formatter
-> UI
```

如果用户点击 Continue Optimization，则执行流为：

```text
Previous State + New User Intent
-> Prompt Optimization Layer
-> Agent Orchestrator
-> Result Formatter
```

## 七 Prompt Optimization Layer 的输入输出

### 输入

- 原始用户输入
- 当前模式（Generate / Debug / Evaluate）
- 可选用户偏好
- 可选上一轮上下文

### 输出

建议输出结构化对象，而不是纯文本：

```json
{
  "raw_input": "用户原始输入",
  "optimized_prompt": "通过终极模板生成的优化后输入",
  "diagnosis": {
    "task_type": "...",
    "output_type": "...",
    "quality_target": "...",
    "failure_modes": []
  },
  "template_version": "v1"
}
```

这样后面的主 agent 就可以直接使用这些中间对象，而不是再次从零理解。

## 八 与终极模板的关系

你提到的 `prompt-generator.md` 中终极模板，非常适合作为这层的 **V1 默认优化策略**。

也就是说：

- 第一个版本用终极模板做默认优化器
- 后续如果积累到更多经验，可以替换或并行加入：
  - 轻量优化模板
  - 深度优先模板
  - 可执行性优先模板
  - 针对 Debug / Evaluate 的专用优化模板

所以终极模板不是直接写死在全系统里，而是被包装成：

**Default Optimization Strategy v1**

## 九 观测与实验要求

如果我们真的想验证这套 Prompt 优化的有效性，就必须记录中间层。

建议至少记录三层数据：

### 1. 原始输入

用户最初怎么说的。

### 2. 优化后输入 / 中间 Prompt

系统如何帮用户补结构、补术语、补边界。

### 3. 最终结果

最终返回给用户的结果是什么。

这样我们后续才能分析：

- 哪些场景下优化显著提升质量
- 哪些场景下优化过度
- 哪些输入不适合用当前模板

## 十 配置与开关建议

为了保证系统可演化，建议至少保留以下控制项：

### 1. 全局开关

- `prompt_optimization_enabled`

### 2. 模式级开关

- `generate_optimization_enabled`
- `debug_optimization_enabled`
- `evaluate_optimization_enabled`

### 3. 策略版本

- `optimization_strategy = default_v1`

### 4. 实验分流

后续可扩展为：

- `strategy = default_v1`
- `strategy = lite_v1`
- `strategy = depth_v1`

## 十一 对三种模式的差异化接入建议

### Generate 模式

这是最适合完整接入终极模板的模式。

因为 Generate 的目标本来就是把用户输入翻译成更高质量 Prompt。

### Debug 模式

Debug 模式不应机械套同一模板，而应使用 Debug 适配版本。重点不是重新定义需求，而是：

- 识别失败模式
- 判断缺失控制层
- 最小必要修复

### Evaluate 模式

Evaluate 模式也不应直接用 Generate 逻辑，而应优化成：

- 提高评估输入结构清晰度
- 确保评分维度一致
- 确保给出可行动的修复建议

因此，Prompt Optimization Layer 的 V1 可以共用核心原则，但最终建议演化为模式特化策略。

## 十二 落地建议

### 第一阶段

先在 Generate 模式中接入终极模板，形成 V1 默认优化层。

### 第二阶段

让 Debug / Evaluate 也接入各自适配优化器。

### 第三阶段

引入开关、观测和版本化策略。

### 第四阶段

引入实验能力，对比不同优化策略效果。

## 十三 最终建议

我的建议不是“不要接进去”，而是：

**一定要接进去，但要以 Prompt Optimization Layer 的形式接进去。**

这是产品级、agent 级的正确落法。

因为我们真正要做的不是把一个母模板写死，而是让“Prompt 优化”成为整个系统的第一层能力。

## 十四 最终结论

将终极模板直接写入执行流这个想法本身是正确的，而且非常有价值。

但最佳实现方式不是简单硬编码，而是构建：

- 默认开启
- 可配置
- 可观测
- 可回退
- 可演化

的 `Prompt Optimization Layer`。

这样我们就能一边开发产品，一边持续验证我们此前整套 Prompt Engineering 探索是否真的有效，并把这套能力逐步沉淀为产品真正的核心护城河。
