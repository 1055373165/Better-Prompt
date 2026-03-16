from app.schemas.prompt_agent import GeneratePromptRequest, PromptArtifactType, PromptDiagnosis, PromptTaskType


PROMPT_BRIEF_HEADER = """下面是一份等待优化的原始 Prompt 或任务描述。\n\n你的目标是识别其中真正的元需求，并将它重写为更高质量、可直接使用的最终 Prompt。\n\n请优先补足真正影响执行结果的关键约束、边界条件、质量标准和输出格式，而不是改写用户真正想完成的业务目标。"""

ARTIFACT_TARGET_LABELS: dict[PromptArtifactType, str] = {
    'task_prompt': '重写后的最终任务 Prompt，可直接发送给目标模型',
    'system_prompt': '可长期复用的系统提示词',
    'analysis_workflow': '适合复杂任务拆解的分析工作流 Prompt',
    'conversation_prompt': '适合多轮协作的对话 Prompt',
}

TASK_BRIEF_HINTS: dict[PromptTaskType, list[str]] = {
    'document_translation': [
        '把文档翻译、本地化和版面保真视为同一个任务，不要退化成泛泛的“帮我翻译”。',
        '明确标题、正文、列表、表格、图注、脚注、公式、页眉页脚与页码的处理策略。',
        '把术语、专有名词、缩写和章节编号一致性写成硬约束，必要时要求先建立术语表。',
        '如果用户强调中英对照或映射一致性，要求按段落、块或编号保持对齐。',
        '遇到 OCR 噪声、结构歧义、缺页或版面冲突时，要求模型显式标注并采用保守回退策略。',
    ],
}


class PromptOptimizationLayer:
    strategy_name = 'direct_execution_prompt_v2'

    def _build_task_focus_text(self, task_type: PromptTaskType) -> str:
        hints = TASK_BRIEF_HINTS.get(task_type, [])
        if not hints:
            return ''
        return '\n'.join(f'- {hint}' for hint in hints)

    def optimize_generate_input(self, request: GeneratePromptRequest, diagnosis: PromptDiagnosis) -> str:
        output_target = ARTIFACT_TARGET_LABELS.get(request.artifact_type, '最终 Prompt')
        task_focus_text = self._build_task_focus_text(diagnosis.task_type)
        lines = [
            PROMPT_BRIEF_HEADER,
            '',
            f'目标产物：{output_target}',
            f'推断任务类型：{diagnosis.task_type}',
            f'质量偏好：{diagnosis.quality_target}',
            '补充原则：',
            '- 默认交付最终 Prompt，不要产出元 Prompt。',
            '- 把用户输入视为待优化的原始 Prompt 或原始任务描述，目标是重写得更强，而不是偏离用户真正要完成的任务。',
            '- 角色设定必须服务于真实业务任务，不要把执行模型写成 Prompt Agent 或 Prompt Compiler，除非用户明确要求。',
            '- 优先补足输入约束、成功标准、输出格式、失效边界和回退规则。',
            '- 除非用户明确要求，不要额外增加“先分析摘要、先解释思路、先输出计划、先自我介绍”等中间步骤。',
            '- 正文保持自然、清晰、信息密度高，避免模板腔和空泛表述。',
            '- 最终产物不要包裹在 Markdown 代码块中，也不要为了举例再插入 fenced code block。',
        ]

        if task_focus_text:
            lines.extend(['', '任务专用提醒：', task_focus_text])

        lines.extend(['', '用户原始描述：', request.user_input])

        if request.context_notes:
            lines.extend(['', '补充上下文：', request.context_notes])

        return '\n'.join(lines)
