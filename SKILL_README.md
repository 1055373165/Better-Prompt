# Prompt Engineering Skill Package

## Overview

这是一个将自然语言需求编译为高质量成品 Prompt 的技能包。它不是单纯的 Prompt 模板集合，也不是一份理论手册，而是一套可复用、可调试、可评估、可集成的 Prompt Engineering 结构化系统。

这个 skill package 的核心目标是：

- 用户只输入一句需求、一个问题或一个模糊目标
- 系统自动识别任务类型、输出目标、质量目标和高风险失败模式
- 系统自动装配合适的控制模块
- 最终输出一份可直接复制使用的 Prompt

换句话说，这套包的本质不是帮助用户“手写 Prompt”，而是帮助系统“编译 Prompt”。

## Package Files

当前 skill package 由以下文件组成：

- `prompt-engineering-skill.md`
  - 单文件总说明，适合作为聚合版技能包说明

- `skill-overview.md`
  - 技能定位、核心价值、适用场景、触发条件、能力边界

- `skill-contract.md`
  - 输入契约、输出契约、运行协议、质量要求

- `skill-invocation.md`
  - 默认调用模板、调试模式模板、评估模式模板、Prompt-only 模式

- `skill-integration.md`
  - 行为模式、任务类型路由、失败模式修复路由、集成建议、发布定位

## Quick Start

如果你只想最快开始使用，建议按下面顺序：

### Option A: 直接调用

直接使用 `skill-invocation.md` 中的默认调用模板。

适合场景：

- 你已经知道这个 skill 是干什么的
- 你只想快速把一句需求变成成品 Prompt

### Option B: 先理解技能边界

先读：

- `skill-overview.md`
- `skill-contract.md`

再使用：

- `skill-invocation.md`

适合场景：

- 你要把这个技能交给团队使用
- 你要做产品化或系统化集成
- 你希望明确这个 skill 的输入输出契约

### Option C: 做产品或系统集成

推荐阅读顺序：

- `skill-overview.md`
- `skill-contract.md`
- `skill-integration.md`
- `skill-invocation.md`

适合场景：

- 你要把这个 skill 接入应用、网页、插件或自动化系统
- 你要设计一个面向最终用户的 Prompt 生成入口

## Recommended Default Entry

如果整个 skill package 只保留一个默认入口，建议使用下面这个模式：

- 参考文件：`skill-invocation.md`
- 使用模板：`Default Invocation Template`

这是当前最推荐的默认入口，因为它兼顾了：

- 使用门槛低
- 输出透明
- 可直接复制使用
- 容易扩展到调试和评估模式

## Runtime Model

这个 skill package 的运行逻辑可以压缩成以下闭环：

```text
输入一句需求
-> 识别任务类型
-> 识别输出目标
-> 识别质量目标
-> 预判失败模式
-> 装配控制模块
-> 组装五层 Prompt
-> 输出最终 Prompt
```

当输入是已有 Prompt 或 bad output 时，则切换为：

```text
输入原始任务 + 当前 Prompt + 当前输出
-> 识别失败模式
-> 判断缺失控制层
-> 做最小必要修复
-> 输出修复后的 Prompt
```

## Package Design Principles

这个 skill package 建立在以下原则之上：

- 用户的描述是起点，不是边界
- 用户输入越短，系统越要主动补结构
- Prompt 质量依赖控制结构，而不是语言华丽度
- 调试 Prompt 比重写 Prompt 更重要
- Skill 应隐藏复杂性，而不是把复杂性转嫁给用户

## What Makes This Package Different

与普通 Prompt 模板库相比，这个 package 的区别在于：

- 它不是固定模板集合，而是带路由和控制模块装配逻辑的系统
- 它不仅支持生成，还支持调试和评估
- 它不仅告诉你“写什么”，还定义了“何时触发什么结构”
- 它更接近 Prompt Compiler，而不是 Prompt Snippet List

## Suggested Usage Levels

### Level 1: Personal Use

你自己使用时，只需要：

- 阅读 `skill-invocation.md`
- 直接调用默认模板

### Level 2: Team Use

团队内部使用时，建议统一：

- `skill-overview.md` 作为技能说明
- `skill-contract.md` 作为输入输出规范
- `skill-invocation.md` 作为标准调用入口

### Level 3: Product Use

做产品化时，建议：

- 前台只暴露一句需求输入框
- 后台按 `skill-contract.md` 和 `skill-integration.md` 实现路由与装配
- 默认返回成品 Prompt，可选显示诊断摘要

## Suggested Next Step

如果你要继续把这个 package 做得更像真正可发布的 skill，最推荐的下一步是新增：

- `SKILL_RELEASE_NOTES.md`

它可以用于记录：

- 当前版本定位
- 核心能力
- 适用场景
- 与前一版相比的升级点
- 后续演化方向

## Final Principle

这个 skill package 的本质，不是写 Prompt，而是编译 Prompt。

只要它能把自然语言需求稳定转换成高质量成品 Prompt，并且整个过程具备输入输出契约、路由逻辑、调试能力和评估能力，它就已经是一个真正成熟的 Prompt Engineering skill package。
