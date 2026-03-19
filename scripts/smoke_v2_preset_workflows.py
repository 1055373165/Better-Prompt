from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.prompt_iteration import PromptIteration
from app.models.prompt_session import PromptSession
from app.schemas.workflow_asset import (
    CreateContextPackRequest,
    CreateEvaluationProfileRequest,
    CreateRunPresetRequest,
    CreateWorkflowRecipeRequest,
    RunPresetLaunchRequest,
)
from app.services.prompt_agent_service import PromptAgentService
from app.services.prompt_session_service import PromptSessionService
from app.services.run_preset_launch_service import RunPresetLaunchService
from app.services.workflow_asset_service import (
    ContextPackService,
    EvaluationProfileService,
    RunPresetService,
    WorkflowRecipeService,
)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def main() -> None:
    temp_dir = tempfile.TemporaryDirectory(prefix='betterprompt-v2-smoke-')
    db_path = Path(temp_dir.name) / 'smoke.db'
    database_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(database_url, future=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with session_factory() as db:
            context_pack_service = ContextPackService(db)
            evaluation_profile_service = EvaluationProfileService(db)
            workflow_recipe_service = WorkflowRecipeService(db)
            run_preset_service = RunPresetService(db)
            launch_service = RunPresetLaunchService(db)
            prompt_agent_service = PromptAgentService(db)
            prompt_session_service = PromptSessionService(db)

            context_pack = await context_pack_service.create_context_pack(
                CreateContextPackRequest(
                    name='Smoke Context Pack',
                    description='Context for smoke validation',
                    payload={
                        'brief': 'Code review focus',
                        'constraints': ['be specific', 'include risks'],
                    },
                    tags=['smoke', 'review'],
                    change_summary='initial context pack',
                )
            )
            evaluation_profile = await evaluation_profile_service.create_evaluation_profile(
                CreateEvaluationProfileRequest(
                    name='Smoke Evaluation Profile',
                    description='Profile for smoke validation',
                    rules={
                        'weights': {'executability': 5, 'stability': 5},
                        'notes': 'Prefer concrete recommendations',
                    },
                    change_summary='initial evaluation profile',
                )
            )
            workflow_recipe = await workflow_recipe_service.create_workflow_recipe(
                CreateWorkflowRecipeRequest(
                    name='Smoke Workflow Recipe',
                    description='Recipe for smoke validation',
                    domain_hint='code-review',
                    definition={
                        'steps': [
                            {'mode': 'debug', 'label': 'repair failing review prompt'},
                        ],
                    },
                    change_summary='initial workflow recipe',
                )
            )

            debug_preset = await run_preset_service.create_run_preset(
                CreateRunPresetRequest(
                    name='Smoke Debug Preset',
                    description='Matches save-as-run-preset debug shape',
                    definition={
                        'mode': 'debug',
                        'context_pack_version_ids': [context_pack.current_version.id],
                        'evaluation_profile_version_id': evaluation_profile.current_version.id,
                        'workflow_recipe_version_id': workflow_recipe.current_version.id,
                        'run_settings': {
                            'original_task': 'Review this API design prompt',
                            'current_prompt': 'Please review the design and tell me if it looks good.',
                            'current_output': 'Looks good overall.',
                            'output_preference': 'balanced',
                        },
                    },
                )
            )

            debug_mode, debug_payload = await launch_service.build_launch_request(
                debug_preset.id,
                RunPresetLaunchRequest(),
            )
            ensure(debug_mode == 'debug', 'definition.mode should become the default launch mode')
            ensure(debug_payload.run_preset_id == debug_preset.id, 'debug payload should carry run_preset_id')
            ensure(
                debug_payload.workflow_recipe_version_id == workflow_recipe.current_version.id,
                'debug payload should carry workflow recipe ref',
            )

            debug_response = await prompt_agent_service.debug(debug_payload)
            await launch_service.mark_used(debug_preset.id)
            ensure(debug_response.iteration.session_id is not None, 'debug response should persist session_id')
            ensure(debug_response.iteration.iteration_id is not None, 'debug response should persist iteration_id')

            debug_session = await db.get(PromptSession, debug_response.iteration.session_id)
            ensure(debug_session is not None, 'debug session row should exist')
            ensure(debug_session.run_kind == 'preset_run', 'debug session should be recorded as preset_run')
            ensure(debug_session.run_preset_id == debug_preset.id, 'debug session should record run_preset_id')
            ensure(
                debug_session.workflow_recipe_version_id == workflow_recipe.current_version.id,
                'debug session should record workflow_recipe_version_id',
            )

            debug_iteration = await db.get(PromptIteration, debug_response.iteration.iteration_id)
            ensure(debug_iteration is not None, 'debug iteration row should exist')
            debug_input_payload = json.loads(debug_iteration.input_payload_json)
            ensure(
                debug_input_payload['request']['run_preset_id'] == debug_preset.id,
                'iteration request payload should carry run_preset_id',
            )
            ensure(
                debug_input_payload['resolved_refs']['workflow_recipe_version_id'] == workflow_recipe.current_version.id,
                'iteration resolved refs should carry workflow recipe ref',
            )
            ensure(
                debug_input_payload['preset_definition']['mode'] == 'debug',
                'iteration preset definition should preserve saved default mode',
            )

            evaluate_preset = await run_preset_service.create_run_preset(
                CreateRunPresetRequest(
                    name='Smoke Evaluate Preset',
                    description='Matches save-as-run-preset evaluate shape',
                    definition={
                        'mode': 'evaluate',
                        'context_pack_version_ids': [context_pack.current_version.id],
                        'evaluation_profile_version_id': evaluation_profile.current_version.id,
                        'run_settings': {
                            'target_text': 'Please analyze this business model with concrete risks.',
                            'target_type': 'prompt',
                        },
                    },
                )
            )

            evaluate_mode, evaluate_payload = await launch_service.build_launch_request(
                evaluate_preset.id,
                RunPresetLaunchRequest(),
            )
            ensure(evaluate_mode == 'evaluate', 'evaluate preset should launch in evaluate mode')
            evaluate_response = await prompt_agent_service.evaluate(evaluate_payload)
            ensure(evaluate_response.iteration.session_id is not None, 'evaluate response should persist session_id')

            sessions = await prompt_session_service.list_sessions(
                run_kind='preset_run',
                run_preset_id=debug_preset.id,
                workflow_recipe_version_id=workflow_recipe.current_version.id,
            )
            debug_summary = next(
                (item for item in sessions.items if item.id == debug_response.iteration.session_id),
                None,
            )
            ensure(debug_summary is not None, 'prompt_session_service filters should return the debug preset session')
            ensure(debug_summary.run_preset_name == debug_preset.name, 'session summary should expose run_preset_name')
            ensure(
                debug_summary.workflow_recipe_name == workflow_recipe.name,
                'session summary should expose workflow_recipe_name',
            )
            ensure(
                debug_summary.workflow_recipe_version_number == workflow_recipe.current_version.version_number,
                'session summary should expose workflow_recipe_version_number',
            )

            debug_detail = await prompt_session_service.get_session(debug_response.iteration.session_id)
            ensure(debug_detail is not None, 'prompt_session_service detail should exist')
            ensure(debug_detail.run_preset_name == debug_preset.name, 'session detail should expose run_preset_name')

            generate_preset = await run_preset_service.create_run_preset(
                CreateRunPresetRequest(
                    name='Smoke Generate Preset',
                    description='Matches save-as-run-preset generate shape',
                    definition={
                        'mode': 'generate',
                        'context_pack_version_ids': [context_pack.current_version.id],
                        'evaluation_profile_version_id': evaluation_profile.current_version.id,
                        'run_settings': {
                            'user_input': 'Write a rigorous prompt for reviewing API tradeoffs.',
                            'show_diagnosis': True,
                            'output_preference': 'balanced',
                            'artifact_type': 'task_prompt',
                            'prompt_only': False,
                        },
                    },
                )
            )

            generate_mode, generate_payload = await launch_service.build_launch_request(
                generate_preset.id,
                RunPresetLaunchRequest(),
            )
            ensure(generate_mode == 'generate', 'generate preset should launch in generate mode')
            ensure(
                generate_payload.user_input == 'Write a rigorous prompt for reviewing API tradeoffs.',
                'generate preset should preserve saved user_input',
            )

            print('v2 preset workflow smoke passed')
            print(f'debug_session={debug_response.iteration.session_id}')
            print(f'evaluate_session={evaluate_response.iteration.session_id}')
            print(f'temp_db={db_path}')
    finally:
        await engine.dispose()
        temp_dir.cleanup()


if __name__ == '__main__':
    os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
    asyncio.run(main())
