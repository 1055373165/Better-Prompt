import json
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.prompt_agent import (
    ContinuePromptRequest,
    ContinuePromptResponse,
    DebugPromptRequest,
    DebugPromptResponse,
    EvaluatePromptRequest,
    EvaluatePromptResponse,
    GeneratePromptRequest,
    GeneratePromptResponse,
)
from app.services.llm import (
    PromptLLMConfigurationError,
    get_default_llm_client,
    is_template_fallback_enabled,
)
from app.services.prompt_agent.continue_engine import PromptContinueEngine
from app.services.prompt_agent.debug_engine import PromptDebugEngine
from app.services.prompt_agent.diagnosis import PromptDiagnosisEngine
from app.services.prompt_agent.evaluate_engine import PromptEvaluateEngine
from app.services.prompt_agent.generate_engine import PromptGenerateEngine
from app.services.prompt_agent.memory_service import PromptMemoryService
from app.services.prompt_agent.module_router import PromptModuleRouter
from app.services.prompt_agent.optimization_layer import PromptOptimizationLayer
from app.services.prompt_agent.result_formatter import PromptResultFormatter
from app.services.prompt_agent.task_understanding import TaskUnderstandingEngine


class PromptAgentOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_understanding = TaskUnderstandingEngine()
        self.diagnosis_engine = PromptDiagnosisEngine()
        self.module_router = PromptModuleRouter()
        self.optimization_layer = PromptOptimizationLayer()
        self.generate_engine = PromptGenerateEngine()
        self.continue_engine = PromptContinueEngine()
        self.debug_engine = PromptDebugEngine()
        self.evaluate_engine = PromptEvaluateEngine()
        self.result_formatter = PromptResultFormatter()
        self.memory_service = PromptMemoryService()

    async def generate(self, request: GeneratePromptRequest) -> GeneratePromptResponse:
        diagnosis = self.task_understanding.understand(request)
        diagnosis = self.diagnosis_engine.enrich_generate_diagnosis(diagnosis)
        modules = self.module_router.route_for_generate(diagnosis)
        optimized_input = self.optimization_layer.optimize_generate_input(request, diagnosis)
        prompt_instruction = self.generate_engine.build_prompt(request, optimized_input, diagnosis, modules)
        generation_backend = 'template'
        generation_model: str | None = None

        try:
            llm_client = get_default_llm_client()
        except PromptLLMConfigurationError:
            if not is_template_fallback_enabled():
                raise
            final_prompt = prompt_instruction
        else:
            system_prompt, user_prompt = self.generate_engine.build_messages(request, optimized_input, diagnosis, modules)
            final_prompt = await llm_client.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
            generation_backend = 'llm'
            generation_model = llm_client.model_name

        return GeneratePromptResponse(
            diagnosis=diagnosis if request.show_diagnosis else None,
            final_prompt=final_prompt,
            artifact_type=request.artifact_type,
            applied_modules=modules,
            optimization_strategy=self.optimization_layer.strategy_name,
            optimized_input=optimized_input,
            prompt_only=request.prompt_only,
            diagnosis_visible=request.show_diagnosis,
            generation_backend=generation_backend,
            generation_model=generation_model,
        )

    async def generate_stream(self, request: GeneratePromptRequest) -> AsyncGenerator[str, None]:
        """Yield SSE events for streaming generate. Each event is a JSON line."""
        diagnosis = self.task_understanding.understand(request)
        diagnosis = self.diagnosis_engine.enrich_generate_diagnosis(diagnosis)
        modules = self.module_router.route_for_generate(diagnosis)
        optimized_input = self.optimization_layer.optimize_generate_input(request, diagnosis)

        # Send metadata event first
        meta = {
            'event': 'meta',
            'diagnosis': diagnosis.model_dump() if request.show_diagnosis else None,
            'artifact_type': request.artifact_type,
            'applied_modules': list(modules),
            'optimization_strategy': self.optimization_layer.strategy_name,
            'optimized_input': optimized_input,
            'prompt_only': request.prompt_only,
            'diagnosis_visible': request.show_diagnosis,
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

        try:
            llm_client = get_default_llm_client()
        except PromptLLMConfigurationError:
            if not is_template_fallback_enabled():
                error_event = {'event': 'error', 'detail': 'LLM not configured and template fallback disabled'}
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
                return
            # Template fallback: send full content at once
            prompt_instruction = self.generate_engine.build_prompt(request, optimized_input, diagnosis, modules)
            chunk_event = {'event': 'chunk', 'content': prompt_instruction}
            yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"
            done_event = {'event': 'done', 'generation_backend': 'template', 'generation_model': None}
            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"
            return

        # Stream from LLM
        system_prompt, user_prompt = self.generate_engine.build_messages(request, optimized_input, diagnosis, modules)
        async for chunk in llm_client.generate_text_stream(system_prompt=system_prompt, user_prompt=user_prompt):
            chunk_event = {'event': 'chunk', 'content': chunk}
            yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"

        done_event = {'event': 'done', 'generation_backend': 'llm', 'generation_model': llm_client.model_name}
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    async def debug(self, request: DebugPromptRequest) -> DebugPromptResponse:
        top_failure_mode, missing_layers, strengths, weaknesses = self.diagnosis_engine.diagnose_debug(
            request.current_prompt,
            request.current_output,
        )
        fix_map = {
            'problem_redefinition': '补充问题重定义层',
            'cognitive_drill_down': '补充认知下钻层',
            'key_point_priority': '增加关键点优先与判断强度',
            'criticality': '增加批判性分析与失效方式说明',
            'information_density': '压缩空话并提升信息密度',
            'boundary_validation': '补充前提、边界与验证条件',
            'executability': '补充可执行步骤与成功标准',
            'style_control': '补充自然表达与去模板化要求',
        }
        minimal_fix = [fix_map[layer] for layer in missing_layers] or ['增加质量门槛与文风约束']
        fixed_prompt = self.debug_engine.fix_prompt(request, minimal_fix)
        return DebugPromptResponse(
            strengths=strengths,
            weaknesses=weaknesses,
            top_failure_mode=top_failure_mode,
            missing_control_layers=missing_layers,
            minimal_fix=minimal_fix,
            fixed_prompt=fixed_prompt,
        )

    async def evaluate(self, request: EvaluatePromptRequest) -> EvaluatePromptResponse:
        breakdown, total, interpretation, top_issue, suggested_fix_layer = self.evaluate_engine.evaluate(request.target_text)
        return EvaluatePromptResponse(
            score_breakdown=breakdown,
            total_score=total,
            total_interpretation=interpretation,
            top_issue=top_issue,
            suggested_fix_layer=suggested_fix_layer,
        )

    async def continue_optimization(self, request: ContinuePromptRequest) -> ContinuePromptResponse:
        refined_result = self.continue_engine.refine(request)
        if request.mode == 'generate':
            actions = self.result_formatter.continue_actions_for_generate()
        elif request.mode == 'debug':
            actions = self.result_formatter.continue_actions_for_debug()
        else:
            actions = self.result_formatter.continue_actions_for_evaluate()
        return ContinuePromptResponse(
            source_mode=request.mode,
            optimization_goal=request.optimization_goal,
            refined_result=refined_result,
            suggested_next_actions=actions,
        )
