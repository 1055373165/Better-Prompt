from app.schemas.prompt_agent import PromptControlModule, PromptDiagnosis


class PromptModuleRouter:
    def route_for_generate(self, diagnosis: PromptDiagnosis) -> list[PromptControlModule]:
        base: list[PromptControlModule] = [
            'problem_redefinition',
            'cognitive_drill_down',
            'style_control',
        ]
        if diagnosis.quality_target == 'depth':
            base.append('key_point_priority')
        elif diagnosis.quality_target == 'execution':
            base.extend(['boundary_validation', 'executability'])
        elif diagnosis.quality_target == 'natural':
            base.append('information_density')
        else:
            base.extend(['information_density', 'boundary_validation'])
        return list(dict.fromkeys(base))
