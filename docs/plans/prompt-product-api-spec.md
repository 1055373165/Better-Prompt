# Prompt Product API Specification

## 一 文档目的

本文件定义独立 Prompt 产品 `Prompt Studio` 的 MVP API 契约。目标不是一次性覆盖未来所有能力，而是为 MVP 的三种核心模式提供稳定、清晰、可开发的接口规范：

- Generate
- Debug
- Evaluate

本规格严格围绕独立 Prompt 产品，不依附于任何特定行业业务语境。

## 二 设计原则

### 原则 1：前端输入尽量简单

前端尽量只传递最小必要信息，复杂的任务识别、失败模式预判、模块装配在服务端完成。

### 原则 2：返回结构化结果，而不是只返回文本

服务端不仅要返回最终 Prompt，也要返回诊断信息、修复信息或评估信息，以支持 UI 分层展示。

### 原则 3：模式显式化

生成、调试、评估是三种不同工作模式，应明确分离，不混在单个大接口里。

### 原则 4：输出可直接使用

所有核心接口的返回结果都必须包含可直接复制使用的核心产物。

## 三 API 范围

MVP API 包含三个主接口：

- `POST /api/v1/prompt-product/generate`
- `POST /api/v1/prompt-product/debug`
- `POST /api/v1/prompt-product/evaluate`

可选扩展接口：

- `GET /api/v1/prompt-product/presets`
- `GET /api/v1/prompt-product/history`
- `POST /api/v1/prompt-product/copy-event`

其中前三个是 MVP 必做，后三个是可选增强。

## 四 通用约定

### Content-Type

```text
application/json
```

### Response Envelope

所有成功响应统一使用：

```json
{
  "success": true,
  "data": {}
}
```

所有失败响应统一使用：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

## 五 Generate API

### Endpoint

```text
POST /api/v1/prompt-product/generate
```

### 用途

将一句需求、一个问题或一段原始任务描述编译成可直接使用的高质量 Prompt。

### Request Body

```json
{
  "user_input": "帮我把这个问题变成一个高质量 prompt",
  "show_diagnosis": true,
  "output_preference": "balanced",
  "prompt_only": false,
  "context_notes": "optional"
}
```

### 字段说明

- `user_input`
  - 类型：`string`
  - 必填
  - 用户原始输入，一句话需求或任务描述

- `show_diagnosis`
  - 类型：`boolean`
  - 可选
  - 默认：`true`
  - 是否返回诊断摘要

- `output_preference`
  - 类型：`string`
  - 可选
  - 可选值：`balanced | depth | execution | natural`
  - 默认：`balanced`
  - 控制生成结果偏好

- `prompt_only`
  - 类型：`boolean`
  - 可选
  - 默认：`false`
  - 如果为 `true`，前端可只展示最终 Prompt

- `context_notes`
  - 类型：`string`
  - 可选
  - 用户额外说明

### Response Body

```json
{
  "success": true,
  "data": {
    "mode": "generate",
    "diagnosis": {
      "task_type": "source_code_analysis",
      "output_type": "analysis_prompt",
      "quality_target": "depth",
      "failure_modes": [
        "surface_restatement",
        "template_tone"
      ]
    },
    "final_prompt": "完整成品 Prompt 文本",
    "applied_modules": [
      "problem_redefinition",
      "cognitive_drill_down",
      "criticality",
      "style_control"
    ]
  }
}
```

### Response 字段说明

- `mode`
  - 固定为 `generate`

- `diagnosis`
  - 任务诊断摘要

- `task_type`
  - 任务类型，例如：
    - `algorithm_analysis`
    - `source_code_analysis`
    - `architecture_spec`
    - `business_insight`
    - `a_share_analysis`
    - `general_deep_analysis`
    - `writing_generation`
    - `other`

- `output_type`
  - 输出产物类型

- `quality_target`
  - 当前主质量目标

- `failure_modes`
  - 预判的高风险失败模式列表

- `final_prompt`
  - 可直接复制使用的成品 Prompt

- `applied_modules`
  - 实际装配的控制模块列表

## 六 Debug API

### Endpoint

```text
POST /api/v1/prompt-product/debug
```

### 用途

对已有 Prompt 和已有输出进行结构化调试，输出最小必要修复后的 Prompt。

### Request Body

```json
{
  "original_task": "帮我分析这段代码",
  "current_prompt": "当前 Prompt 内容",
  "current_output": "当前输出内容",
  "output_preference": "balanced"
}
```

### 字段说明

- `original_task`
  - 类型：`string`
  - 必填
  - 原始任务描述

- `current_prompt`
  - 类型：`string`
  - 必填
  - 当前使用的 Prompt

- `current_output`
  - 类型：`string`
  - 必填
  - 当前生成的输出结果

- `output_preference`
  - 类型：`string`
  - 可选
  - 默认：`balanced`

### Response Body

```json
{
  "success": true,
  "data": {
    "mode": "debug",
    "diagnosis": {
      "top_failure_mode": "surface_restatement",
      "missing_control_layers": [
        "problem_redefinition",
        "cognitive_drill_down"
      ]
    },
    "minimal_fix": [
      "补充问题重定义层",
      "补充认知下钻层"
    ],
    "fixed_prompt": "修复后的 Prompt 文本"
  }
}
```

### Response 字段说明

- `top_failure_mode`
  - 当前最主要失败模式

- `missing_control_layers`
  - 缺失的关键控制层

- `minimal_fix`
  - 最小必要修复建议列表

- `fixed_prompt`
  - 修复后的完整 Prompt

## 七 Evaluate API

### Endpoint

```text
POST /api/v1/prompt-product/evaluate
```

### 用途

对一个 Prompt 或一个输出文本做结构化质量评估。

### Request Body

```json
{
  "target_text": "需要评估的 Prompt 或输出内容",
  "target_type": "prompt"
}
```

### 字段说明

- `target_text`
  - 类型：`string`
  - 必填
  - 待评估文本

- `target_type`
  - 类型：`string`
  - 必填
  - 可选值：`prompt | output`

### Response Body

```json
{
  "success": true,
  "data": {
    "mode": "evaluate",
    "score_breakdown": {
      "problem_fit": 4,
      "constraint_awareness": 3,
      "information_density": 4,
      "judgment_strength": 3,
      "executability": 2,
      "natural_style": 4,
      "overall_stability": 3
    },
    "total_score": 23,
    "top_issue": "缺少可执行性",
    "suggested_fix_layer": "executability"
  }
}
```

### 评分维度

- `problem_fit`
  - 是否真正回应问题本质

- `constraint_awareness`
  - 是否识别关键约束、边界、代价与失败模式

- `information_density`
  - 是否具有足够信息密度

- `judgment_strength`
  - 是否给出了明确判断

- `executability`
  - 是否可执行或可决策

- `natural_style`
  - 是否文风自然、避免模板腔

- `overall_stability`
  - 是否整体稳定

## 八 错误码建议

### 通用错误码

- `INVALID_REQUEST`
  - 请求缺少必要字段或格式错误

- `EMPTY_INPUT`
  - 输入为空

- `UNSUPPORTED_TARGET_TYPE`
  - `target_type` 非法

- `GENERATION_FAILED`
  - 生成失败

- `DEBUG_FAILED`
  - 调试失败

- `EVALUATION_FAILED`
  - 评估失败

- `INTERNAL_ERROR`
  - 服务内部异常

## 九 数据类型建议

### TaskType

```text
algorithm_analysis
source_code_analysis
architecture_spec
business_insight
a_share_analysis
general_deep_analysis
writing_generation
other
```

### FailureMode

```text
surface_restatement
template_tone
correct_but_empty
pseudo_depth
uncritical_praise
no_priority_judgment
not_executable
style_instability
```

### ControlModule

```text
problem_redefinition
cognitive_drill_down
key_point_priority
criticality
information_density
boundary_validation
executability
style_control
```

## 十 后端服务职责建议

建议后端服务层承担以下职责：

- 任务类型识别
- 输出产物识别
- 质量目标识别
- 失败模式预判
- 控制模块路由
- 五层 Prompt 装配
- 调试模式修复
- 评估模式评分

建议抽象服务名：

- `PromptProductService`

内部可以再细分为：

- `PromptDiagnosisEngine`
- `PromptAssemblyEngine`
- `PromptDebugEngine`
- `PromptEvaluationEngine`

## 十一 非功能要求

### 响应时间

MVP 阶段优先保证结果质量，其次再优化性能。目标是：

- Generate：可接受在数秒级
- Debug：可接受在数秒级
- Evaluate：应尽量更快

### 可解释性

所有模式都应尽量返回结构化中间结果，以支持产品前端展示，而不是只返回黑盒文本。

### 可扩展性

API 设计应预留后续扩展空间，例如：

- Prompt 历史记录
- 预设模式
- 团队共享 Prompt 资产
- 任务模板与模块可视化

## 十二 MVP 实现优先级

建议按以下顺序实现：

1. Generate API
2. Debug API
3. Evaluate API
4. 可选 History / Presets 扩展

## 十三 最终说明

这份 API 规格不是通用 AI 服务规范，而是独立 Prompt 产品的 MVP 契约。它的目标是确保产品的三种核心模式具备稳定、清晰、可实现的接口基础，为后续前端实现和服务端落地提供统一边界。
