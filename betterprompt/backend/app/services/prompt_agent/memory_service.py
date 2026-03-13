class PromptMemoryService:
    def build_continue_context(self, previous_result: str, optimization_goal: str) -> str:
        return (
            f"请基于上一轮结果继续优化，不要推翻已有有效部分，只增强本轮目标对应的质量层。\n\n"
            f"上一轮结果：\n{previous_result}\n\n"
            f"本轮优化目标：{optimization_goal}\n\n"
            f"输出要求：\n"
            f"- 直接输出优化后的完整新版本\n"
            f"- 不要先解释准备增强哪一层，也不要写优化说明\n"
            f"- 尽量保持原有有效结构，只修真正影响质量上限的部分\n"
        )
