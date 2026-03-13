# Prompt Product MVP Plan

## 一 结论

当前这套 Prompt Engineering 体系已经达到了可以产品化的门槛，而且更准确地说，已经具备一个 `Prompt Compiler / Prompt OS MVP` 的雏形。继续增加文档和模板的边际收益已经开始下降，下一步最有价值的动作不是继续扩展理论，而是收敛成一个最小可用产品：用户输入一句需求，系统输出可直接使用的成品 Prompt，并支持生成、调试、评估三种工作模式。

这意味着，接下来产品化的核心任务不再是“再写一版手册”，而是把现有文档体系转化成一套清晰的产品边界、交互流程和最小实现路径。

## 二 产品定位

这个产品不是一个普通的 Prompt 模板库，也不是一个 AI 聊天壳。它的核心定位应当是：

**一个把自然语言需求编译成高质量 Prompt 的 Prompt Compiler。**

产品最小心智模型可以非常简单：

- 用户输入一句需求
- 系统先理解任务类型与目标
- 系统自动补足控制结构
- 系统输出成品 Prompt
- 用户可选继续做调试或评估

因此，它本质上不是在“帮用户写答案”，而是在“帮用户写更强的 Prompt”。

## 三 为什么现在已经可以产品化

当前体系已经具备产品化最关键的五个基础。

第一，已经有相对完整的方法论闭环，包括 Playbook、Quick Reference、Examples、Control Modules、Generator、Skill Package。这说明系统不再是零散经验，而是具有明确结构。

第二，已经形成了统一的 Prompt 五层结构：角色层、问题重定义层、认知路径层、质量门槛层、全局文风层。这意味着系统已经有稳定的 Prompt 装配骨架。

第三，已经有显式的控制模块层与路由规则，说明系统不是只能“生成 prompt”，而是知道为什么这样生成。这是可解释性和可调试性的基础。

第四，已经有生成、调试、评估三种模式，说明产品最关键的工作流不是单点能力，而是完整闭环。

第五，当前仓库本身已经具备 AI 前后端能力，包括：

- 后端已有 AI API 与 skills 结构
- 前端已有 AI provider、AI chat、AI task panel 等组件
- 已有适合扩展的文档规划目录

因此，从产品化角度看，真正缺的不是技术基础，而是产品定义与 MVP 收敛。

## 四 产品目标用户

第一类用户，是需要频繁与大模型协作，但不会系统写 Prompt 的知识工作者。他们最典型的需求是：我不想研究 Prompt Engineering，但我想直接得到高质量 Prompt。

第二类用户，是已经会写一点 Prompt，但结果不稳定的进阶用户。他们需要的不是更多模板，而是更稳定的编译器、更可解释的装配过程和更可调试的修复路径。

第三类用户，是团队、产品或平台集成方。他们需要的不是单条 Prompt，而是一套可以接入工作流、能够统一质量标准的 Prompt 生成系统。

## 五 MVP 产品目标

MVP 不应该试图覆盖所有能力，而应聚焦三个最小可用结果：

### 目标一：一句需求生成成品 Prompt

这是最核心路径，也是产品存在的第一理由。

### 目标二：已有 Prompt 的最小必要调试

这是第二高频场景，也是把产品从“模板库”拉向“工程工具”的关键。

### 目标三：对 Prompt 或输出做质量评估

这是让产品具备闭环能力的必要环节。

换句话说，MVP 只需要三种模式：

- Generate
- Debug
- Evaluate

## 六 MVP 信息架构

最推荐的 MVP 信息架构如下：

```text
Prompt Product
├── Generate
├── Debug
├── Evaluate
├── Prompt History
└── Module / Preset (可先弱化或隐藏)
```

### 1. Generate

用户输入一句需求，系统输出：

- 诊断摘要
- 成品 Prompt

可以增加两个可选开关：

- 是否显示诊断摘要
- 输出更偏深度 / 更偏可执行性 / 更偏自然文风

### 2. Debug

用户输入：

- 原始任务
- 当前 Prompt
- 当前输出

系统输出：

- 失败模式判断
- 缺失控制层
- 最小必要修复
- 修复后的 Prompt

### 3. Evaluate

用户输入：

- 一个 Prompt
- 或者一个输出结果

系统输出：

- 评分项
- 总分
- 最主要缺陷
- 最优先补的控制层

### 4. Prompt History

MVP 可以先做最简单版本，只保留最近历史，不一定一开始就做复杂管理。

### 5. Module / Preset

对于 MVP，模块层不一定要前台完全暴露。更合理的做法是后台自动调用，前台只在高级模式下显示。

## 七 MVP 用户流程

### 流程 A：生成模式

```text
输入一句需求
-> 系统识别任务类型
-> 系统装配控制模块
-> 系统生成成品 Prompt
-> 用户复制使用
```

### 流程 B：调试模式

```text
输入原始任务 + 当前 Prompt + 当前输出
-> 系统识别失败模式
-> 系统判断缺失控制层
-> 系统给出最小必要修复
-> 输出修复后的 Prompt
```

### 流程 C：评估模式

```text
输入 Prompt 或输出
-> 系统打分
-> 系统指出主要缺陷
-> 系统建议优先补哪一层
```

## 八 MVP 的产品原则

### 原则一：一句需求优先

用户必须能够只输入一句需求就开始使用。不要强迫用户填写复杂表单。

### 原则二：复杂性放在后台

控制模块、任务路由、失败模式映射这些复杂逻辑，应尽量在后台自动完成。前台不应暴露太多工程细节。

### 原则三：先交付成品，再展示解释

默认应先给用户可直接使用的成品 Prompt。诊断和解释可以是可选展开内容，而不是默认强制阅读的前置步骤。

### 原则四：调试能力比更多模板更重要

产品差异化不应建立在模板数量上，而应建立在：当 Prompt 不好时，系统能否告诉用户为什么不好、该怎么修。

## 九 前端产品形态建议

基于当前仓库已有 AI 前端基础，MVP 最适合做成一个独立 feature 页面，而不是先深度嵌进现有股票分析流程。

推荐页面结构：

```text
Prompt Studio
├── 模式切换 Tabs: Generate / Debug / Evaluate
├── 主输入区
├── 可选高级设置
├── 结果展示区
└── 历史记录侧栏（可选）
```

### Generate 页

输入框：一句需求

可选项：

- 显示诊断摘要
- 偏好：深度 / 可执行性 / 自然文风

输出区：

- 诊断摘要
- 最终 Prompt
- 一键复制

### Debug 页

三个输入框：

- 原始任务
- 当前 Prompt
- 当前输出

输出区：

- 失败模式
- 缺失控制层
- 修复建议
- 修复后的 Prompt

### Evaluate 页

输入一个 Prompt 或一个输出文本

输出区：

- 分项评分
- 总分
- 最主要缺陷
- 最优先补层

## 十 后端能力建议

从当前仓库看，已有 AI API 和 AI skills 能力，因此 MVP 后端最合理方式不是另起炉灶，而是：

- 新增一个 Prompt Product 专用 skill / endpoint
- 内部复用当前 skill package 逻辑
- 输出结构化 JSON，而不是只输出纯文本

建议 MVP 的后端能力至少包括：

### 1. Generate Endpoint

输入：

- user_request
- mode_preferences 可选

输出：

- task_type
- output_type
- quality_target
- failure_modes
- final_prompt

### 2. Debug Endpoint

输入：

- original_task
- current_prompt
- current_output

输出：

- failure_mode
- missing_control_layers
- minimal_fix
- fixed_prompt

### 3. Evaluate Endpoint

输入：

- prompt_or_output
- evaluate_target_type

输出：

- scores
- total_score
- top_issue
- suggested_fix_layer

## 十一 与现有仓库的落点建议

基于当前结构，最推荐的文档与实现落点如下。

### 文档落点

- `docs/plans/prompt-product-mvp.md` 作为 MVP 总方案
- 后续再补：
  - `docs/plans/prompt-product-prd.md`
  - `docs/plans/prompt-product-api-spec.md`
  - `docs/plans/prompt-product-frontend-spec.md`

### 前端落点建议

优先考虑新建独立 feature，而不是混进现有股票页面：

- `frontend/src/features/prompt-studio/`

页面可包含：

- `index.tsx`
- `components/generate-panel.tsx`
- `components/debug-panel.tsx`
- `components/evaluate-panel.tsx`
- `components/result-card.tsx`

### 后端落点建议

可基于现有 AI skills / chat 能力扩展：

- `backend/app/api/v1/prompt_product.py`
- `backend/app/services/prompt_product_service.py`
- 或者作为 `ai_skills.py` 的新 skill 分类接入

## 十二 MVP 范围边界

为了防止第一版失控，必须明确不做什么。

### MVP 先不做

- 大规模 Prompt 模板市场
- 团队协作与权限系统
- 复杂 Prompt 版本管理
- 多模型自动 benchmark
- 高级可视化模块编辑器
- 完整知识库和案例广场

### MVP 先做

- 一句话生成 Prompt
- Prompt 调试
- Prompt 评估
- 一键复制
- 基础历史记录（可选）

## 十三 版本路线建议

### V0

文档化完成，产品边界明确，技能包清晰。

### V1 MVP

完成 Generate / Debug / Evaluate 三模式的最小可用产品。

### V1.5

加入历史记录、预设偏好、常见任务快捷入口。

### V2

加入模块可视化、团队协作、Prompt 资产管理、质量反馈闭环。

## 十四 立即建议

如果现在开始产品化，最合理的下一步不是直接开始无边界编码，而是按下面顺序推进：

1. 先锁定 Prompt Product 的 PRD
2. 再锁定后端 API 契约
3. 再锁定前端信息架构和交互
4. 最后开始实现 MVP

## 十五 最终判断

这次对 Prompt Engineering 的探索，已经达到了可以产品化的水平。

理由不是“文档写得够多”，而是因为它已经具备了产品化所需的四个关键要素：

- 清晰的产品对象：一句需求 -> 成品 Prompt
- 清晰的结构骨架：五层 Prompt 结构
- 清晰的中间层：控制模块与失败模式映射
- 清晰的闭环能力：生成、调试、评估

从这个节点开始，最重要的不是继续写更多 Prompt，而是把它做成真正能被用户使用的产品。
