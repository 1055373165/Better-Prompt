from app.schemas.prompt_agent import PromptControlModule, PromptDiagnosis, PromptFailureMode, PromptTaskType

# Per-task-type most likely failure modes (ordered by risk)
TASK_FAILURE_MAP: dict[PromptTaskType, list[PromptFailureMode]] = {
    'algorithm_analysis': ['surface_restatement', 'pseudo_depth'],
    'source_code_analysis': ['surface_restatement', 'uncritical_praise'],
    'architecture_spec': ['not_executable', 'correct_but_empty'],
    'business_insight': ['correct_but_empty', 'no_priority_judgment'],
    'product_design': ['not_executable', 'no_priority_judgment'],
    'data_analysis': ['surface_restatement', 'not_executable'],
    'education_learning': ['template_tone', 'surface_restatement'],
    'creative_marketing': ['template_tone', 'style_instability'],
    'writing_generation': ['template_tone', 'style_instability'],
    'document_translation': ['not_executable', 'correct_but_empty', 'style_instability'],
    'general_deep_analysis': ['surface_restatement', 'template_tone', 'correct_but_empty'],
}

# Extra failure modes appended per quality_target
QUALITY_FAILURE_EXTRA: dict[str, list[PromptFailureMode]] = {
    'depth': ['pseudo_depth'],
    'execution': ['not_executable'],
    'natural': ['style_instability'],
}


class PromptDiagnosisEngine:
    def enrich_generate_diagnosis(self, diagnosis: PromptDiagnosis) -> PromptDiagnosis:
        # Start from task-type predicted failures
        failure_modes: list[PromptFailureMode] = list(
            TASK_FAILURE_MAP.get(diagnosis.task_type, TASK_FAILURE_MAP['general_deep_analysis'])
        )

        # Append quality-target extras (deduplicated)
        for fm in QUALITY_FAILURE_EXTRA.get(diagnosis.quality_target, []):
            if fm not in failure_modes:
                failure_modes.append(fm)

        diagnosis.failure_modes = failure_modes
        return diagnosis

    def diagnose_debug(self, current_prompt: str, current_output: str) -> tuple[PromptFailureMode, list[PromptControlModule], list[str], list[str]]:
        prompt_text = current_prompt.lower()
        output_text = current_output.lower()

        strengths: list[str] = []
        weaknesses: list[str] = []
        missing_layers: list[PromptControlModule] = []

        if any(keyword in prompt_text for keyword in ['角色', '你是', 'role']):
            strengths.append('Prompt 已包含角色定位')
        else:
            weaknesses.append('角色定位不明确，模型容易输出泛化内容')

        if any(keyword in prompt_text for keyword in ['步骤', 'step', '输出格式', '格式', '结构']):
            strengths.append('Prompt 已包含一定结构约束')
        else:
            weaknesses.append('缺少明确结构约束，输出稳定性不足')
            missing_layers.append('executability')

        if any(keyword in prompt_text for keyword in ['边界', '前提', '限制', '约束', '失效']):
            strengths.append('Prompt 已部分覆盖边界或约束意识')
        else:
            weaknesses.append('缺少前提、边界或失效条件说明')
            missing_layers.append('boundary_validation')

        if len(current_output.strip()) < 120:
            weaknesses.append('输出过短，可能停留在表层复述')

        if any(keyword in output_text for keyword in ['总结来说', '总之', '首先', '其次', '最后']) and len(current_output.strip()) < 240:
            weaknesses.append('输出存在模板化表达倾向，信息密度偏低')

        if not any(keyword in prompt_text for keyword in ['本质', '真正', '重定义', '先判断']):
            missing_layers.append('problem_redefinition')

        if not any(keyword in prompt_text for keyword in ['为什么', '代价', '机制', '关键点', '根因']):
            missing_layers.append('cognitive_drill_down')

        missing_layers = list(dict.fromkeys(missing_layers))

        if 'problem_redefinition' in missing_layers:
            top_failure_mode: PromptFailureMode = 'surface_restatement'
        elif 'cognitive_drill_down' in missing_layers:
            top_failure_mode = 'pseudo_depth'
        elif 'boundary_validation' in missing_layers or 'executability' in missing_layers:
            top_failure_mode = 'not_executable'
        else:
            top_failure_mode = 'template_tone'

        if not strengths:
            strengths.append('当前 Prompt 至少已经明确了基础任务目标')

        if not weaknesses:
            weaknesses.append('当前 Prompt 仍可进一步增强质量门槛与风格稳定性')

        return top_failure_mode, missing_layers, strengths, weaknesses
