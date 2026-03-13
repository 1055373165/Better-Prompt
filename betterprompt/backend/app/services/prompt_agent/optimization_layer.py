from app.schemas.prompt_agent import GeneratePromptRequest, PromptDiagnosis


ULTIMATE_TEMPLATE_HEADER = """我会给你一句需求、一个问题，或者一个模糊目标。\n\n你的任务不是直接回答，而是先把它编译成一份可以直接使用的高质量 Prompt。\n\n你必须自动完成以下工作：\n1. 识别任务类型\n2. 识别用户真正想要的输出产物\n3. 识别用户最在意的质量目标\n4. 识别这个任务最容易出现的低质量输出\n5. 自动补足最合适的角色定义、问题重定义、认知路径、质量门槛和文风约束\n6. 输出一份可以直接复制使用的最终 Prompt\n"""


class PromptOptimizationLayer:
    strategy_name = 'default_ultimate_template_v1'

    def optimize_generate_input(self, request: GeneratePromptRequest, diagnosis: PromptDiagnosis) -> str:
        return (
            f"{ULTIMATE_TEMPLATE_HEADER}\n"
            f"请优先遵守以下原则：\n"
            f"- 用户的描述是起点，不是边界\n"
            f"- 不要停留在表层复述，先识别问题本质\n"
            f"- 不要输出模板腔、正确废话或伪深度\n"
            f"- 如果任务需要判断或建议，必须补足边界、失效条件和可执行性\n"
            f"- 正文风格应自然、连贯、信息密度高\n\n"
            f"当前推断任务类型：{diagnosis.task_type}\n"
            f"当前偏好：{diagnosis.quality_target}\n\n"
            f"我的需求是：\n{request.user_input}"
        )
