from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
import uuid

import app.models  # noqa: F401
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.agent_alert import AgentAlert
from app.models.freshness_record import FreshnessRecord
from app.schemas.agent_runtime import (
    CreateAgentMonitorRequest,
    CreateWatchlistItemRequest,
    CreateWatchlistRequest,
    UpdateAgentAlertRequest,
)
from app.schemas.domain_workspace import (
    CreateDomainWorkspaceRequest,
    CreateResearchSourceRequest,
    CreateWorkspaceSubjectRequest,
)
from app.schemas.workflow_asset import CreateRunPresetRequest, CreateWorkflowRecipeRequest
from app.services.agent_runtime_service import (
    AgentAlertService,
    AgentMonitorService,
    AgentRuntimeValidationError,
    FreshnessRecordService,
    WatchlistService,
)
from app.services.domain_workspace_service import (
    DomainWorkspaceService,
    ResearchSourceService,
    WorkspaceSubjectService,
)
from app.services.prompt_session_service import PromptSessionService
from app.services.workflow_asset_service import RunPresetService, WorkflowRecipeService


class V4BackendContractsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        database_path = Path(self.tempdir.name) / 'v4-contracts.db'
        database_url = f'sqlite+aiosqlite:///{database_path}'
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.tempdir.cleanup()

    async def test_runtime_resources_round_trip_and_link_prompt_sessions(self) -> None:
        async with self.session_factory() as db:
            workspace = await DomainWorkspaceService(db).create_workspace(
                CreateDomainWorkspaceRequest(
                    workspace_type='stock_analysis',
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
            source = await ResearchSourceService(db).create_source(
                workspace.id,
                CreateResearchSourceRequest(
                    subject_id=subject.id,
                    source_type='url',
                    canonical_uri='https://example.com/nvda-update',
                    title='NVIDIA update',
                    content={'summary': 'Revenue inflection'},
                ),
            )
            run_preset = await RunPresetService(db).create_run_preset(
                CreateRunPresetRequest(
                    name='Monitor Debug Preset',
                    definition={
                        'mode': 'debug',
                        'run_settings': {
                            'original_task': 'Review the latest company update',
                            'current_prompt': 'Please summarize the company update.',
                            'current_output': 'Looks good overall.',
                        },
                    },
                )
            )
            workflow_recipe = await WorkflowRecipeService(db).create_workflow_recipe(
                CreateWorkflowRecipeRequest(
                    name='Daily Monitor Recipe',
                    definition={'steps': [{'mode': 'generate'}]},
                )
            )

            watchlists = WatchlistService(db)
            monitors = AgentMonitorService(db)
            alerts = AgentAlertService(db)
            freshness = FreshnessRecordService(db)
            prompt_sessions = PromptSessionService(db)

            watchlist = await watchlists.create_watchlist(
                CreateWatchlistRequest(
                    workspace_id=workspace.id,
                    name='Core AI Names',
                    description='Track primary AI holdings',
                )
            )
            item = await watchlists.create_item(
                watchlist.id,
                CreateWatchlistItemRequest(subject_id=subject.id, sort_order=10),
            )
            listed_watchlists = await watchlists.list_watchlists(workspace_id=workspace.id)
            listed_items = await watchlists.list_items(watchlist.id)

            monitor = await monitors.create_monitor(
                CreateAgentMonitorRequest(
                    workspace_id=workspace.id,
                    watchlist_id=watchlist.id,
                    subject_id=subject.id,
                    run_preset_id=run_preset.id,
                    workflow_recipe_version_id=workflow_recipe.current_version.id,
                    monitor_type='schedule',
                    trigger_config={'cadence': 'daily'},
                    alert_policy={'only_material_change': True},
                )
            )
            first_run = await monitors.trigger_monitor(monitor.id)
            second_run = await monitors.trigger_monitor(monitor.id)
            listed_monitors = await monitors.list_monitors(workspace_id=workspace.id, status='active')
            listed_runs = await monitors.list_runs(monitor.id)
            run_detail = await monitors.get_run(second_run.id)
            session = await prompt_sessions.get_session(first_run.prompt_session_id)

            db.add(
                AgentAlert(
                    id=str(uuid.uuid4()),
                    workspace_id=workspace.id,
                    subject_id=subject.id,
                    run_id=second_run.id,
                    severity='high',
                    status='unread',
                    title='Material change detected',
                    summary_text='The latest filing changes the thesis',
                    payload_json=json.dumps({'change': 'filing'}, ensure_ascii=False),
                )
            )
            db.add(
                FreshnessRecord(
                    id=str(uuid.uuid4()),
                    workspace_id=workspace.id,
                    subject_id=subject.id,
                    source_id=source.id,
                    status='stale',
                    observed_at=datetime.now(UTC).replace(tzinfo=None),
                    last_checked_at=datetime.now(UTC).replace(tzinfo=None),
                    data_timestamp=datetime.now(UTC).replace(tzinfo=None),
                    details_json=json.dumps({'lag_hours': 48}, ensure_ascii=False),
                )
            )
            await db.commit()

            alert_list = await alerts.list_alerts(workspace_id=workspace.id, status='unread')
            updated_alert = await alerts.update_alert(
                alert_list.items[0].id,
                UpdateAgentAlertRequest(status='read'),
            )
            alert_detail = await alerts.get_alert(updated_alert.id)
            freshness_list = await freshness.list_records(
                workspace_id=workspace.id,
                subject_id=subject.id,
                source_id=source.id,
                status='stale',
            )
            freshness_detail = await freshness.get_record(freshness_list.items[0].id)

        self.assertEqual([item.id for item in listed_watchlists.items], [watchlist.id])
        self.assertEqual([item.id for item in listed_items.items], [item.id])
        self.assertEqual(monitor.run_preset_id, run_preset.id)
        self.assertEqual(monitor.workflow_recipe_version_id, workflow_recipe.current_version.id)
        self.assertEqual(first_run.run_status, 'completed')
        self.assertIsNotNone(first_run.prompt_session_id)
        self.assertIsNotNone(first_run.prompt_iteration_id)
        self.assertEqual(second_run.previous_run_id, first_run.id)
        self.assertEqual([item.id for item in listed_monitors.items], [monitor.id])
        self.assertEqual([item.id for item in listed_runs.items], [second_run.id, first_run.id])
        self.assertEqual(run_detail.id, second_run.id)
        self.assertEqual(session.run_kind, 'agent_run')
        self.assertEqual(session.agent_monitor_id, monitor.id)
        self.assertEqual(session.trigger_kind, 'manual')
        self.assertEqual(session.run_preset_id, run_preset.id)
        self.assertEqual(session.workflow_recipe_version_id, workflow_recipe.current_version.id)
        self.assertEqual(updated_alert.status, 'read')
        self.assertIsNotNone(updated_alert.read_at)
        self.assertEqual(alert_detail.id, updated_alert.id)
        self.assertEqual([item.status for item in freshness_list.items], ['stale'])
        self.assertEqual(freshness_detail.details['lag_hours'], 48)

    async def test_cross_workspace_scope_is_rejected(self) -> None:
        async with self.session_factory() as db:
            workspace_service = DomainWorkspaceService(db)
            subject_service = WorkspaceSubjectService(db)
            watchlists = WatchlistService(db)
            monitors = AgentMonitorService(db)

            first_workspace = await workspace_service.create_workspace(
                CreateDomainWorkspaceRequest(
                    workspace_type='company_research',
                    name='First Workspace',
                    config={},
                )
            )
            second_workspace = await workspace_service.create_workspace(
                CreateDomainWorkspaceRequest(
                    workspace_type='company_research',
                    name='Second Workspace',
                    config={},
                )
            )
            first_watchlist = await watchlists.create_watchlist(
                CreateWatchlistRequest(
                    workspace_id=first_workspace.id,
                    name='Workspace One Watchlist',
                )
            )
            foreign_subject = await subject_service.create_subject(
                second_workspace.id,
                CreateWorkspaceSubjectRequest(
                    subject_type='company',
                    external_key='openai',
                    display_name='OpenAI',
                ),
            )

            with self.assertRaises(AgentRuntimeValidationError) as watchlist_error:
                await watchlists.create_item(
                    first_watchlist.id,
                    CreateWatchlistItemRequest(subject_id=foreign_subject.id),
                )

            with self.assertRaises(AgentRuntimeValidationError) as monitor_error:
                await monitors.create_monitor(
                    CreateAgentMonitorRequest(
                        workspace_id=first_workspace.id,
                        subject_id=foreign_subject.id,
                        monitor_type='schedule',
                        trigger_config={'cadence': 'daily'},
                        alert_policy={},
                    )
                )

        self.assertEqual(watchlist_error.exception.code, 'WATCHLIST_ITEM_INVALID')
        self.assertEqual(monitor_error.exception.code, 'AGENT_MONITOR_INVALID')

    async def test_trigger_without_run_preset_is_recorded_as_failed_run(self) -> None:
        async with self.session_factory() as db:
            workspace = await DomainWorkspaceService(db).create_workspace(
                CreateDomainWorkspaceRequest(
                    workspace_type='deep_research',
                    name='Trigger Failure Workspace',
                    config={},
                )
            )
            subject = await WorkspaceSubjectService(db).create_subject(
                workspace.id,
                CreateWorkspaceSubjectRequest(
                    subject_type='topic',
                    display_name='Runtime failure case',
                ),
            )
            monitor = await AgentMonitorService(db).create_monitor(
                CreateAgentMonitorRequest(
                    workspace_id=workspace.id,
                    subject_id=subject.id,
                    monitor_type='schedule',
                    trigger_config={'cadence': 'daily'},
                    alert_policy={},
                )
            )

            failed_run = await AgentMonitorService(db).trigger_monitor(monitor.id)

        self.assertEqual(failed_run.run_status, 'failed')
        self.assertIsNone(failed_run.prompt_iteration_id)
        self.assertEqual(failed_run.change_summary['error_code'], 'AGENT_MONITOR_TRIGGER_INVALID')
