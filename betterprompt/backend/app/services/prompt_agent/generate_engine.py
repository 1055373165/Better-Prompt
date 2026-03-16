from app.schemas.prompt_agent import GeneratePromptRequest, PromptControlModule, PromptDiagnosis, PromptTaskType

# Per-task-type role definition sentence
TASK_ROLE_SENTENCE: dict[PromptTaskType, str] = {
    'algorithm_analysis': '你擅长为算法与数据结构问题设计高质量分析 Prompt。',
    'source_code_analysis': '你擅长为源码理解、代码审查和调试场景设计结构化 Prompt。',
    'architecture_spec': '你擅长为系统设计和架构方案场景设计可执行的技术 Prompt。',
    'business_insight': '你擅长为商业分析和行业研究场景设计高信息密度 Prompt。',
    'product_design': '你擅长为产品设计和需求分析场景设计清晰可落地的 Prompt。',
    'data_analysis': '你擅长为数据分析与指标洞察场景设计结构化 Prompt。',
    'education_learning': '你擅长为教学和学习场景设计循序渐进的 Prompt。',
    'creative_marketing': '你擅长为创意营销和品牌表达场景设计有感染力的 Prompt。',
    'writing_generation': '你擅长为写作、改写和内容生成场景设计风格明确的 Prompt。',
    'document_translation': '你擅长为文档翻译、本地化和版面保真场景设计可直接执行的 Prompt。',
    'general_deep_analysis': '你擅长把模糊需求整理成可直接执行的高质量 Prompt。',
}

TASK_SPECIAL_REQUIREMENTS: dict[PromptTaskType, list[str]] = {
    'document_translation': [
        '如果用户输入涉及 PDF、图书、论文或扫描文档，必须把版面结构识别与块级对齐写成明确执行要求。',
        '必须明确标题、段落、列表、表格、图注、脚注、公式、页眉页脚、页码和引用的处理策略。',
        '必须要求术语、专有名词、缩写和章节编号在全文中保持一致；必要时先建立术语表再翻译。',
        '如果用户强调对照一致性，必须要求输出保留中英映射关系，并按段落、块或编号对齐。',
        '必须写出遇到排版歧义、OCR 噪声、缺页或结构冲突时的回退规则，避免模型擅自补写。',
        '除非用户明确要求分阶段交付，否则不要先输出结构分析摘要或计划说明；应直接服务于最终翻译结果，只在异常位置做显式标注。',
    ],
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
    'business_insight', 'product_design', 'data_analysis', 'document_translation', 'general_deep_analysis',
}


class PromptGenerateEngine:
    system_prompt = (
        '你是 BetterPrompt 的 Prompt Architect。'
        '你的职责是识别用户原始 Prompt 背后的真实元需求，并把它重写成最终可执行的高质量 Prompt 产物。'
        '默认交付对象是用户下一步要发送给目标模型的 Prompt，而不是另一个用于生成 Prompt 的元提示词。'
        '除非用户明确要求，否则不要把执行模型设定成 Prompt Agent、Prompt Compiler 或类似的提示词代理。'
        '除非用户明确要求，否则不要平白增加分析摘要、计划说明、分阶段交付或自我解释。'
        '只输出最终 Prompt 正文，不要解释你的生成过程，不要输出代码块，不要补充额外说明。'
        '即使需要示例，也请用普通文本描述，不要插入 Markdown fenced code block。'
    )

    def _get_module_version(self, task_type: PromptTaskType) -> str:
        return 'long' if task_type in COMPLEX_TASK_TYPES else 'short'

    def _get_role_sentence(self, task_type: PromptTaskType) -> str:
        return TASK_ROLE_SENTENCE.get(task_type, TASK_ROLE_SENTENCE['general_deep_analysis'])

    def _build_task_specific_requirements(self, task_type: PromptTaskType) -> str:
        requirements = TASK_SPECIAL_REQUIREMENTS.get(task_type, [])
        if not requirements:
            return ''
        return '任务专用要求：\n' + '\n'.join(f'- {item}' for item in requirements) + '\n\n'

    def build_prompt(self, request: GeneratePromptRequest, optimized_input: str, diagnosis: PromptDiagnosis, modules: list[PromptControlModule]) -> str:
        version = self._get_module_version(diagnosis.task_type)
        ordered_module_text = '\n'.join(
            f'- {MODULE_INSTRUCTIONS[module][version]}' for module in modules
        )
        task_specific_requirements = self._build_task_specific_requirements(diagnosis.task_type)
        base_context = (
            f"用户任务简报：\n{optimized_input}\n\n"
            f"任务诊断：\n"
            f"- 任务类型：{diagnosis.task_type}\n"
            f"- 输出产物：{diagnosis.output_type}\n"
            f"- 质量目标：{diagnosis.quality_target}\n"
            f"- 高风险失败模式：{', '.join(diagnosis.failure_modes) or '—'}\n\n"
            f"控制要求：\n{ordered_module_text}\n\n"
            f"{task_specific_requirements}"
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
            f"请输出一份可长期复用的系统提示词，用于稳定支撑同类任务执行。\n\n"
            f"优先覆盖以下内容，可以自然组织，不必机械照抄标题：\n"
            f"1. 角色定位\n"
            f"2. 核心任务\n"
            f"3. 工作方法\n"
            f"4. 关键约束\n"
            f"5. 输出标准\n"
            f"6. 禁止事项\n\n"
            f"额外要求：\n"
            f"- 角色必须面向实际业务任务，不要默认把模型设成 Prompt Agent 或 Prompt Compiler\n"
            f"- 适合长期复用，而不是一次性对话\n"
            f"- 角色、方法、质量门槛、边界和失败回退都必须明确\n"
            f"- 除非用户明确要求，否则不要加入与最终业务结果无关的中间步骤或阶段性输出\n"
            f"- 最终结果必须可直接作为 system prompt 使用\n\n"
            f"输出要求：\n"
            f"- 直接输出最终 system prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n"
            f"- 如果需要举例说明格式，用普通文本描述，不要插入 Markdown fenced code block\n\n"
            f"{base_context}"
        )

    def _build_task_prompt_template(self, base_context: str, task_type: PromptTaskType) -> str:
        role = self._get_role_sentence(task_type)
        return (
            f"{role}\n\n"
            f"请直接输出一份可一次性发送给目标模型执行的最终任务 Prompt。\n\n"
            f"优先覆盖以下内容，可以自然组织，不必机械照抄标题：\n"
            f"1. 任务目标\n"
            f"2. 背景与输入信息\n"
            f"3. 具体执行要求\n"
            f"4. 输出格式\n"
            f"5. 质量标准\n\n"
            f"额外要求：\n"
            f"- 默认把这份产物视为用户下一步就要发送给目标模型的最终 Prompt，不要生成元 Prompt\n"
            f"- 如果需要角色设定，角色必须服务于实际业务任务，不要让模型自称 Prompt Agent、Prompt Compiler 或 BetterPrompt\n"
            f"- 尽量减少对额外澄清的依赖，必要时只保留关键缺口的条件分支\n"
            f"- 除非用户明确要求，不要增加“先分析、先总结、先输出计划、先解释方法”这类中间步骤\n"
            f"- 任务指令必须直接、清晰、可执行，并补足边界和回退规则\n\n"
            f"输出要求：\n"
            f"- 直接输出最终任务 Prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n"
            f"- 如果需要示例说明输出格式，用普通文本段落描述，不要插入 Markdown fenced code block\n\n"
            f"{base_context}"
        )

    def _build_analysis_workflow_template(self, base_context: str, task_type: PromptTaskType) -> str:
        role = self._get_role_sentence(task_type)
        return (
            f"{role}\n\n"
            f"请输出一份适合复杂分析任务的工作流式 Prompt。\n\n"
            f"优先覆盖以下内容，可以自然组织，不必机械照抄标题：\n"
            f"1. 分析目标\n"
            f"2. 阶段拆解\n"
            f"3. 每阶段关键问题\n"
            f"4. 判断节点与优先级\n"
            f"5. 验证方式\n"
            f"6. 最终交付标准\n\n"
            f"额外要求：\n"
            f"- 角色必须服务于实际业务任务，不要默认写成 Prompt Agent 或 Prompt Compiler\n"
            f"- 要体现先分析、再判断、再验证、再交付的顺序\n"
            f"- 适合复杂分析，不要写成普通问答指令\n"
            f"- 输出应是一份可直接复制使用的 workflow prompt\n\n"
            f"输出要求：\n"
            f"- 直接输出最终 workflow prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n"
            f"- 如果需要举例说明流程或格式，用普通文本描述，不要插入 Markdown fenced code block\n\n"
            f"{base_context}"
        )

    def _build_conversation_prompt_template(self, base_context: str, task_type: PromptTaskType) -> str:
        role = self._get_role_sentence(task_type)
        return (
            f"{role}\n\n"
            f"请输出一份适合多轮对话协作的 Prompt。\n\n"
            f"优先覆盖以下内容，可以自然组织，不必机械照抄标题：\n"
            f"1. 对话目标\n"
            f"2. 首轮先做什么\n"
            f"3. 澄清问题策略\n"
            f"4. 多轮推进规则\n"
            f"5. 信息不足时的处理方式\n"
            f"6. 最终收敛标准\n\n"
            f"额外要求：\n"
            f"- 角色必须服务于实际业务任务，不要默认写成 Prompt Agent 或 Prompt Compiler\n"
            f"- 要求模型先澄清再推进，而不是直接假设全部上下文成立\n"
            f"- 适合多轮协作，不要写成单次执行指令\n"
            f"- 输出应体现持续对话中的节奏与决策收敛方式\n\n"
            f"输出要求：\n"
            f"- 直接输出最终对话协作 Prompt\n"
            f"- 不要输出任何解释、标题前言或代码块\n"
            f"- 如果需要举例说明对话格式，用普通文本描述，不要插入 Markdown fenced code block\n\n"
            f"{base_context}"
        )
