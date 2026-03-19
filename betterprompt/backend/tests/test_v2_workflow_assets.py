from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import app.models  # noqa: F401
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.schemas.workflow_asset import (
    CreateContextPackRequest,
    CreateEvaluationProfileRequest,
    CreateRunPresetRequest,
    CreateWorkflowRecipeRequest,
    CreateWorkflowRecipeVersionRequest,
    RunPresetLaunchRequest,
)
from app.services.run_preset_launch_service import RunPresetLaunchService
from app.services.workflow_asset_service import (
    ContextPackService,
    EvaluationProfileService,
    RunPresetService,
    WorkflowAssetValidationError,
    WorkflowRecipeService,
)


class WorkflowAssetServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        database_path = Path(self.tempdir.name) / 'workflow-assets.db'
        database_url = f'sqlite+aiosqlite:///{database_path}'
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.tempdir.cleanup()

    async def test_workflow_recipe_rejects_invalid_step_modes(self) -> None:
        async with self.session_factory() as db:
            service = WorkflowRecipeService(db)

            with self.assertRaises(WorkflowAssetValidationError) as context:
                await service.create_workflow_recipe(
                    CreateWorkflowRecipeRequest(
                        name='Broken recipe',
                        definition={'steps': [{'mode': 'ship-it'}]},
                    )
                )

        self.assertEqual(context.exception.code, 'WORKFLOW_RECIPE_DEFINITION_INVALID')

    async def test_workflow_recipe_versions_increment_and_list_latest_first(self) -> None:
        async with self.session_factory() as db:
            service = WorkflowRecipeService(db)
            created = await service.create_workflow_recipe(
                CreateWorkflowRecipeRequest(
                    name='QA workflow recipe',
                    definition={'steps': [{'mode': 'generate'}]},
                )
            )

            updated = await service.create_version(
                created.id,
                CreateWorkflowRecipeVersionRequest(
                    definition={'steps': [{'mode': 'evaluate'}]},
                    change_summary='Switch to evaluation-first flow',
                ),
            )
            versions = await service.list_versions(created.id)

        self.assertIsNotNone(updated.current_version)
        self.assertEqual(updated.current_version.version_number, 2)
        self.assertEqual([item.version_number for item in versions.items], [2, 1])

    async def test_run_preset_validates_asset_references(self) -> None:
        async with self.session_factory() as db:
            bundle = await self._create_asset_bundle(db, recipe_mode='debug')
            service = RunPresetService(db)

            with self.assertRaises(WorkflowAssetValidationError) as context:
                await service.create_run_preset(
                    CreateRunPresetRequest(
                        name='Broken preset',
                        definition={
                            'mode': 'debug',
                            'context_pack_version_ids': ['missing-context-pack-version'],
                            'evaluation_profile_version_id': bundle['evaluation_profile_version_id'],
                            'workflow_recipe_version_id': bundle['workflow_recipe_version_id'],
                            'run_settings': {
                                'original_task': 'Diagnose a brittle prompt',
                                'current_prompt': 'Please improve this prompt',
                                'current_output': 'Looks okay.',
                            },
                        },
                    )
                )

            created = await service.create_run_preset(
                CreateRunPresetRequest(
                    name='Valid preset',
                    definition={
                        'mode': 'debug',
                        'context_pack_version_ids': [bundle['context_pack_version_id']],
                        'evaluation_profile_version_id': bundle['evaluation_profile_version_id'],
                        'workflow_recipe_version_id': bundle['workflow_recipe_version_id'],
                        'run_settings': {
                            'original_task': 'Diagnose a brittle prompt',
                            'current_prompt': 'Please improve this prompt',
                            'current_output': 'Looks okay.',
                        },
                    },
                )
            )

        self.assertEqual(context.exception.code, 'RUN_PRESET_REFERENCE_INVALID')
        self.assertEqual(created.definition['workflow_recipe_version_id'], bundle['workflow_recipe_version_id'])
        self.assertEqual(created.definition['context_pack_version_ids'], [bundle['context_pack_version_id']])

    async def test_run_preset_launch_prefers_definition_mode_and_preserves_workflow_refs(self) -> None:
        async with self.session_factory() as db:
            bundle = await self._create_asset_bundle(db, recipe_mode='evaluate')
            preset = await RunPresetService(db).create_run_preset(
                CreateRunPresetRequest(
                    name='Debug preset',
                    definition={
                        'mode': 'debug',
                        'context_pack_version_ids': [bundle['context_pack_version_id']],
                        'evaluation_profile_version_id': bundle['evaluation_profile_version_id'],
                        'workflow_recipe_version_id': bundle['workflow_recipe_version_id'],
                        'run_settings': {
                            'original_task': 'Find why the prompt is brittle',
                            'current_prompt': 'Do the task carefully.',
                            'current_output': 'A shallow answer.',
                        },
                    },
                )
            )

            mode, launch_request = await RunPresetLaunchService(db).build_launch_request(
                preset.id,
                RunPresetLaunchRequest(
                    domain_workspace_id='workspace-1',
                    subject_id='subject-1',
                ),
            )

        self.assertEqual(mode, 'debug')
        self.assertEqual(launch_request.original_task, 'Find why the prompt is brittle')
        self.assertEqual(launch_request.domain_workspace_id, 'workspace-1')
        self.assertEqual(launch_request.subject_id, 'subject-1')
        self.assertEqual(launch_request.workflow_recipe_version_id, bundle['workflow_recipe_version_id'])
        self.assertEqual(launch_request.evaluation_profile_version_id, bundle['evaluation_profile_version_id'])
        self.assertEqual(launch_request.context_pack_version_ids, [bundle['context_pack_version_id']])
        self.assertEqual(launch_request.run_preset_id, preset.id)

    async def test_run_preset_launch_can_infer_mode_from_recipe_and_mark_last_used(self) -> None:
        async with self.session_factory() as db:
            bundle = await self._create_asset_bundle(db, recipe_mode='evaluate')
            preset_service = RunPresetService(db)
            preset = await preset_service.create_run_preset(
                CreateRunPresetRequest(
                    name='Evaluate preset',
                    definition={
                        'workflow_recipe_version_id': bundle['workflow_recipe_version_id'],
                        'run_settings': {
                            'target_text': 'The answer is too generic.',
                            'target_type': 'output',
                        },
                    },
                )
            )
            launch_service = RunPresetLaunchService(db)

            mode, launch_request = await launch_service.build_launch_request(
                preset.id,
                RunPresetLaunchRequest(),
            )
            await launch_service.mark_used(preset.id)

            refreshed = await preset_service.get_run_preset(preset.id)

        self.assertEqual(mode, 'evaluate')
        self.assertEqual(launch_request.target_type, 'output')
        self.assertEqual(launch_request.target_text, 'The answer is too generic.')
        self.assertIsNotNone(refreshed)
        self.assertIsNotNone(refreshed.last_used_at)

    async def _create_asset_bundle(self, db, *, recipe_mode: str) -> dict[str, str]:
        context_pack = await ContextPackService(db).create_context_pack(
            CreateContextPackRequest(
                name='QA context pack',
                payload={'facts': ['Always keep acceptance criteria visible.']},
            )
        )
        evaluation_profile = await EvaluationProfileService(db).create_evaluation_profile(
            CreateEvaluationProfileRequest(
                name='QA evaluation profile',
                rules={'rubric': ['clarity', 'depth', 'execution']},
            )
        )
        workflow_recipe = await WorkflowRecipeService(db).create_workflow_recipe(
            CreateWorkflowRecipeRequest(
                name='QA workflow recipe',
                definition={'steps': [{'mode': recipe_mode}]},
            )
        )
        return {
            'context_pack_version_id': context_pack.current_version.id,
            'evaluation_profile_version_id': evaluation_profile.current_version.id,
            'workflow_recipe_version_id': workflow_recipe.current_version.id,
        }
