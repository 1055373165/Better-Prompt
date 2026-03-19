from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlencode

import app.models  # noqa: F401
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.api.v1.prompt_sessions import router as prompt_sessions_router
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


@dataclass
class ASGIResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> dict[str, object]:
        return json.loads(self.body.decode('utf-8'))


class MinimalASGIClient:
    def __init__(self, app: FastAPI):
        self.app = app

    async def get(self, path: str, params: dict[str, str] | None = None) -> ASGIResponse:
        response_body: list[bytes] = []
        status_code = 500
        response_headers: dict[str, str] = {}
        request_sent = False

        async def receive() -> dict[str, object]:
            nonlocal request_sent
            if request_sent:
                return {'type': 'http.disconnect'}
            request_sent = True
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        async def send(message: dict[str, object]) -> None:
            nonlocal status_code, response_headers
            if message['type'] == 'http.response.start':
                status_code = int(message['status'])
                response_headers = {
                    key.decode('latin-1'): value.decode('latin-1')
                    for key, value in message.get('headers', [])
                }
            if message['type'] == 'http.response.body':
                response_body.append(message.get('body', b''))

        scope = {
            'type': 'http',
            'asgi': {'version': '3.0', 'spec_version': '2.3'},
            'http_version': '1.1',
            'method': 'GET',
            'scheme': 'http',
            'path': path,
            'raw_path': path.encode('ascii'),
            'query_string': urlencode(params or {}, doseq=True).encode('ascii'),
            'headers': [
                (b'host', b'testserver'),
                (b'accept', b'application/json'),
            ],
            'client': ('127.0.0.1', 12345),
            'server': ('testserver', 80),
            'root_path': '',
            'state': {},
        }

        await self.app(scope, receive, send)
        return ASGIResponse(status_code=status_code, headers=response_headers, body=b''.join(response_body))


class PromptSessionsApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        database_path = Path(self.tempdir.name) / 'prompt-sessions-api.db'
        database_url = f'sqlite+aiosqlite:///{database_path}'
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.app = FastAPI()
        self.app.include_router(prompt_sessions_router, prefix='/api/v1')

        async def override_get_db():
            async with self.session_factory() as session:
                yield session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = MinimalASGIClient(self.app)

    async def asyncTearDown(self) -> None:
        self.app.dependency_overrides.clear()
        await self.engine.dispose()
        self.tempdir.cleanup()

    async def test_list_endpoint_returns_provenance_fields_for_preset_workspace_and_agent_runs(self) -> None:
        seeded = await self._seed_prompt_sessions()

        response = await self.client.get('/api/v1/prompt-sessions')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        items_by_id = {item['id']: item for item in payload['items']}

        preset_item = items_by_id[seeded['preset_session_id']]
        workspace_item = items_by_id[seeded['workspace_session_id']]
        agent_item = items_by_id[seeded['agent_session_id']]

        self.assertEqual(preset_item['run_kind'], 'preset_run')
        self.assertEqual(preset_item['run_preset_name'], 'Signals Preset')
        self.assertEqual(preset_item['workflow_recipe_name'], 'Signals Recipe')
        self.assertEqual(preset_item['workflow_recipe_version_number'], 1)
        self.assertIsNone(preset_item['domain_workspace_id'])
        self.assertIsNone(preset_item['agent_monitor_id'])

        self.assertEqual(workspace_item['run_kind'], 'workspace_run')
        self.assertEqual(workspace_item['domain_workspace_id'], seeded['workspace_id'])
        self.assertEqual(workspace_item['subject_id'], seeded['subject_id'])
        self.assertIsNone(workspace_item['run_preset_name'])
        self.assertEqual(workspace_item['workflow_recipe_name'], 'Signals Recipe')
        self.assertEqual(workspace_item['workflow_recipe_version_number'], 1)

        self.assertEqual(agent_item['run_kind'], 'agent_run')
        self.assertEqual(agent_item['domain_workspace_id'], seeded['workspace_id'])
        self.assertEqual(agent_item['subject_id'], seeded['subject_id'])
        self.assertEqual(agent_item['agent_monitor_id'], seeded['monitor_id'])
        self.assertEqual(agent_item['trigger_kind'], 'manual')
        self.assertEqual(agent_item['run_preset_name'], 'Signals Preset')
        self.assertEqual(agent_item['workflow_recipe_name'], 'Signals Recipe')
        self.assertEqual(agent_item['workflow_recipe_version_number'], 1)

        filtered = await self.client.get(
            '/api/v1/prompt-sessions',
            params={
                'run_kind': 'agent_run',
                'domain_workspace_id': seeded['workspace_id'],
                'subject_id': seeded['subject_id'],
                'agent_monitor_id': seeded['monitor_id'],
                'trigger_kind': 'manual',
                'run_preset_id': seeded['run_preset_id'],
                'workflow_recipe_version_id': seeded['workflow_recipe_version_id'],
            },
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual([item['id'] for item in filtered.json()['items']], [seeded['agent_session_id']])

    async def test_detail_endpoint_returns_provenance_fields_for_each_main_run_kind(self) -> None:
        seeded = await self._seed_prompt_sessions()

        preset_response = await self.client.get(f"/api/v1/prompt-sessions/{seeded['preset_session_id']}")
        workspace_response = await self.client.get(f"/api/v1/prompt-sessions/{seeded['workspace_session_id']}")
        agent_response = await self.client.get(f"/api/v1/prompt-sessions/{seeded['agent_session_id']}")

        self.assertEqual(preset_response.status_code, 200)
        self.assertEqual(workspace_response.status_code, 200)
        self.assertEqual(agent_response.status_code, 200)

        preset_detail = preset_response.json()
        workspace_detail = workspace_response.json()
        agent_detail = agent_response.json()

        self.assertEqual(preset_detail['run_kind'], 'preset_run')
        self.assertEqual(preset_detail['run_preset_name'], 'Signals Preset')
        self.assertEqual(preset_detail['workflow_recipe_name'], 'Signals Recipe')
        self.assertEqual(preset_detail['workflow_recipe_version_number'], 1)
        self.assertEqual(preset_detail['metadata']['source'], 'preset')

        self.assertEqual(workspace_detail['run_kind'], 'workspace_run')
        self.assertEqual(workspace_detail['domain_workspace_id'], seeded['workspace_id'])
        self.assertEqual(workspace_detail['subject_id'], seeded['subject_id'])
        self.assertEqual(workspace_detail['workflow_recipe_name'], 'Signals Recipe')
        self.assertEqual(workspace_detail['workflow_recipe_version_number'], 1)
        self.assertEqual(workspace_detail['metadata']['source'], 'workspace')

        self.assertEqual(agent_detail['run_kind'], 'agent_run')
        self.assertEqual(agent_detail['run_preset_name'], 'Signals Preset')
        self.assertEqual(agent_detail['workflow_recipe_name'], 'Signals Recipe')
        self.assertEqual(agent_detail['workflow_recipe_version_number'], 1)
        self.assertEqual(agent_detail['agent_monitor_id'], seeded['monitor_id'])
        self.assertEqual(agent_detail['trigger_kind'], 'manual')
        self.assertEqual(agent_detail['metadata']['source'], 'agent_monitor')

    async def _seed_prompt_sessions(self) -> dict[str, str]:
        async with self.session_factory() as db:
            bundle = await self._create_scope_bundle(db)
            service = PromptSessionService(db)

            preset_session = await service.create_session(
                CreatePromptSessionRequest(
                    title='Preset Session',
                    entry_mode='debug',
                    run_kind='preset_run',
                    metadata={'source': 'preset'},
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
                session_id=preset_session.id,
                run_preset_id=bundle['run_preset_id'],
                workflow_recipe_version_id=bundle['workflow_recipe_version_id'],
                latest_iteration_id='iteration-preset',
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

        return {
            **bundle,
            'preset_session_id': preset_session.id,
            'workspace_session_id': workspace_session.id,
            'agent_session_id': agent_session.id,
        }

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
