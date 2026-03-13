from app.schemas.prompt_agent import GeneratePromptRequest, PromptControlModule, PromptDiagnosis


class PromptGenerateEngine:
    system_prompt = (
        '你是 BetterPrompt 的 Prompt Compiler。'
        '你的任务是把用户的模糊需求、任务诊断和控制要求，编译成一份可以直接复制给另一个模型使用的高质量 Prompt。'
        '只输出最终 Prompt 正文，不要解释你的生成过程，不要输出代码块，不要补充额外说明。'
    )

    def build_prompt(self, request: GeneratePromptRequest, optimized_input: str, diagnosis: PromptDiagnosis, modules: list[PromptControlModule]) -> str:
        module_lines = {
            'problem_redefinition': '用户的描述是起点，不是边界。先识别问题真正属于什么，再组织回答。',
            'cognitive_drill_down': '不要停留在表层解释，必须分析关键结构、约束、代价与边界。',
            'key_point_priority': '不要平均分配篇幅，优先分析真正决定结果质量上限的少数关键点。',
            'criticality': '不要默认现有方案天然合理，要分析其代价、局限和失效方式。',
            'information_density': '每一段都必须提供新的判断、约束、洞察或区分。',
            'boundary_validation': '所有关键结论都必须说明前提、适用边界、失效条件和验证方式。',
            'executability': '最终输出必须收敛为可执行判断，明确下一步该做什么。',
            'style_control': '正文以自然、流畅、连贯的叙述性段落为主，避免模板腔与 AI 味。',
        }
        ordered_module_text = '\n'.join(f'- {module_lines[module]}' for module in modules)
        base_context = (
            f"任务诊断：\n"
            f"- 任务类型：{diagnosis.task_type}\n"
            f"- 输出产物：{diagnosis.output_type}\n"
            f"- 质量目标：{diagnosis.quality_target}\n"
            f"- 高风险失败模式：{', '.join(diagnosis.failure_modes)}\n\n"
            f"控制要求：\n{ordered_module_text}\n\n"
            f"原始优化输入：\n{optimized_input}\n"
        )
        artifact_templates = {
            'system_prompt': self._build_system_prompt_template(base_context),
            'task_prompt': self._build_task_prompt_template(base_context),
            'analysis_workflow': self._build_analysis_workflow_template(base_context),
            'conversation_prompt': self._build_conversation_prompt_template(base_context),
        }
        return artifact_templates[request.artifact_type]

    def build_messages(self, request: GeneratePromptRequest, optimized_input: str, diagnosis: PromptDiagnosis, modules: list[PromptControlModule]) -> tuple[str, str]:
        return self.system_prompt, self.build_prompt(request, optimized_input, diagnosis, modules)

    def _build_system_prompt_template(self, base_context: str) -> str:
        return (
            f"你是一位擅长把模糊需求翻译成高质量 Prompt 的 Prompt Agent。\n\n"
            f"请输出一份可长期复用的系统提示词，结构必须完整稳定。\n\n"
            f"必须按以下骨架组织：\n"
            f"1. 角色定位\n"
            f"2. 核心任务\n"
            f"3. 工作方法\n"
            f"4. 关键约束\n"
            f"5. 输出标准\n"
            f"6. 禁止事项\n\n"
            f"额外要求：\n"
            f"- 适合长期复用，而不是一次性对话\n"
            f"- 角色、方法、质量门槛和边界必须明确\n"
            f"- 最终结果必须可直接作为 system prompt 使用\n\n"
            f"输出要求：\n"
            f"- 直接输出最终 system prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n\n"
            f"{base_context}"
        )

    def _build_task_prompt_template(self, base_context: str) -> str:
        return (
            f"你是一位擅长把模糊需求翻译成高质量 Prompt 的 Prompt Agent。\n\n"
            f"请输出一份可一次性直接发送给模型执行的任务 Prompt。\n\n"
            f"必须按以下骨架组织：\n"
            f"1. 任务目标\n"
            f"2. 背景与输入信息\n"
            f"3. 具体执行要求\n"
            f"4. 输出格式\n"
            f"5. 质量标准\n\n"
            f"额外要求：\n"
            f"- 避免依赖额外解释或多轮澄清\n"
            f"- 任务指令必须直接、清晰、可执行\n"
            f"- 输出应是一份完整的一次性任务 Prompt\n\n"
            f"输出要求：\n"
            f"- 直接输出最终任务 Prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n\n"
            f"{base_context}"
        )

    def _build_analysis_workflow_template(self, base_context: str) -> str:
        return (
            f"你是一位擅长把模糊需求翻译成高质量 Prompt 的 Prompt Agent。\n\n"
            f"请输出一份适合复杂分析任务的工作流式 Prompt。\n\n"
            f"必须按以下骨架组织：\n"
            f"1. 分析目标\n"
            f"2. 阶段拆解\n"
            f"3. 每阶段关键问题\n"
            f"4. 判断节点与优先级\n"
            f"5. 验证方式\n"
            f"6. 最终交付标准\n\n"
            f"额外要求：\n"
            f"- 要体现先分析、再判断、再验证、再交付的顺序\n"
            f"- 适合复杂分析，不要写成普通问答指令\n"
            f"- 输出应是一份可直接复制使用的 workflow prompt\n\n"
            f"输出要求：\n"
            f"- 直接输出最终 workflow prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n\n"
            f"{base_context}"
        )

    def _build_conversation_prompt_template(self, base_context: str) -> str:
        return (
            f"你是一位擅长把模糊需求翻译成高质量 Prompt 的 Prompt Agent。\n\n"
            f"请输出一份适合多轮对话协作的 Prompt。\n\n"
            f"必须按以下骨架组织：\n"
            f"1. 对话目标\n"
            f"2. 首轮先做什么\n"
            f"3. 澄清问题策略\n"
            f"4. 多轮推进规则\n"
            f"5. 信息不足时的处理方式\n"
            f"6. 最终收敛标准\n\n"
            f"额外要求：\n"
            f"- 要求模型先澄清再推进，而不是直接假设全部上下文成立\n"
            f"- 适合多轮协作，不要写成单次执行指令\n"
            f"- 输出应体现持续对话中的节奏与决策收敛方式\n\n"
            f"输出要求：\n"
            f"- 直接输出最终对话协作 Prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n\n"
            f"{base_context}"
        )
