# Prompt Agent Continue / Debug / Evaluate 链路分析与修复记录

## 背景

本次问题来自 Prompt Agent Workspace 的交互闭环：

- 用户在 `Generate / Debug / Evaluate` 任一模式下拿到结果
- 点击“下一步可以继续优化”中的动作按钮
- 前端实际发起 `POST /api/v1/prompt-agent/continue`
- 但页面没有明显变化，也没有给出正在处理或处理完成的反馈

同时，`Debug` 与 `Evaluate` 模式也被用户感知为“有功能问题”，需要一并排查。

## 影响范围

- `Generate` 模式下的 Continue Optimization
- `Debug` 模式下的 Continue Optimization
- `Evaluate` 模式下的 Continue Optimization
- 与上述能力相关的结果展示、状态切换和用户反馈

## 链路分析

### 1. Continue 请求链路本身是通的

前端 Continue 按钮链路：

1. `ContinueActions` 触发 `onSelect`
2. 页面层在 `index.tsx` 中调用 `continueMutation.mutate(...)`
3. `usePromptAgentContinue` 发送 `POST /prompt-agent/continue`
4. 后端 `prompt_agent.py` 进入 `continue_optimization`
5. `PromptAgentOrchestrator.continue_optimization()` 返回 `ContinuePromptResponse`

对应源码：

- `frontend/src/features/prompt-agent/components/continue-actions.tsx`
- `frontend/src/features/prompt-agent/index.tsx`
- `frontend/src/features/prompt-agent/hooks/use-prompt-agent-continue.ts`
- `backend/app/api/v1/prompt_agent.py`
- `backend/app/services/prompt_agent/orchestrator.py`

结论：

- 网络请求不是根因
- 后端接口也不是“没返回”
- 问题主要出在前端状态如何进入 UI

### 2. 根因一：ResultPanel 的分支顺序遮掉了 Continue 结果

`ResultPanel` 当前渲染顺序是：

1. `generateResult`
2. `debugResult`
3. `evaluateResult`
4. 最后才是 `continueResult`

这意味着：

- 只要当前模式已经有基础结果
- Continue 请求即使成功返回
- `continueResult` 仍会被前面的基础结果分支覆盖

直接后果：

- 用户点了继续优化
- 网络请求成功
- 但页面仍显示旧结果
- 用户主观感受就是“没生效”

对应源码：

- `frontend/src/features/prompt-agent/components/result-panel.tsx`

### 3. 根因二：页面层传入了原始 continue 数据，但没有按当前 mode 做显示优先级控制

页面层已经计算了：

- `activeContinueResult`
- `currentResultText`
- `latestActions`

其中 `activeContinueResult` 已经按 `source_mode === mode` 做了过滤。

但传给 `ResultPanel` 的却仍是：

- `continueMutation.data ?? null`

而不是过滤后的 `activeContinueResult`。

这会导致两个问题：

- 当前模式的 Continue 结果没有被优先展示
- 模式切换后如果状态没及时清理，理论上还可能把上一模式的 continue 数据带进结果区判断

对应源码：

- `frontend/src/features/prompt-agent/index.tsx`

### 4. 根因三：Evaluate 模式的 Continue 源文本取错了

页面层现在用于 Continue 的 `currentResultText` 来自：

- Generate: `final_prompt`
- Debug: `fixed_prompt`
- Evaluate: `top_issue`

其中 `Evaluate` 的这条最有问题。

`top_issue` 只是评估结论中的一句问题描述，不是用户真正要继续优化的目标文本。

因此 Evaluate 模式当前的 Continue 实际上是在让系统“继续优化一条诊断句子”，而不是：

- 原始被评估的 Prompt
- 或原始被评估的输出内容

直接后果：

- 就算 Continue 结果展示出来
- 语义上也不对
- 用户会觉得 Evaluate 模式“功能不正常”

对应源码：

- `frontend/src/features/prompt-agent/index.tsx`
- `frontend/src/features/prompt-agent/hooks/use-prompt-agent-evaluate.ts`

### 5. 根因四：Continue 没有任何过程反馈或成功提示

`ContinueActions` 当前只做了两件事：

- 请求中禁用按钮
- 无其他状态提示

缺失的反馈包括：

- 正在基于哪个目标继续优化
- 优化成功后结果区已切换
- 优化失败时与当前动作的关联提示

这会让用户在“请求已发出但结果被遮挡”时，更强烈地感知为“什么都没发生”。

对应源码：

- `frontend/src/features/prompt-agent/components/continue-actions.tsx`

### 6. 关于 `mode-selector.tsx#L18-19`

`mode-selector.tsx#L18-19` 中的 `Debug / Evaluate` 文案本身不是根因。

真正的问题是：

- 这些模式对应的 Continue 链路也复用了同一套结果展示逻辑
- 所以同样会被 ResultPanel 的基础结果分支遮挡
- 尤其 `Evaluate` 还叠加了“继续优化源文本取错”的问题

也就是说：

- `ModeSelector` 暴露了功能入口
- 但问题发生在进入模式之后的结果状态流

对应源码：

- `frontend/src/features/prompt-agent/components/mode-selector.tsx`

## 修复目标

本次修复应同时覆盖四件事：

1. Continue 成功后结果区必须真正切到新结果
2. Continue 过程必须有明确反馈
3. Evaluate 模式 Continue 必须基于被评估的原始文本，而不是 `top_issue`
4. 当用户重新发起新的 Generate / Debug / Evaluate 请求时，旧的 Continue 状态应被清理，避免污染新结果

## 修复落地

本次已经完成以下修复：

### 0. Continue 后端从模板拼接升级为真实 LLM 调用

此前 `PromptAgentOrchestrator.continue_optimization()` 只是直接调用 `continue_engine.refine(request)` 并返回，所以接口虽然名义上是“继续优化”，实际上只是返回一段“交给另一个模型去优化”的指令模板，没有真正完成优化。

本次修复后：

- `continue` 会像 `generate` 一样优先尝试调用默认 LLM client
- `continue` 不再允许模板回退；无论全局是否开启 fallback，这条链都必须走真实 LLM
- 响应体新增 `generation_backend` 和 `generation_model`

结果：

- Continue 现在是真实模型生成
- 前端也可以明确显示这次优化到底来自 `llm` 还是 `template`
- 如果 LLM 未配置或上游失败，接口会显式返回错误，而不是伪装成“优化成功”

### 1. 结果区优先展示当前 mode 的 Continue 结果

- 页面层现在把过滤后的 `activeContinueResult` 传给 `ResultPanel`
- `ResultPanel` 调整了分支优先级，只要当前模式存在 Continue 结果，就先展示优化后版本

结果：

- Continue 请求成功后，结果区会直接切到新的优化结果
- `Generate / Debug / Evaluate` 三种模式都走同一套正确逻辑

### 2. Continue 按钮增加了明确的进行中 / 完成反馈

- 请求进行中会显示“正在基于某个目标继续优化”
- 当前被点击的按钮会出现 loading 态
- 成功后会显示“当前结果区显示的是优化后版本”

结果：

- 用户不再需要靠猜测判断是否已经生效

### 3. Evaluate Continue 改为基于被评估原文继续优化

- Continue 的源文本从 `evaluate.target_text` 获取，而不是 `top_issue`
- 同时把评估结论作为 `context_notes` 传给后端 Continue 引擎
- 后端在继续优化时会把“最主要缺陷 / 建议优先修复层 / 总分解读”等上下文一起注入

结果：

- Evaluate 模式现在是在“继续改原文”
- 而不是“继续改一条诊断句子”

### 4. Debug Continue 也补上了诊断上下文

- 把 `top_failure_mode`
- `weaknesses`
- `missing_control_layers`

一并作为 `context_notes` 传入后端，避免继续优化时失去上一轮诊断信息。

### 5. 新一轮基础请求会清理旧 Continue 状态

- 用户重新发起 `Generate / Debug / Evaluate` 请求前，会先 `reset` Continue 状态

结果：

- 不会再出现上一轮 Continue 结果污染新一轮基础结果区的问题

### 6. Continue 支持实时流式输出

此前 Continue 虽然已经改成真实 LLM 调用，但前端仍然只等最终响应返回后再整体替换结果，所以用户在 `Evaluate` 模式下只会看到按钮进入 loading，而看不到文本逐步生成。

本次继续补齐：

- 后端新增 `/prompt-agent/continue/stream`
- 前端 Continue hook 改为基于 SSE 的流式读取
- `ResultPanel` 在 `Generate / Debug / Evaluate` 三个模式下都能在 Continue 进行中显示实时生成中的文本

结果：

- 点击“基于评估重生成一版”等 Continue 动作后，结果区会立即显示流式输出
- 不再只有按钮 loading 而没有正文变化

### 7. Evaluate / Debug 的长结果从右侧窄栏提升为下方主结果区

此前 `Evaluate / Debug` 复用了“左输入、右结果”的双栏布局，这适合展示评分摘要或短诊断，但不适合承载 Continue 产生的长文本结果。

本次改动后：

- `Evaluate` 改成“上方评估，下方结果”
- `Debug` 改成“上方诊断，下方结果”
- 长文本结果、实时生成和继续优化按钮都集中到下方主结果区

结果：

- 结果成为主舞台，而不是挤在右侧窄栏里的附属信息
- 评估结论与优化后版本的阅读顺序更自然

## 验证记录

- `npm run build` 通过
- `betterprompt/backend/.venv/bin/python -m compileall betterprompt/backend/app` 通过
- `PromptContinueEngine` 运行时冒烟验证通过，确认 `context_notes` 已进入 Continue 提示词拼装链路
- 真实上游联调通过：`continue_optimization()` 返回 `generation_backend="llm"`、`generation_model="deepseek-chat"`
- 真实流式联调通过：`continue_optimization_stream()` 已验证会先发送 `meta`，再连续发送 `chunk`

## 引用源

- `frontend/src/features/prompt-agent/index.tsx`
- `frontend/src/features/prompt-agent/components/result-panel.tsx`
- `frontend/src/features/prompt-agent/components/continue-actions.tsx`
- `frontend/src/features/prompt-agent/components/mode-selector.tsx`
- `frontend/src/features/prompt-agent/hooks/use-prompt-agent-continue.ts`
- `frontend/src/features/prompt-agent/hooks/use-prompt-agent-evaluate.ts`
- `backend/app/api/v1/prompt_agent.py`
- `backend/app/services/prompt_agent/orchestrator.py`
- `backend/app/services/prompt_agent/continue_engine.py`
