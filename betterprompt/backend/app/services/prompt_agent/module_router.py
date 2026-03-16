from app.schemas.prompt_agent import PromptControlModule, PromptDiagnosis, PromptTaskType

# Base module set per task type (order matters for prompt assembly)
TASK_MODULE_MAP: dict[PromptTaskType, list[PromptControlModule]] = {
    'algorithm_analysis': ['problem_redefinition', 'cognitive_drill_down', 'key_point_priority', 'boundary_validation', 'style_control'],
    'source_code_analysis': ['problem_redefinition', 'cognitive_drill_down', 'criticality', 'key_point_priority', 'style_control'],
    'architecture_spec': ['problem_redefinition', 'criticality', 'boundary_validation', 'executability', 'style_control'],
    'business_insight': ['problem_redefinition', 'cognitive_drill_down', 'key_point_priority', 'criticality', 'style_control'],
    'product_design': ['problem_redefinition', 'criticality', 'executability', 'boundary_validation', 'style_control'],
    'data_analysis': ['problem_redefinition', 'key_point_priority', 'boundary_validation', 'executability', 'style_control'],
    'education_learning': ['problem_redefinition', 'cognitive_drill_down', 'style_control'],
    'creative_marketing': ['style_control', 'information_density', 'key_point_priority'],
    'writing_generation': ['style_control', 'information_density'],
    'document_translation': ['problem_redefinition', 'key_point_priority', 'boundary_validation', 'executability', 'style_control'],
    'general_deep_analysis': ['problem_redefinition', 'cognitive_drill_down', 'key_point_priority', 'boundary_validation', 'style_control'],
}

# Modules to ADD per quality_target
QUALITY_ADD: dict[str, list[PromptControlModule]] = {
    'depth': ['cognitive_drill_down', 'key_point_priority', 'criticality'],
    'execution': ['executability', 'boundary_validation'],
    'natural': ['information_density', 'style_control'],
    'balanced': ['information_density'],
}

# Modules triggered by specific failure modes
FAILURE_FIX_MAP: dict[str, list[PromptControlModule]] = {
    'surface_restatement': ['problem_redefinition', 'cognitive_drill_down'],
    'template_tone': ['style_control', 'information_density'],
    'correct_but_empty': ['key_point_priority', 'criticality'],
    'pseudo_depth': ['cognitive_drill_down', 'criticality'],
    'uncritical_praise': ['criticality', 'boundary_validation'],
    'no_priority_judgment': ['key_point_priority'],
    'not_executable': ['executability', 'boundary_validation'],
    'style_instability': ['style_control'],
}


class PromptModuleRouter:
    def route_for_generate(self, diagnosis: PromptDiagnosis) -> list[PromptControlModule]:
        # 1. Start with task-type base modules
        modules: list[PromptControlModule] = list(TASK_MODULE_MAP.get(diagnosis.task_type, TASK_MODULE_MAP['general_deep_analysis']))

        # 2. Add quality-target modules
        for mod in QUALITY_ADD.get(diagnosis.quality_target, []):
            if mod not in modules:
                modules.append(mod)

        # 3. Add failure-mode fix modules
        for fm in diagnosis.failure_modes:
            for mod in FAILURE_FIX_MAP.get(fm, []):
                if mod not in modules:
                    modules.append(mod)

        return modules
