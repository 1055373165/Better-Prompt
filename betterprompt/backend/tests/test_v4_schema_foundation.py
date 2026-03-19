from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import uuid

import app.models  # noqa: F401
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.agent_monitor import AgentMonitor
from app.models.domain_workspace import DomainWorkspace
from app.models.workspace_subject import WorkspaceSubject
from app.schemas.prompt_session import CreatePromptSessionRequest
from app.services.prompt_session_service import PromptSessionService


class V4SchemaFoundationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        database_path = Path(self.tempdir.name) / 'v4-schema.db'
        database_url = f'sqlite+aiosqlite:///{database_path}'
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.tempdir.cleanup()

    async def test_metadata_contains_v4_tables_and_prompt_session_columns(self) -> None:
        async with self.engine.begin() as conn:
            table_names = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
            session_columns = await conn.run_sync(
                lambda sync_conn: {
                    column['name']
                    for column in inspect(sync_conn).get_columns('prompt_sessions')
                }
            )

        self.assertTrue(
            {
                'watchlists',
                'watchlist_items',
                'agent_monitors',
                'agent_runs',
                'agent_alerts',
                'freshness_records',
            }.issubset(table_names)
        )
        self.assertTrue({'agent_monitor_id', 'trigger_kind'}.issubset(session_columns))

    async def test_prompt_session_service_round_trips_agent_provenance(self) -> None:
        workspace_id = str(uuid.uuid4())
        subject_id = str(uuid.uuid4())
        monitor_id = str(uuid.uuid4())

        async with self.session_factory() as db:
            db.add(
                DomainWorkspace(
                    id=workspace_id,
                    workspace_type='stock_analysis',
                    name='V4 Workspace',
                    config_json='{}',
                )
            )
            db.add(
                WorkspaceSubject(
                    id=subject_id,
                    workspace_id=workspace_id,
                    subject_type='ticker',
                    external_key='MSFT',
                    display_name='Microsoft',
                    metadata_json='{}',
                )
            )
            db.add(
                AgentMonitor(
                    id=monitor_id,
                    workspace_id=workspace_id,
                    subject_id=subject_id,
                    monitor_type='schedule',
                    trigger_config_json='{"cadence":"daily"}',
                    alert_policy_json='{"only_material_change":true}',
                )
            )
            await db.commit()

            service = PromptSessionService(db)
            created = await service.create_session(
                CreatePromptSessionRequest(
                    title='Agent rerun',
                    entry_mode='debug',
                    run_kind='agent_run',
                    domain_workspace_id=workspace_id,
                    subject_id=subject_id,
                    agent_monitor_id=monitor_id,
                    trigger_kind='schedule',
                    metadata={'created_by': 'test'},
                )
            )
            listed = await service.list_sessions(
                run_kind='agent_run',
                domain_workspace_id=workspace_id,
                subject_id=subject_id,
                agent_monitor_id=monitor_id,
                trigger_kind='schedule',
            )

        self.assertEqual(created.run_kind, 'agent_run')
        self.assertEqual(created.agent_monitor_id, monitor_id)
        self.assertEqual(created.trigger_kind, 'schedule')
        self.assertEqual([item.id for item in listed.items], [created.id])
