# Prompt Agent MVP Implementation Plan

## 一 文档目标

本文件用于把 `Prompt Agent` 的产品方案与架构方案转化为可执行的第一版实施计划。目标不是再补充概念，而是明确：

- MVP 第一版到底做什么
- 前后端分别先实现什么
- agent 编排层先落哪些能力
- 哪些功能延后
- 实施顺序如何安排

这份文档应作为开发启动时的直接基线。

## 二 MVP 产品目标重述

Prompt Agent MVP 只聚焦一件事：

**让个人用户输入一段话后，可以在 Generate / Debug / Evaluate 三种模式中选择一种，并得到一个可以直接使用或继续优化的结果。**

如果第一版无法稳定完成这件事，那么就不应继续扩展更多功能。

## 三 MVP 范围锁定

### MVP 必做能力

#### 1. Generate

输入一句需求，输出：

- 诊断摘要
- 成品系统提示词
- 可继续优化入口

#### 2. Debug

输入原始任务 + 当前 Prompt + 当前输出，输出：

- Prompt 优势
- Prompt 弱点
- 顶层失败模式
- 缺失控制层
- 最小必要修复
- 修复后的 Prompt
- 可继续优化入口

#### 3. Evaluate

输入 Prompt 或输出，输出：

- 分项评分
- 总分
- 最主要缺陷
- 最优先修复建议
- 可继续优化入口

#### 4. Continue Optimization

在每个结果页给出“继续优化”入口，让 agent 基于上一步结果继续产生增强版本。

### MVP 暂不做能力

- 团队协作
- Prompt marketplace
- 高级资产库
- 多模型 benchmark
- 可视化模块编辑器
- 复杂多 agent 协作
- 长周期自治 agent

## 四 技术实现策略

### 总策略

采用 **单 agent 编排器 + 多模式引擎** 的实现方式，而不是多个完全自治 agent。

这是因为 MVP 的目标是稳定性、可控性和快速交付，而不是展示 agent 复杂度。

### 具体策略

- 一个总 orchestrator 负责状态推进
- 三个核心引擎负责不同模式
- 一个统一的模块路由层负责 Prompt 控制结构注入
- 一个会话记忆层负责 Continue Optimization
- 一个统一的结果格式化层负责前端展示对象

## 五 后端实施计划

### 阶段 1：建立 API 壳层

目标：先建立后端接口边界与数据结构。

建议新增：

- `backend/app/api/v1/prompt_agent.py`
- `backend/app/schemas/prompt_agent.py`
- `backend/app/services/prompt_agent_service.py`

#### API 范围

- `POST /api/v1/prompt-agent/generate`
- `POST /api/v1/prompt-agent/debug`
- `POST /api/v1/prompt-agent/evaluate`
- `POST /api/v1/prompt-agent/continue`

### 阶段 2：建立 orchestrator 和引擎骨架

建议新增：

- `backend/app/services/prompt_agent/orchestrator.py`
- `backend/app/services/prompt_agent/task_understanding.py`
- `backend/app/services/prompt_agent/diagnosis.py`
- `backend/app/services/prompt_agent/module_router.py`
- `backend/app/services/prompt_agent/generate_engine.py`
- `backend/app/services/prompt_agent/debug_engine.py`
- `backend/app/services/prompt_agent/evaluate_engine.py`
- `backend/app/services/prompt_agent/result_formatter.py`
- `backend/app/services/prompt_agent/memory_service.py`

### 阶段 3：打通 Generate 模式

优先级最高。

Generate 模式跑通后，产品才真正有第一条可用主路径。

最低要求：

- 正确识别任务类型
- 给出诊断摘要
- 返回完整成品 Prompt
- 支持 Prompt-only 输出

### 阶段 4：打通 Debug 模式

Debug 模式是产品差异化关键。

最低要求：

- 能从输入中识别失败模式
- 能输出缺失控制层
- 能给出最小必要修复
- 能输出修复后的 Prompt

### 阶段 5：打通 Evaluate 模式

最低要求：

- 能输出结构化评分
- 能给出最主要缺陷
- 能输出建议补层

### 阶段 6：打通 Continue Optimization

最低要求：

- 同一会话内保留上一轮结果
- 用户可以基于上一轮结果继续增强
- 能区分继续优化方向，例如：
  - 更深
  - 更可执行
  - 更自然
  - 针对最低分项修复

## 六 前端实施计划

### 阶段 1：页面框架

建议新增：

- `frontend/src/features/prompt-agent/index.tsx`

页面最小结构：

- 标题区
- 模式切换区
- 输入区
- 结果区
- Continue Optimization 区

### 阶段 2：组件骨架

建议新增：

- `components/mode-selector.tsx`
- `components/generate-panel.tsx`
- `components/debug-panel.tsx`
- `components/evaluate-panel.tsx`
- `components/result-panel.tsx`
- `components/diagnosis-card.tsx`
- `components/score-card.tsx`
- `components/continue-actions.tsx`

### 阶段 3：数据 hooks

建议新增：

- `hooks/use-prompt-agent-generate.ts`
- `hooks/use-prompt-agent-debug.ts`
- `hooks/use-prompt-agent-evaluate.ts`
- `hooks/use-prompt-agent-continue.ts`

### 阶段 4：状态管理

MVP 阶段建议使用 feature 内局部状态为主，不急于引入复杂全局状态。

但应明确保留：

- 当前模式
- 当前输入
- 当前结果
- 当前会话上一步结果

## 七 Agent 编排层实施计划

### MVP 需要落地的最佳实践

#### 1. 明确模式分流

先识别模式，再进入不同流程。

#### 2. 明确中间状态对象

不要让所有逻辑都混在一次 LLM 输出里。

#### 3. 明确控制模块路由

必须把控制模块层作为一等公民，而不是隐式逻辑。

#### 4. 会话级短期记忆

支持 Continue Optimization，但暂不做长期复杂记忆。

#### 5. 明确最小必要修复原则

Debug 模式必须避免动辄重写一切。

#### 6. 结构化评估内置

Evaluate 模式必须是产品一等能力，而不是后补。

## 八 推荐开发顺序

### Sprint 1

- 落地后端 schemas 和 API 路由壳层
- 落地前端页面骨架和模式切换
- 落地 Generate 模式最小闭环

### Sprint 2

- 落地 Debug 模式
- 落地 Evaluate 模式
- 完成统一结果展示组件

### Sprint 3

- 落地 Continue Optimization
- 补充会话级记忆
- 增强 Copy / Compare / Re-run 体验

## 九 每阶段验收标准

### Generate 验收标准

- 输入一句需求可得到结构化诊断和成品 Prompt
- Prompt 可复制
- Prompt 结果不退化为纯解释文

### Debug 验收标准

- 能识别至少一个主要失败模式
- 能输出至少一项缺失控制层
- 能给出一版修复后的 Prompt

### Evaluate 验收标准

- 能输出固定维度评分
- 能输出总分
- 能指出最主要缺陷与建议补层

### Continue Optimization 验收标准

- 能基于上一轮结果做下一轮增强
- 不丢失当前会话上下文
- 用户能显式触发继续优化

## 十 风险控制

### 风险 1：开发一开始就做得过重

控制方式：

- 先打通 Generate
- 再补 Debug
- 再补 Evaluate
- 最后做 Continue Optimization

### 风险 2：把 agent 做成黑盒聊天

控制方式：

- 所有模式必须返回结构化中间结果
- 所有结果页都要有明确标签

### 风险 3：控制模块层只停留在文档中

控制方式：

- 在服务端单独实现 module router
- 在调试和评估结果中显式返回缺失层或已用模块

## 十一 实施后的下一阶段

当 MVP 跑通后，下一阶段可做：

- Prompt 版本链
- Prompt 历史记录
- 偏好预设
- 常见任务快捷入口
- Prompt 对比视图

## 十二 最终说明

这份实施计划的目标，是确保 Prompt Agent 的 MVP 能够以最短路径跑出可用闭环，而不是陷入功能发散。

MVP 的唯一衡量标准不是文档写得多，而是：

**用户输入一段话，选择一种模式，系统给出一个可直接使用并且可继续优化的结果。**

只要这一点稳定成立，Prompt Agent 就已经进入了真正的产品阶段。
