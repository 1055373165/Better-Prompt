from app.schemas.prompt_agent import ContinuePromptRequest


class PromptContinueEngine:
    system_prompt = (
        '你是 BetterPrompt 的 Continue Optimization Agent。'
        '你的职责是基于上一版结果、当前优化目标和补充上下文，直接产出新的最终版本。'
        '如果输入本身是一份 Prompt，那么输出也必须仍是一份可直接发送给目标模型执行的 Prompt。'
        '不要解释优化过程，不要复述任务，不要输出代码块或额外说明。'
        '只输出重写后的最终内容。'
    )

    @staticmethod
    def _context_block(request: ContinuePromptRequest) -> str:
        context_notes = (request.context_notes or '').strip()
        if not context_notes:
            return ''
        return f"本轮可参考的上下文：\n{context_notes}"

    def build_messages(self, request: ContinuePromptRequest) -> tuple[str, str]:
        return self.system_prompt, self.refine(request)

    def refine(self, request: ContinuePromptRequest) -> str:
        if request.mode == 'generate':
            return self._refine_generate(request)
        if request.mode == 'debug':
            return self._refine_debug(request)
        return self._refine_evaluate(request)

    def _refine_generate(self, request: ContinuePromptRequest) -> str:
        previous = request.previous_result.strip()
        goal = request.optimization_goal.strip()
        context_block = self._context_block(request)
        context_section = f"{context_block}\n\n" if context_block else ''
        return (
            f"你是一位继续打磨 Prompt 成品的高级 Prompt Agent。\n\n"
            f"以下是上一版结果，请在保留其有效结构的前提下，直接重写为更强版本，而不是追加解释或备注。\n\n"
            f"本轮优化目标：{goal}\n\n"
            f"{context_section}"
            f"重写要求：\n"
            f"- 保留上一版中已经有效的角色、任务定义、结构骨架与质量门槛\n"
            f"- 重点增强与“{goal}”直接相关的判断、约束、表达精度和可执行性\n"
            f"- 删除重复、空泛、模板化表达\n"
            f"- 最终输出必须仍是一版可以直接复制使用的完整 Prompt 成品\n"
            f"- 不要输出“优化说明”“修改建议”“补充要求”这类元说明\n\n"
            f"请直接重写这版 Prompt：\n{previous}"
        )

    def _refine_debug(self, request: ContinuePromptRequest) -> str:
        previous = request.previous_result.strip()
        goal = request.optimization_goal.strip()
        context_block = self._context_block(request)
        context_section = f"{context_block}\n\n" if context_block else ''
        return (
            f"你是一位继续修复 Prompt 的高级 Prompt Agent。\n\n"
            f"以下是上一版修复结果，请基于它直接重写出更稳的一版修复后 Prompt，而不是继续追加修复说明。\n\n"
            f"本轮重点修复：{goal}\n\n"
            f"{context_section}"
            f"重写要求：\n"
            f"- 不改变原始任务意图\n"
            f"- 优先修复仍影响稳定性、边界、判断强度或可执行性的问题\n"
            f"- 如果结构已基本完整，则重点增强关键判断、约束和验证方式\n"
            f"- 最终输出必须仍是一版修复后的完整 Prompt 成品\n"
            f"- 不要输出“继续修复要求”“补充说明”“修改理由”这类元说明\n\n"
            f"请直接重写这版修复后 Prompt：\n{previous}"
        )

    def _refine_evaluate(self, request: ContinuePromptRequest) -> str:
        previous = request.previous_result.strip()
        goal = request.optimization_goal.strip()
        context_block = self._context_block(request)
        context_section = f"{context_block}\n\n" if context_block else ''
        return (
            f"你是一位根据评估结果继续提升内容质量的高级 Prompt Agent。\n\n"
            f"以下是上一版待优化内容，请围绕评估暴露的问题直接重写出更强版本，而不是重复评估结论。\n\n"
            f"本轮优化目标：{goal}\n\n"
            f"{context_section}"
            f"重写要求：\n"
            f"- 优先修复上一轮最弱质量层相关问题\n"
            f"- 同时补强整体稳定性、约束意识、判断强度和执行清晰度\n"
            f"- 最终输出必须是更强版本的实际内容，而不是评语或分析说明\n"
            f"- 不要输出“优化说明”“评估结论复述”“进一步增强要求”这类元说明\n\n"
            f"请直接重写这版内容：\n{previous}"
        )
