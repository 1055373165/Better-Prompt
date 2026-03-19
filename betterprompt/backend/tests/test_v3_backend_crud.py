from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
import uuid

import app.models  # noqa: F401
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.prompt_iteration import PromptIteration
from app.schemas.domain_workspace import (
    CreateDomainWorkspaceRequest,
    CreateResearchReportRequest,
    CreateResearchReportVersionRequest,
    CreateResearchSourceRequest,
    CreateWorkspaceSubjectRequest,
)
from app.schemas.prompt_agent import DebugPromptRequest
from app.schemas.prompt_session import CreatePromptSessionRequest
from app.schemas.workflow_asset import (
    CreateContextPackRequest,
    CreateEvaluationProfileRequest,
    CreateRunPresetRequest,
    CreateWorkflowRecipeRequest,
)
from app.services.domain_workspace_service import (
    DomainWorkspaceService,
    DomainWorkspaceValidationError,
    ResearchReportService,
    ResearchSourceService,
    WorkspaceSubjectService,
)
from app.services.prompt_agent_service import PromptAgentService
from app.services.prompt_session_service import PromptSessionService
from app.services.workflow_asset_service import (
    ContextPackService,
    EvaluationProfileService,
    RunPresetService,
    WorkflowRecipeService,
)


class V3BackendCrudTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        database_path = Path(self.tempdir.name) / 'v3-crud.db'
        database_url = f'sqlite+aiosqlite:///{database_path}'
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.tempdir.cleanup()

    async def test_workspace_config_validation_and_counts(self) -> None:
        async with self.session_factory() as db:
            context_pack = await ContextPackService(db).create_context_pack(
                CreateContextPackRequest(name='Workspace Context', payload={'facts': ['alpha']})
            )
            evaluation_profile = await EvaluationProfileService(db).create_evaluation_profile(
                CreateEvaluationProfileRequest(name='Workspace Profile', rules={'rubric': ['depth']})
            )
            workflow_recipe = await WorkflowRecipeService(db).create_workflow_recipe(
                CreateWorkflowRecipeRequest(
                    name='Workspace Recipe',
                    definition={'steps': [{'mode': 'generate'}]},
                )
            )
            run_preset = await RunPresetService(db).create_run_preset(
                CreateRunPresetRequest(
                    name='Workspace Preset',
                    definition={'mode': 'generate', 'run_settings': {'user_input': 'hello'}},
                )
            )

            service = DomainWorkspaceService(db)
            workspace = await service.create_workspace(
                CreateDomainWorkspaceRequest(
                    workspace_type='stock_analysis',
                    name='Core Stocks',
                    description='Track the main names',
                    config={
                        'default_run_preset_id': run_preset.id,
                        'default_recipe_version_id': workflow_recipe.current_version.id,
                        'default_context_pack_ids': [context_pack.id],
                        'default_evaluation_profile_id': evaluation_profile.id,
                    },
                )
            )

            with self.assertRaises(DomainWorkspaceValidationError) as context:
                await service.create_workspace(
                    CreateDomainWorkspaceRequest(
                        workspace_type='stock_analysis',
                        name='Broken Workspace',
                        config={'default_run_preset_id': 'missing-preset'},
                    )
                )

        self.assertEqual(workspace.subject_count, 0)
        self.assertEqual(workspace.source_count, 0)
        self.assertEqual(workspace.report_count, 0)
        self.assertEqual(context.exception.code, 'DOMAIN_WORKSPACE_CONFIG_INVALID')

    async def test_subject_source_report_crud_and_versioning(self) -> None:
        async with self.session_factory() as db:
            workspace_service = DomainWorkspaceService(db)
            subject_service = WorkspaceSubjectService(db)
            source_service = ResearchSourceService(db)
            report_service = ResearchReportService(db)
            prompt_session_service = PromptSessionService(db)

            workspace = await workspace_service.create_workspace(
                CreateDomainWorkspaceRequest(
                    workspace_type='company_research',
                    name='Company Research',
                    config={},
                )
            )
            subject = await subject_service.create_subject(
                workspace.id,
                CreateWorkspaceSubjectRequest(
                    subject_type='company',
                    external_key='openai',
                    display_name='OpenAI',
                ),
            )
            source = await source_service.create_source(
                workspace.id,
                CreateResearchSourceRequest(
                    subject_id=subject.id,
                    source_type='url',
                    canonical_uri='https://example.com/openai-note',
                    title='OpenAI note',
                    content={'summary': 'Initial field notes'},
                ),
            )

            session = await prompt_session_service.create_session(
                CreatePromptSessionRequest(
                    title='Workspace report run',
                    entry_mode='generate',
                    run_kind='workspace_run',
                    domain_workspace_id=workspace.id,
                    subject_id=subject.id,
                    metadata={'created_by': 'test'},
                )
            )
            iteration = PromptIteration(
                id=str(uuid.uuid4()),
                session_id=session.id,
                mode='generate',
                status='completed',
                input_payload_json=json.dumps({'step': 'draft'}, ensure_ascii=False),
                output_payload_json=json.dumps({'result': 'first'}, ensure_ascii=False),
            )
            db.add(iteration)
            await db.commit()

            report = await report_service.create_report(
                workspace.id,
                CreateResearchReportRequest(
                    subject_id=subject.id,
                    report_type='company_brief',
                    title='OpenAI brief',
                    content={'thesis': 'Initial thesis'},
                    source_session_id=session.id,
                    source_iteration_id=iteration.id,
                    summary_text='First cut',
                    confidence_score=0.65,
                ),
            )
            updated = await report_service.create_version(
                report.id,
                CreateResearchReportVersionRequest(
                    content={'thesis': 'Refined thesis'},
                    summary_text='Second cut',
                    confidence_score=0.82,
                ),
            )
            listed = await report_service.list_reports(workspace.id, subject_id=subject.id)
            versions = await report_service.list_versions(report.id)
            refreshed_workspace = await workspace_service.get_workspace(workspace.id)

        self.assertEqual(source.subject_id, subject.id)
        self.assertEqual(updated.latest_version.version_number, 2)
        self.assertEqual([item.version_number for item in versions.items], [2, 1])
        self.assertEqual(len(listed.items), 1)
        self.assertEqual(listed.items[0].latest_version.version_number, 2)
        self.assertEqual(refreshed_workspace.subject_count, 1)
        self.assertEqual(refreshed_workspace.source_count, 1)
        self.assertEqual(refreshed_workspace.report_count, 1)

    async def test_prompt_agent_debug_runs_inside_workspace_are_recorded_as_workspace_run(self) -> None:
        async with self.session_factory() as db:
            workspace = await DomainWorkspaceService(db).create_workspace(
                CreateDomainWorkspaceRequest(
                    workspace_type='deep_research',
                    name='Deep Research',
                    config={},
                )
            )
            subject = await WorkspaceSubjectService(db).create_subject(
                workspace.id,
                CreateWorkspaceSubjectRequest(
                    subject_type='topic',
                    display_name='Agent UX',
                ),
            )

            response = await PromptAgentService(db).debug(
                DebugPromptRequest(
                    original_task='Diagnose why the prompt is brittle',
                    current_prompt='Please analyze and summarize.',
                    current_output='Looks good overall.',
                    domain_workspace_id=workspace.id,
                    subject_id=subject.id,
                )
            )
            session = await PromptSessionService(db).get_session(response.iteration.session_id)

        self.assertIsNotNone(session)
        self.assertEqual(session.run_kind, 'workspace_run')
        self.assertEqual(session.domain_workspace_id, workspace.id)
        self.assertEqual(session.subject_id, subject.id)
