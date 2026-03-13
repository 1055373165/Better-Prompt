from app.schemas.prompt_agent import GeneratePromptRequest, PromptDiagnosis


class TaskUnderstandingEngine:
    def understand(self, request: GeneratePromptRequest) -> PromptDiagnosis:
        text = request.user_input.lower()
        output_type = request.artifact_type

        if any(keyword in text for keyword in ['代码', '源码', '函数', 'module', 'code']):
            task_type = 'source_code_analysis'
        elif any(keyword in text for keyword in ['架构', '系统设计', '接口', '技术方案']):
            task_type = 'architecture_spec'
        elif any(keyword in text for keyword in ['商业', '行业', '增长', '公司']):
            task_type = 'business_insight'
        elif any(keyword in text for keyword in ['写作', '改写', '润色', '文章']):
            task_type = 'writing_generation'
        elif any(keyword in text for keyword in ['算法', '题解', 'leetcode']):
            task_type = 'algorithm_analysis'
        else:
            task_type = 'general_deep_analysis'

        return PromptDiagnosis(
            task_type=task_type,
            output_type=output_type,
            quality_target=request.output_preference,
            failure_modes=[],
        )
