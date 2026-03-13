from app.schemas.prompt_agent import DebugPromptRequest


class PromptDebugEngine:
    def fix_prompt(self, request: DebugPromptRequest, minimal_fix: list[str]) -> str:
        fixes = '\n'.join(f'- {item}' for item in minimal_fix)
        return (
            f"你需要完成的原始任务是：\n{request.original_task}\n\n"
            f"请在保留原始意图的前提下，使用下面这版修复后的 Prompt 执行：\n\n"
            f"{request.current_prompt}\n\n"
            f"补充修复要求：\n{fixes}\n\n"
            f"执行要求：\n"
            f"- 先重定义问题，再决定回答路径\n"
            f"- 不要停留在表层复述，必须解释关键原因、约束与代价\n"
            f"- 对关键判断说明适用边界、失效条件与验证方式\n"
            f"- 最终结论必须收敛到可执行建议\n"
            f"- 正文保持自然、连贯、非模板化表达"
        )
