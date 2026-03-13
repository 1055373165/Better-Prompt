# Skill Contract

## Input Contract

本技能包必须接受以下输入形态：

- 一句话需求
- 一个问题
- 一段原始任务描述
- 一段已有 Prompt
- 原始任务 + 当前 Prompt + 当前输出

如果输入信息不足，系统必须自动补足最常见且最有价值的控制结构，而不是要求用户先学习 Prompt Engineering 术语。

## Output Contract

### Default Output

默认输出两部分：

```text
诊断摘要：
- 任务类型：
- 输出产物：
- 质量目标：
- 高风险失败模式：

可直接使用的最终 Prompt：
【完整成品 Prompt】
```

### Prompt-Only Output

如果用户明确只需要成品 Prompt，则只输出最终 Prompt。

### Debug Output

如果用户输入的是已有 Prompt 或 bad output，则输出：

```text
失败模式判断：
缺失控制层：
最小必要修复：
修复后的 Prompt：
```

### Evaluation Output

如果用户要求评估 Prompt 或输出质量，则输出：

```text
评分项：
总分：
最主要缺陷：
最优先补的控制层：
```

## Runtime Protocol

### Step 1: Identify Task Type

识别用户输入更接近哪一类任务：

- 算法分析型
- 源码分析型
- 架构规格型
- 商业洞察型
- A 股分析型
- 通用深度分析型
- 写作生成型
- Prompt 调试型
- 其他

### Step 2: Identify Intended Output

识别用户真正想要的输出产物：

- 分析文章
- 研究报告
- 规格文档
- 评审意见
- 决策建议
- 可直接使用的 Prompt
- 调试后的 Prompt
- 其他

### Step 3: Identify Quality Priority

识别用户更看重什么：

- 深度
- 可执行性
- 批判性
- 清晰度
- 自然文风
- 结构完整
- 决策价值

### Step 4: Predict Failure Modes

预判任务最容易滑向哪些低质量输出：

- 表层复述
- 模板腔
- 正确废话
- 伪深度
- 无批判赞美
- 面面俱到无判断
- 不可执行
- 风格不稳

### Step 5: Inject Control Modules

从控制模块层中自动选择合适模块：

- 问题重定义
- 认知下钻
- 关键点优先
- 批判性
- 信息密度
- 边界与验证
- 可执行性
- 风格控制

### Step 6: Assemble Final Prompt

将模块装配进以下五层结构：

- 角色层
- 问题重定义层
- 认知路径层
- 质量门槛层
- 全局文风层

### Step 7: Return Final Artifact

输出完整、可直接复制使用的最终 Prompt。

## Quality Requirements

本技能包输出的最终 Prompt 必须满足以下要求：

- 不只是头衔堆砌
- 不只是任务复述
- 必须包含明确控制结构
- 必须能压制高频失败模式
- 必须能直接复制使用
- 必须尽量减少模板腔
- 必须在必要时收敛为可执行判断
