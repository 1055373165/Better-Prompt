from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import uuid

import app.models  # noqa: F401
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.domain_workspace import DomainWorkspace
from app.models.workspace_subject import WorkspaceSubject
from app.schemas.prompt_session import CreatePromptSessionRequest
from app.services.prompt_session_service import PromptSessionService


class V3SchemaFoundationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        database_path = Path(self.tempdir.name) / 'v3-schema.db'
        database_url = f'sqlite+aiosqlite:///{database_path}'
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.tempdir.cleanup()

    async def test_metadata_contains_v3_tables_and_prompt_session_columns(self) -> None:
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
                'domain_workspaces',
                'workspace_subjects',
                'research_sources',
                'research_reports',
                'research_report_versions',
            }.issubset(table_names)
        )
        self.assertTrue({'domain_workspace_id', 'subject_id'}.issubset(session_columns))

    async def test_prompt_session_service_round_trips_workspace_provenance(self) -> None:
        workspace_id = str(uuid.uuid4())
        subject_id = str(uuid.uuid4())

        async with self.session_factory() as db:
            db.add(
                DomainWorkspace(
                    id=workspace_id,
                    workspace_type='stock_analysis',
                    name='Stocks Workspace',
                    config_json='{}',
                )
            )
            db.add(
                WorkspaceSubject(
                    id=subject_id,
                    workspace_id=workspace_id,
                    subject_type='ticker',
                    external_key='AAPL',
                    display_name='Apple',
                    metadata_json='{}',
                )
            )
            await db.commit()

            service = PromptSessionService(db)
            created = await service.create_session(
                CreatePromptSessionRequest(
                    title='Workspace run',
                    entry_mode='generate',
                    run_kind='workspace_run',
                    domain_workspace_id=workspace_id,
                    subject_id=subject_id,
                    metadata={'created_by': 'test'},
                )
            )
            listed = await service.list_sessions(
                run_kind='workspace_run',
                domain_workspace_id=workspace_id,
                subject_id=subject_id,
            )

        self.assertEqual(created.run_kind, 'workspace_run')
        self.assertEqual(created.domain_workspace_id, workspace_id)
        self.assertEqual(created.subject_id, subject_id)
        self.assertEqual([item.id for item in listed.items], [created.id])
