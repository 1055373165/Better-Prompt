import json
from collections.abc import AsyncGenerator
from typing import Any

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
    PromptIterationRef,
)
from app.services.llm import (
    PromptLLMConfigurationError,
    get_default_llm_client,
    is_template_fallback_enabled,
)
from app.services.prompt_agent.continue_engine import PromptContinueEngine
from app.services.prompt_agent.debug_engine import PromptDebugEngine
from app.services.prompt_agent.diagnosis import PromptDiagnosisEngine
from app.services.prompt_agent.errors import PromptAgentRequestError
from app.services.prompt_agent.evaluate_engine import PromptEvaluateEngine
from app.services.prompt_agent.generate_engine import PromptGenerateEngine
from app.services.prompt_agent.memory_service import PromptMemoryService
from app.services.prompt_agent.module_router import PromptModuleRouter
from app.services.prompt_agent.optimization_layer import PromptOptimizationLayer
from app.services.prompt_agent.persistence import PromptAgentPersistenceService
from app.services.prompt_agent.result_formatter import PromptResultFormatter
from app.services.prompt_agent.task_understanding import TaskUnderstandingEngine
from app.services.prompt_agent.workflow_context import PromptWorkflowContextService, ResolvedWorkflowContext


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
        self.workflow_context = PromptWorkflowContextService(db)
        self.persistence = PromptAgentPersistenceService(db)

    async def generate(self, request: GeneratePromptRequest) -> GeneratePromptResponse:
        request, resolved_context = await self.workflow_context.resolve_request(request)
        request = request.model_copy(
            update={'context_notes': resolved_context.build_generate_context_notes(request.context_notes)}
        )
        diagnosis = self.task_understanding.understand(request)
        diagnosis = self.diagnosis_engine.enrich_generate_diagnosis(diagnosis)
        modules = self.module_router.route_for_generate(diagnosis)
        optimized_input = self.optimization_layer.optimize_generate_input(request, diagnosis)
        generation_backend = 'template'
        generation_model: str | None = None

        try:
            llm_client = get_default_llm_client()
        except PromptLLMConfigurationError:
            if not is_template_fallback_enabled():
                raise
            prompt_instruction = self.generate_engine.build_prompt(request, optimized_input, diagnosis, modules)
            final_prompt = prompt_instruction
        else:
            system_prompt, user_prompt = self.generate_engine.build_messages(request, optimized_input, diagnosis, modules)
            final_prompt = await llm_client.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
            generation_backend = 'llm'
            generation_model = llm_client.model_name

        response = GeneratePromptResponse(
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
        response.iteration = await self._persist_response(
            mode='generate',
            session_entry_mode='generate',
            request=request,
            response=response,
            resolved_context=resolved_context,
            provider=generation_backend,
            model=generation_model,
        )
        return response

    async def generate_stream(self, request: GeneratePromptRequest) -> AsyncGenerator[str, None]:
        """Yield SSE events for streaming generate. Each event is a JSON line."""
        try:
            request, resolved_context = await self.workflow_context.resolve_request(request)
        except PromptAgentRequestError as exc:
            error_event = {'event': 'error', 'detail': exc.message, 'code': exc.code}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            return

        request = request.model_copy(
            update={'context_notes': resolved_context.build_generate_context_notes(request.context_notes)}
        )
        diagnosis = self.task_understanding.understand(request)
        diagnosis = self.diagnosis_engine.enrich_generate_diagnosis(diagnosis)
        modules = self.module_router.route_for_generate(diagnosis)
        optimized_input = self.optimization_layer.optimize_generate_input(request, diagnosis)
        accumulated = ''
        generation_backend = 'template'
        generation_model: str | None = None

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
            accumulated = prompt_instruction
            chunk_event = {'event': 'chunk', 'content': accumulated}
            yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"
            done_event = await self._build_generate_done_event(
                request=request,
                resolved_context=resolved_context,
                diagnosis=diagnosis if request.show_diagnosis else None,
                final_prompt=accumulated,
                modules=modules,
                optimized_input=optimized_input,
                generation_backend='template',
                generation_model=None,
            )
            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"
            return

        # Stream from LLM
        system_prompt, user_prompt = self.generate_engine.build_messages(request, optimized_input, diagnosis, modules)
        async for chunk in llm_client.generate_text_stream(system_prompt=system_prompt, user_prompt=user_prompt):
            accumulated += chunk
            chunk_event = {'event': 'chunk', 'content': chunk}
            yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"

        generation_backend = 'llm'
        generation_model = llm_client.model_name
        done_event = await self._build_generate_done_event(
            request=request,
            resolved_context=resolved_context,
            diagnosis=diagnosis if request.show_diagnosis else None,
            final_prompt=accumulated,
            modules=modules,
            optimized_input=optimized_input,
            generation_backend=generation_backend,
            generation_model=generation_model,
        )
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    async def debug(self, request: DebugPromptRequest) -> DebugPromptResponse:
        request, resolved_context = await self.workflow_context.resolve_request(request)
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
        fixed_prompt = self.debug_engine.fix_prompt(
            request,
            minimal_fix,
            workflow_guidance=resolved_context.build_debug_guidance(),
        )
        response = DebugPromptResponse(
            strengths=strengths,
            weaknesses=weaknesses,
            top_failure_mode=top_failure_mode,
            missing_control_layers=missing_layers,
            minimal_fix=minimal_fix,
            fixed_prompt=fixed_prompt,
        )
        response.iteration = await self._persist_response(
            mode='debug',
            session_entry_mode='debug',
            request=request,
            response=response,
            resolved_context=resolved_context,
            provider='rule_based_debug',
            model=None,
        )
        return response

    async def evaluate(self, request: EvaluatePromptRequest) -> EvaluatePromptResponse:
        request, resolved_context = await self.workflow_context.resolve_request(request)
        breakdown, total, interpretation, top_issue, suggested_fix_layer = self.evaluate_engine.evaluate(
            request.target_text,
            target_type=request.target_type,
            profile_rules=resolved_context.evaluation_rules(),
            recipe_definition=resolved_context.recipe_definition(),
        )
        response = EvaluatePromptResponse(
            score_breakdown=breakdown,
            total_score=total,
            total_interpretation=interpretation,
            top_issue=top_issue,
            suggested_fix_layer=suggested_fix_layer,
        )
        response.iteration = await self._persist_response(
            mode='evaluate',
            session_entry_mode='evaluate',
            request=request,
            response=response,
            resolved_context=resolved_context,
            provider='rule_based_evaluate',
            model=None,
        )
        return response

    async def continue_optimization(self, request: ContinuePromptRequest) -> ContinuePromptResponse:
        request, resolved_context = await self.workflow_context.resolve_request(request)
        request = request.model_copy(
            update={'context_notes': resolved_context.build_continue_context_notes(request.context_notes)}
        )
        llm_client = get_default_llm_client()
        system_prompt, user_prompt = self.continue_engine.build_messages(request)
        refined_result = await llm_client.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
        generation_backend = 'llm'
        generation_model = llm_client.model_name

        if request.mode == 'generate':
            actions = self.result_formatter.continue_actions_for_generate()
        elif request.mode == 'debug':
            actions = self.result_formatter.continue_actions_for_debug()
        else:
            actions = self.result_formatter.continue_actions_for_evaluate()
        response = ContinuePromptResponse(
            source_mode=request.mode,
            optimization_goal=request.optimization_goal,
            refined_result=refined_result,
            suggested_next_actions=actions,
            generation_backend=generation_backend,
            generation_model=generation_model,
        )
        response.iteration = await self._persist_response(
            mode='continue',
            session_entry_mode=request.mode,
            request=request,
            response=response,
            resolved_context=resolved_context,
            provider='llm',
            model=generation_model,
            parent_iteration_id=request.parent_iteration_id,
        )
        return response

    async def continue_optimization_stream(self, request: ContinuePromptRequest) -> AsyncGenerator[str, None]:
        try:
            request, resolved_context = await self.workflow_context.resolve_request(request)
        except PromptAgentRequestError as exc:
            error_event = {'event': 'error', 'detail': exc.message, 'code': exc.code}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            return

        request = request.model_copy(
            update={'context_notes': resolved_context.build_continue_context_notes(request.context_notes)}
        )
        if request.mode == 'generate':
            actions = self.result_formatter.continue_actions_for_generate()
        elif request.mode == 'debug':
            actions = self.result_formatter.continue_actions_for_debug()
        else:
            actions = self.result_formatter.continue_actions_for_evaluate()

        meta = {
            'event': 'meta',
            'source_mode': request.mode,
            'optimization_goal': request.optimization_goal,
            'result_label': '优化后版本',
            'suggested_next_actions': actions,
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"
        accumulated = ''

        try:
            llm_client = get_default_llm_client()
        except PromptLLMConfigurationError as exc:
            error_event = {'event': 'error', 'detail': str(exc)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            return

        system_prompt, user_prompt = self.continue_engine.build_messages(request)

        try:
            async for chunk in llm_client.generate_text_stream(system_prompt=system_prompt, user_prompt=user_prompt):
                accumulated += chunk
                chunk_event = {'event': 'chunk', 'content': chunk}
                yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"
        except Exception as exc:  # noqa: BLE001 - surface upstream errors as SSE payloads
            error_event = {'event': 'error', 'detail': str(exc)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            return

        done_event = await self._build_continue_done_event(
            request=request,
            resolved_context=resolved_context,
            refined_result=accumulated,
            actions=actions,
            generation_model=llm_client.model_name,
        )
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    async def _persist_response(
        self,
        *,
        mode: str,
        session_entry_mode: str,
        request,
        response,
        resolved_context: ResolvedWorkflowContext,
        provider: str | None,
        model: str | None,
        parent_iteration_id: str | None = None,
    ) -> PromptIterationRef:
        return await self.persistence.persist_response(
            mode=mode,
            session_entry_mode=session_entry_mode,
            session_id=request.session_id,
            domain_workspace_id=request.domain_workspace_id,
            subject_id=request.subject_id,
            agent_monitor_id=getattr(request, 'agent_monitor_id', None),
            trigger_kind=getattr(request, 'trigger_kind', None),
            request_payload=self._build_request_payload(request, resolved_context),
            output_payload=response.model_dump(),
            title_hint=self._build_title_hint(mode, request, resolved_context),
            run_kind=self._run_kind(request),
            run_preset_id=request.run_preset_id,
            workflow_recipe_version_id=request.workflow_recipe_version_id,
            parent_iteration_id=parent_iteration_id,
            provider=provider,
            model=model,
        )

    async def _build_generate_done_event(
        self,
        *,
        request: GeneratePromptRequest,
        resolved_context: ResolvedWorkflowContext,
        diagnosis,
        final_prompt: str,
        modules: list[str],
        optimized_input: str,
        generation_backend: str,
        generation_model: str | None,
    ) -> dict[str, Any]:
        response = GeneratePromptResponse(
            diagnosis=diagnosis,
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
        iteration_ref = await self._persist_response(
            mode='generate',
            session_entry_mode='generate',
            request=request,
            response=response,
            resolved_context=resolved_context,
            provider=generation_backend,
            model=generation_model,
        )
        return {
            'event': 'done',
            'generation_backend': generation_backend,
            'generation_model': generation_model,
            'session_id': iteration_ref.session_id,
            'iteration_id': iteration_ref.iteration_id,
        }

    async def _build_continue_done_event(
        self,
        *,
        request: ContinuePromptRequest,
        resolved_context: ResolvedWorkflowContext,
        refined_result: str,
        actions: list[str],
        generation_model: str | None,
    ) -> dict[str, Any]:
        response = ContinuePromptResponse(
            source_mode=request.mode,
            optimization_goal=request.optimization_goal,
            refined_result=refined_result,
            suggested_next_actions=actions,
            generation_backend='llm',
            generation_model=generation_model,
        )
        iteration_ref = await self._persist_response(
            mode='continue',
            session_entry_mode=request.mode,
            request=request,
            response=response,
            resolved_context=resolved_context,
            provider='llm',
            model=generation_model,
            parent_iteration_id=request.parent_iteration_id,
        )
        return {
            'event': 'done',
            'generation_backend': 'llm',
            'generation_model': generation_model,
            'session_id': iteration_ref.session_id,
            'iteration_id': iteration_ref.iteration_id,
        }

    def _build_request_payload(self, request, resolved_context: ResolvedWorkflowContext) -> dict[str, Any]:
        return {
            'request': request.model_dump(),
            'resolved_refs': resolved_context.ref_payload(),
            'preset_definition': resolved_context.preset_definition if resolved_context.run_preset else {},
            'workflow_recipe_definition': resolved_context.recipe_definition(),
            'evaluation_rules': resolved_context.evaluation_rules(),
        }

    def _build_title_hint(self, mode: str, request, resolved_context: ResolvedWorkflowContext) -> str:
        if resolved_context.run_preset is not None:
            return resolved_context.run_preset.name[:255]

        candidates = {
            'generate': getattr(request, 'user_input', ''),
            'debug': getattr(request, 'original_task', ''),
            'evaluate': getattr(request, 'target_text', ''),
            'continue': getattr(request, 'optimization_goal', ''),
        }
        raw_title = ' '.join(str(candidates.get(mode, '')).split()).strip()
        if not raw_title:
            raw_title = f'{mode.title()} run'
        return raw_title[:255]

    def _run_kind(self, request) -> str:
        if getattr(request, 'agent_monitor_id', None):
            return 'agent_run'
        if getattr(request, 'domain_workspace_id', None):
            return 'workspace_run'
        return 'preset_run' if request.run_preset_id else 'manual_workbench'
