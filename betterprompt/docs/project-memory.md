# Project Memory

## Prompt Agent

### 2026-03-15 Continue / Debug / Evaluate 结果不更新问题

结论摘要：

- `Continue` 接口链路本身是通的，问题主要在前端结果展示与状态衔接
- `ResultPanel` 先渲染 `generate/debug/evaluate` 基础结果，导致成功返回的 `continueResult` 被遮挡
- `Evaluate` 模式的 Continue 之前错误地使用了 `top_issue` 作为继续优化输入，语义不成立
- `ContinueActions` 缺少明确的 loading / success 反馈，用户容易误判为“没有生效”
- 本次修复已完成：结果区会优先切到 Continue 新版本，Evaluate / Debug 的 Continue 会带上上一轮评估或诊断上下文，新一轮基础请求会清空陈旧 Continue 状态
- `continue` 后端已改成真实 LLM 调用，不再默认返回模板拼接产物；真实联调返回 `generation_backend="llm"`、`generation_model="deepseek-chat"`
- `continue` 现已严格禁止模板回退；如果没有可用 LLM 或上游失败，应直接报错而不是返回伪优化结果
- `continue` 现已支持流式输出；在 `Evaluate / Debug / Generate` 中点击继续优化时，结果区会实时滚动新文本
- `continue/stream` 已做真实上游联调，确认 SSE 会先发 `meta` 再持续发 `chunk`
- `Evaluate / Debug` 已从左右双栏改成上下单列工作流，长文本结果放到下方主结果区，不再挤在右侧窄栏

复用入口：

- 分析文档：`betterprompt/docs/prompt-agent-continue-debug-evaluate-chain-analysis-and-fix.md`

引用源：

- `frontend/src/features/prompt-agent/index.tsx`
- `frontend/src/features/prompt-agent/components/result-panel.tsx`
- `frontend/src/features/prompt-agent/components/continue-actions.tsx`
- `frontend/src/features/prompt-agent/components/mode-selector.tsx`
- `frontend/src/features/prompt-agent/hooks/use-prompt-agent-continue.ts`
- `frontend/src/features/prompt-agent/hooks/use-prompt-agent-evaluate.ts`
- `backend/app/api/v1/prompt_agent.py`
- `backend/app/services/prompt_agent/orchestrator.py`
