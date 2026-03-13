# Prompt Product Frontend Specification

## 一 文档目的

本文件定义独立 Prompt 产品 `Prompt Studio` 的前端 MVP 规格。目标是把 PRD 和 API 规格转化为可开发的前端信息架构、页面结构、组件职责、状态设计和交互流程。

本规格严格围绕独立 Prompt 产品，不依附于任何特定行业产品语境。

## 二 前端产品目标

前端 MVP 要实现的不是一个复杂平台，而是一个清晰、低门槛、可直接使用的 Prompt Compiler 界面。用户进入产品后，不应该先学习系统结构，而应该立即理解：

- 在这里输入一句需求
- 系统会输出一个成品 Prompt
- 如果 Prompt 不好，可以调试
- 如果不确定质量，可以评估

因此，前端设计目标可以压缩为三点：

### 目标 1

让第一次使用的用户在最短时间内完成第一次成功生成。

### 目标 2

让用户能够清楚区分 Generate / Debug / Evaluate 三种模式。

### 目标 3

让结果区的“可直接复制使用”成为最强主动作。

## 三 信息架构

MVP 建议采用单页面多模式结构，而不是多页面深层跳转结构。

```text
Prompt Studio
├── Header
├── Mode Tabs
│   ├── Generate
│   ├── Debug
│   └── Evaluate
├── Main Workspace
│   ├── Input Panel
│   ├── Optional Settings Panel
│   └── Result Panel
└── Optional History Panel
```

这样做的好处是：

- 学习成本低
- 模式切换清晰
- 有利于后续扩展历史、预设和模块视图

## 四 页面级结构

### 1. 主页面

推荐页面名称：`Prompt Studio`

建议页面路径概念：

```text
/prompt-studio
```

页面分为四个区域：

- 顶部标题区
- 模式切换区
- 主工作区
- 结果展示区

如果后期增加历史记录，可以将其作为右侧侧栏，不应一开始压过主工作流。

## 五 三种模式定义

### 模式一：Generate

这是默认模式，也是产品核心。

#### 输入内容

- 一句话需求或任务描述

#### 可选设置

- 是否显示诊断摘要
- 输出偏好：
  - 平衡
  - 深度优先
  - 可执行性优先
  - 自然文风优先

#### 输出内容

- 诊断摘要
- 最终 Prompt
- 一键复制按钮

#### 目标体验

用户能在一次输入后拿到可以直接复制使用的 Prompt。

### 模式二：Debug

这是产品差异化能力的核心部分。

#### 输入内容

- 原始任务
- 当前 Prompt
- 当前输出

#### 输出内容

- 失败模式判断
- 缺失控制层
- 最小必要修复
- 修复后的 Prompt
- 一键复制按钮

#### 目标体验

用户不再依赖盲改 Prompt，而是知道 Prompt 为什么不好、怎么修。

### 模式三：Evaluate

这是产品闭环能力的关键。

#### 输入内容

- 一个 Prompt
- 或一个输出文本

#### 输出内容

- 分项评分
- 总分
- 最主要缺陷
- 最优先补层

#### 目标体验

用户能快速判断 Prompt 或输出是否达标，而不是只靠感觉。

## 六 关键组件拆分建议

### 1. `prompt-studio-page`

页面级容器，负责整体布局和模式切换。

### 2. `mode-tabs`

负责切换：

- Generate
- Debug
- Evaluate

### 3. `generate-panel`

Generate 模式输入区域。

职责：

- 管理一句需求输入
- 管理可选设置
- 触发生成请求

### 4. `debug-panel`

Debug 模式输入区域。

职责：

- 管理三个输入框
- 触发调试请求

### 5. `evaluate-panel`

Evaluate 模式输入区域。

职责：

- 管理目标文本输入
- 管理评估目标类型选择
- 触发评估请求

### 6. `result-card`

统一结果展示卡片。

职责：

- 展示诊断摘要
- 展示 Prompt / 评分 / 修复建议
- 展示复制按钮

### 7. `diagnosis-block`

用于展示任务类型、输出目标、质量目标和失败模式。

### 8. `copy-button`

高优先级交互按钮。应始终出现在最终 Prompt 或修复结果旁边。

### 9. `history-sidebar`（可选）

MVP 可先不做。如果做，也应是弱化存在，不应打断主流程。

## 七 推荐前端目录结构

```text
frontend/src/features/prompt-studio/
├── index.tsx
├── components/
│   ├── mode-tabs.tsx
│   ├── generate-panel.tsx
│   ├── debug-panel.tsx
│   ├── evaluate-panel.tsx
│   ├── result-card.tsx
│   ├── diagnosis-block.tsx
│   ├── score-breakdown.tsx
│   └── history-sidebar.tsx
├── hooks/
│   ├── use-prompt-generate.ts
│   ├── use-prompt-debug.ts
│   └── use-prompt-evaluate.ts
└── types.ts
```

## 八 页面交互流程

### Generate 流程

```text
用户输入一句需求
-> 点击 Generate
-> 页面进入 loading 状态
-> 返回诊断摘要 + 最终 Prompt
-> 用户点击 Copy
```

### Debug 流程

```text
用户输入原始任务 + 当前 Prompt + 当前输出
-> 点击 Debug
-> 页面进入 loading 状态
-> 返回失败模式 + 修复建议 + 修复后的 Prompt
-> 用户点击 Copy
```

### Evaluate 流程

```text
用户输入 Prompt 或输出文本
-> 点击 Evaluate
-> 页面进入 loading 状态
-> 返回评分 + 缺陷 + 建议补层
```

## 九 状态设计建议

MVP 前端至少需要这几类状态：

### 页面模式状态

- `generate`
- `debug`
- `evaluate`

### 请求状态

- `idle`
- `loading`
- `success`
- `error`

### 表单状态

按模式分离维护，不要共享同一份复杂表单对象。

### 结果状态

按模式分离：

- generateResult
- debugResult
- evaluateResult

## 十 关键交互原则

### 原则 1：结果区必须突出最终 Prompt

无论是生成还是调试，最终 Prompt 都必须是结果区的主角，而不是诊断说明。

### 原则 2：复制动作必须足够明显

对于这个产品来说，复制是最关键动作之一。复制按钮必须足够显著。

### 原则 3：诊断信息默认可见但不压主内容

诊断摘要很重要，但不应喧宾夺主。建议用折叠卡片或较轻层级展示。

### 原则 4：模式切换必须清晰

Generate / Debug / Evaluate 必须让用户一眼看懂区别，不能让三个模式的输入框相互混淆。

### 原则 5：错误反馈必须明确

如果请求失败，应明确告诉用户：

- 是输入缺失
- 还是服务调用失败
- 还是结果生成失败

不能只显示模糊错误。

## 十一 UI 风格建议

产品定位是 Prompt Compiler，因此 UI 应强调：

- 简洁
- 清晰
- 工具感
- 信息分层明确
- 结果导向

不建议做成聊天式气泡体验，因为那会弱化“编译 Prompt”的产品心智。

更适合的风格是：

- 左侧输入 / 右侧结果
- 或上下结构：输入在上，结果在下
- 模式切换采用清晰 Tabs
- 输出采用卡片式分区

## 十二 MVP 展示字段建议

### Generate 结果卡

- 任务类型
- 输出目标
- 质量目标
- 高风险失败模式
- 最终 Prompt
- Copy 按钮

### Debug 结果卡

- 顶层失败模式
- 缺失控制层
- 最小必要修复
- 修复后的 Prompt
- Copy 按钮

### Evaluate 结果卡

- 分项评分
- 总分
- 最主要缺陷
- 最优先补层

## 十三 错误与空状态建议

### 空状态

Generate 空状态示例：

- 输入一句需求，系统会为你生成可直接使用的 Prompt

Debug 空状态示例：

- 输入任务、当前 Prompt 和当前输出，系统会帮你定位问题并修复

Evaluate 空状态示例：

- 输入一个 Prompt 或输出文本，系统会为你评估质量

### 错误状态

错误提示应尽量具体，例如：

- 请输入一句需求
- 当前 Prompt 不能为空
- 当前输出不能为空
- 评估目标不能为空
- 生成失败，请稍后重试

## 十四 响应式建议

MVP 阶段应至少兼容：

- 桌面优先
- 平板可用
- 移动端可降级但不必追求完整最优

推荐桌面端布局：

- 宽屏双栏
- 窄屏单栏堆叠

## 十五 MVP 不做的前端内容

为了控制实现复杂度，前端 MVP 先不做：

- 可视化模块拖拽装配器
- Prompt 历史高级搜索
- 多 Prompt 并排对比工作台
- 团队协作面板
- 用户资产库管理系统
- 图谱式 Prompt 路由可视化

## 十六 前端开发优先级建议

按以下顺序最合理：

1. `Prompt Studio` 单页框架
2. Generate 模式
3. Debug 模式
4. Evaluate 模式
5. 统一结果卡与 Copy 能力
6. 可选 History

## 十七 最终说明

这份前端规格的目标，不是追求一次性完整，而是确保 MVP 有清晰结构、低学习成本和强结果导向。

Prompt Studio 的前端必须始终围绕一个核心体验来设计：

**让用户用最少输入，得到最可直接使用的 Prompt 结果。**
