from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import app.models  # noqa: F401
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.prompt_session import PromptSession
from app.schemas.agent_runtime import CreateAgentMonitorRequest
from app.schemas.domain_workspace import CreateDomainWorkspaceRequest, CreateWorkspaceSubjectRequest
from app.schemas.prompt_session import CreatePromptSessionRequest
from app.schemas.workflow_asset import CreateRunPresetRequest, CreateWorkflowRecipeRequest
from app.services.agent_runtime_service import AgentMonitorService
from app.services.domain_workspace_service import DomainWorkspaceService, WorkspaceSubjectService
from app.services.prompt_session_service import PromptSessionService
from app.services.workflow_asset_service import RunPresetService, WorkflowRecipeService


class PromptSessionProvenanceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        database_path = Path(self.tempdir.name) / 'prompt-session-provenance.db'
        database_url = f'sqlite+aiosqlite:///{database_path}'
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.tempdir.cleanup()

    async def test_list_and_detail_enrich_v2_v3_v4_provenance_fields(self) -> None:
        async with self.session_factory() as db:
            bundle = await self._create_scope_bundle(db)
            service = PromptSessionService(db)

            manual_session = await service.create_session(
                CreatePromptSessionRequest(
                    title='Manual Preset Session',
                    entry_mode='debug',
                    run_kind='manual_workbench',
                    metadata={'source': 'workbench'},
                )
            )
            workspace_session = await service.create_session(
                CreatePromptSessionRequest(
                    title='Workspace Session',
                    entry_mode='generate',
                    run_kind='workspace_run',
                    domain_workspace_id=bundle['workspace_id'],
                    subject_id=bundle['subject_id'],
                    metadata={'source': 'workspace'},
                )
            )
            agent_session = await service.create_session(
                CreatePromptSessionRequest(
                    title='Agent Session',
                    entry_mode='debug',
                    run_kind='agent_run',
                    domain_workspace_id=bundle['workspace_id'],
                    subject_id=bundle['subject_id'],
                    agent_monitor_id=bundle['monitor_id'],
                    trigger_kind='manual',
                    metadata={'source': 'agent_monitor'},
                )
            )

            await self._attach_session_refs(
                db,
                session_id=manual_session.id,
                run_preset_id=bundle['run_preset_id'],
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
                latest_iteration_id='iteration-manual',
            )
            await self._attach_session_refs(
                db,
                session_id=workspace_session.id,
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
                latest_iteration_id='iteration-workspace',
            )
            await self._attach_session_refs(
                db,
                session_id=agent_session.id,
                run_preset_id=bundle['run_preset_id'],
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
                latest_iteration_id='iteration-agent',
            )

            sessions = await service.list_sessions()
            workspace_detail = await service.get_session(workspace_session.id)
            agent_detail = await service.get_session(agent_session.id)

        sessions_by_id = {item.id: item for item in sessions.items}
        manual_summary = sessions_by_id[manual_session.id]
        workspace_summary = sessions_by_id[workspace_session.id]
        agent_summary = sessions_by_id[agent_session.id]

        self.assertEqual(manual_summary.run_kind, 'manual_workbench')
        self.assertEqual(manual_summary.run_preset_name, 'Signals Preset')
        self.assertEqual(manual_summary.workflow_recipe_name, 'Signals Recipe')
        self.assertEqual(manual_summary.workflow_recipe_version_number, 1)
        self.assertEqual(manual_summary.latest_iteration_id, 'iteration-manual')

        self.assertEqual(workspace_summary.run_kind, 'workspace_run')
        self.assertEqual(workspace_summary.domain_workspace_id, bundle['workspace_id'])
        self.assertEqual(workspace_summary.subject_id, bundle['subject_id'])
        self.assertIsNone(workspace_summary.run_preset_name)
        self.assertEqual(workspace_summary.workflow_recipe_name, 'Signals Recipe')
        self.assertEqual(workspace_summary.latest_iteration_id, 'iteration-workspace')

        self.assertEqual(agent_summary.run_kind, 'agent_run')
        self.assertEqual(agent_summary.domain_workspace_id, bundle['workspace_id'])
        self.assertEqual(agent_summary.subject_id, bundle['subject_id'])
        self.assertEqual(agent_summary.agent_monitor_id, bundle['monitor_id'])
        self.assertEqual(agent_summary.trigger_kind, 'manual')
        self.assertEqual(agent_summary.run_preset_name, 'Signals Preset')
        self.assertEqual(agent_summary.workflow_recipe_name, 'Signals Recipe')
        self.assertEqual(agent_summary.workflow_recipe_version_number, 1)
        self.assertEqual(agent_summary.latest_iteration_id, 'iteration-agent')

        self.assertIsNotNone(workspace_detail)
        self.assertEqual(workspace_detail.workflow_recipe_name, 'Signals Recipe')
        self.assertEqual(workspace_detail.metadata['source'], 'workspace')

        self.assertIsNotNone(agent_detail)
        self.assertEqual(agent_detail.run_preset_name, 'Signals Preset')
        self.assertEqual(agent_detail.workflow_recipe_name, 'Signals Recipe')
        self.assertEqual(agent_detail.agent_monitor_id, bundle['monitor_id'])
        self.assertEqual(agent_detail.trigger_kind, 'manual')
        self.assertEqual(agent_detail.metadata['source'], 'agent_monitor')

    async def test_list_sessions_supports_cross_cutting_provenance_filters(self) -> None:
        async with self.session_factory() as db:
            bundle = await self._create_scope_bundle(db)
            service = PromptSessionService(db)

            manual_session = await service.create_session(
                CreatePromptSessionRequest(
                    title='Manual Preset Session',
                    entry_mode='debug',
                    run_kind='manual_workbench',
                )
            )
            workspace_session = await service.create_session(
                CreatePromptSessionRequest(
                    title='Workspace Session',
                    entry_mode='generate',
                    run_kind='workspace_run',
                    domain_workspace_id=bundle['workspace_id'],
                    subject_id=bundle['subject_id'],
                )
            )
            agent_session = await service.create_session(
                CreatePromptSessionRequest(
                    title='Agent Session',
                    entry_mode='debug',
                    run_kind='agent_run',
                    domain_workspace_id=bundle['workspace_id'],
                    subject_id=bundle['subject_id'],
                    agent_monitor_id=bundle['monitor_id'],
                    trigger_kind='manual',
                )
            )

            await self._attach_session_refs(
                db,
                session_id=manual_session.id,
                run_preset_id=bundle['run_preset_id'],
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
            )
            await self._attach_session_refs(
                db,
                session_id=workspace_session.id,
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
            )
            await self._attach_session_refs(
                db,
                session_id=agent_session.id,
                run_preset_id=bundle['run_preset_id'],
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
            )

            agent_filtered = await service.list_sessions(
                run_kind='agent_run',
                domain_workspace_id=bundle['workspace_id'],
                subject_id=bundle['subject_id'],
                agent_monitor_id=bundle['monitor_id'],
                trigger_kind='manual',
                run_preset_id=bundle['run_preset_id'],
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
            )
            preset_filtered = await service.list_sessions(run_preset_id=bundle['run_preset_id'])
            workspace_filtered = await service.list_sessions(
                domain_workspace_id=bundle['workspace_id'],
                subject_id=bundle['subject_id'],
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
            )

        self.assertEqual([item.id for item in agent_filtered.items], [agent_session.id])
        self.assertEqual({item.id for item in preset_filtered.items}, {manual_session.id, agent_session.id})
        self.assertEqual({item.id for item in workspace_filtered.items}, {workspace_session.id, agent_session.id})

    async def _create_scope_bundle(self, db) -> dict[str, str]:
        workflow_recipe = await WorkflowRecipeService(db).create_workflow_recipe(
            CreateWorkflowRecipeRequest(
                name='Signals Recipe',
                definition={'steps': [{'mode': 'debug'}]},
            )
        )
        run_preset = await RunPresetService(db).create_run_preset(
            CreateRunPresetRequest(
                name='Signals Preset',
                definition={
                    'mode': 'debug',
                    'workflow_recipe_version_id': workflow_recipe.current_version.id,
                    'run_settings': {
                        'original_task': 'Review the signal',
                        'current_prompt': 'Please review the signal.',
                        'current_output': 'Looks acceptable.',
                    },
                },
            )
        )
        workspace = await DomainWorkspaceService(db).create_workspace(
            CreateDomainWorkspaceRequest(
                workspace_type='signal_research',
                name='Signals Workspace',
                config={},
            )
        )
        subject = await WorkspaceSubjectService(db).create_subject(
            workspace.id,
            CreateWorkspaceSubjectRequest(
                subject_type='ticker',
                external_key='NVDA',
                display_name='NVIDIA',
            ),
        )
        monitor = await AgentMonitorService(db).create_monitor(
            CreateAgentMonitorRequest(
                workspace_id=workspace.id,
                subject_id=subject.id,
                run_preset_id=run_preset.id,
                workflow_recipe_version_id=workflow_recipe.current_version.id,
                monitor_type='schedule',
                trigger_config={'cadence': 'daily'},
                alert_policy={'only_material_change': True},
            )
        )
        return {
            'workspace_id': workspace.id,
            'subject_id': subject.id,
            'monitor_id': monitor.id,
            'run_preset_id': run_preset.id,
            'workflow_recipe_version_id': workflow_recipe.current_version.id,
        }

    async def _attach_session_refs(
        self,
        db,
        *,
        session_id: str,
        run_preset_id: str | None = None,
        workflow_recipe_version_id: str | None = None,
        latest_iteration_id: str | None = None,
    ) -> None:
        session = await db.get(PromptSession, session_id)
        self.assertIsNotNone(session)
        session.run_preset_id = run_preset_id
        session.workflow_recipe_version_id = workflow_recipe_version_id
        session.latest_iteration_id = latest_iteration_id
        await db.commit()

