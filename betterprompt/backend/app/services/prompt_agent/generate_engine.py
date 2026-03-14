from app.schemas.prompt_agent import GeneratePromptRequest, PromptControlModule, PromptDiagnosis, PromptTaskType

# Per-task-type role definition sentence
TASK_ROLE_SENTENCE: dict[PromptTaskType, str] = {
    'algorithm_analysis': '你是一位精通算法与数据结构的 Prompt Agent，擅长将算法问题的核心约束转化为高质量指令。',
    'source_code_analysis': '你是一位资深代码审查专家型 Prompt Agent，擅长将源码理解需求转化为结构化分析指令。',
    'architecture_spec': '你是一位系统架构师型 Prompt Agent，擅长将架构设计需求转化为可执行的技术方案指令。',
    'business_insight': '你是一位商业分析师型 Prompt Agent，擅长将商业洞察需求转化为深度分析指令。',
    'product_design': '你是一位产品设计专家型 Prompt Agent，擅长将模糊的产品需求转化为清晰可落地的设计指令。',
    'data_analysis': '你是一位数据分析专家型 Prompt Agent，擅长将数据分析目标转化为结构化的分析工作指令。',
    'education_learning': '你是一位教学设计专家型 Prompt Agent，擅长将学习目标转化为循序渐进的教学指令。',
    'creative_marketing': '你是一位创意营销专家型 Prompt Agent，擅长将营销目标转化为有感染力的创作指令。',
    'writing_generation': '你是一位写作与编辑专家型 Prompt Agent，擅长将写作需求转化为风格精准的创作指令。',
    'general_deep_analysis': '你是一位擅长把模糊需求翻译成高质量 Prompt 的 Prompt Agent。',
}

# Short and long versions for each module instruction
MODULE_INSTRUCTIONS: dict[PromptControlModule, dict[str, str]] = {
    'problem_redefinition': {
        'short': '先识别问题真正属于什么，再组织回答。',
        'long': '用户的描述是起点，不是边界。先判断用户真正想解决的问题是什么——它可能不是字面表述的那个问题。重新定义后再组织回答，确保方向正确。',
    },
    'cognitive_drill_down': {
        'short': '必须分析关键结构、约束、代价与边界。',
        'long': '不要停留在表层解释。对每个关键论点，追问：为什么是这样？代价是什么？机制如何运作？边界在哪里？用层层递进的方式揭示深层逻辑。',
    },
    'key_point_priority': {
        'short': '优先分析真正决定结果质量上限的少数关键点。',
        'long': '不要平均分配篇幅。识别出 2-3 个真正决定结果质量上限的关键点，用 80% 的分析深度聚焦这些点，其余内容简要带过。明确说明为什么这些是关键点。',
    },
    'criticality': {
        'short': '分析现有方案的代价、局限和失效方式。',
        'long': '不要默认现有方案天然合理。对每个被推荐的方案或结论，主动分析：它的代价是什么？在什么条件下会失效？有没有更优的替代？保持建设性批判。',
    },
    'information_density': {
        'short': '每一段都必须提供新的判断、约束、洞察或区分。',
        'long': '删除所有不提供新信息的句子。每一段都必须至少包含一个新判断、新约束、新洞察或新区分。如果一段话去掉后不影响结论，则不应存在。',
    },
    'boundary_validation': {
        'short': '所有关键结论都必须说明前提、适用边界和失效条件。',
        'long': '对每个关键结论，明确：它成立的前提是什么？适用边界在哪里？在什么条件下会失效？如何验证它是否正确？不接受无条件的绝对结论。',
    },
    'executability': {
        'short': '最终输出必须收敛为可执行判断。',
        'long': '最终输出必须收敛为可执行的判断和行动。明确下一步该做什么、怎么做、成功标准是什么。避免停留在"建议参考"层面，要给出具体可落地的指导。',
    },
    'style_control': {
        'short': '以自然、流畅的叙述为主，避免模板腔。',
        'long': '正文以自然、流畅、连贯的叙述性段落为主。避免"首先/其次/最后"的模板结构，避免空洞的总结句，避免 AI 味的客套话。让每句话都像专家在认真讨论问题。',
    },
}

# Task complexity: determines whether to use long or short module instructions
COMPLEX_TASK_TYPES: set[PromptTaskType] = {
    'algorithm_analysis', 'source_code_analysis', 'architecture_spec',
    'business_insight', 'product_design', 'data_analysis', 'general_deep_analysis',
}


class PromptGenerateEngine:
    system_prompt = (
        '你是 BetterPrompt 的 Prompt Compiler。'
        '你的任务是把用户的模糊需求、任务诊断和控制要求，编译成一份可以直接复制给另一个模型使用的高质量 Prompt。'
        '只输出最终 Prompt 正文，不要解释你的生成过程，不要输出代码块，不要补充额外说明。'
    )

    def _get_module_version(self, task_type: PromptTaskType) -> str:
        return 'long' if task_type in COMPLEX_TASK_TYPES else 'short'

    def _get_role_sentence(self, task_type: PromptTaskType) -> str:
        return TASK_ROLE_SENTENCE.get(task_type, TASK_ROLE_SENTENCE['general_deep_analysis'])

    def build_prompt(self, request: GeneratePromptRequest, optimized_input: str, diagnosis: PromptDiagnosis, modules: list[PromptControlModule]) -> str:
        version = self._get_module_version(diagnosis.task_type)
        ordered_module_text = '\n'.join(
            f'- {MODULE_INSTRUCTIONS[module][version]}' for module in modules
        )
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
            'system_prompt': self._build_system_prompt_template(base_context, diagnosis.task_type),
            'task_prompt': self._build_task_prompt_template(base_context, diagnosis.task_type),
            'analysis_workflow': self._build_analysis_workflow_template(base_context, diagnosis.task_type),
            'conversation_prompt': self._build_conversation_prompt_template(base_context, diagnosis.task_type),
        }
        return artifact_templates[request.artifact_type]

    def build_messages(self, request: GeneratePromptRequest, optimized_input: str, diagnosis: PromptDiagnosis, modules: list[PromptControlModule]) -> tuple[str, str]:
        return self.system_prompt, self.build_prompt(request, optimized_input, diagnosis, modules)

    def _build_system_prompt_template(self, base_context: str, task_type: PromptTaskType) -> str:
        role = self._get_role_sentence(task_type)
        return (
            f"{role}\n\n"
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

    def _build_task_prompt_template(self, base_context: str, task_type: PromptTaskType) -> str:
        role = self._get_role_sentence(task_type)
        return (
            f"{role}\n\n"
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

    def _build_analysis_workflow_template(self, base_context: str, task_type: PromptTaskType) -> str:
        role = self._get_role_sentence(task_type)
        return (
            f"{role}\n\n"
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

    def _build_conversation_prompt_template(self, base_context: str, task_type: PromptTaskType) -> str:
        role = self._get_role_sentence(task_type)
        return (
            f"{role}\n\n"
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
