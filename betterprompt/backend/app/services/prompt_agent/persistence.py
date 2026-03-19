from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_iteration import PromptIteration
from app.models.prompt_session import PromptSession
from app.schemas.prompt_agent import PromptIterationRef
from app.services.prompt_agent.errors import PromptAgentRequestError


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


class PromptAgentPersistenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def persist_response(
        self,
        *,
        mode: str,
        session_entry_mode: str,
        session_id: str | None,
        domain_workspace_id: str | None,
        subject_id: str | None,
        agent_monitor_id: str | None,
        trigger_kind: str | None,
        request_payload: dict[str, Any],
        output_payload: dict[str, Any],
        title_hint: str,
        run_kind: str,
        run_preset_id: str | None,
        workflow_recipe_version_id: str | None,
        parent_iteration_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> PromptIterationRef:
        session = await self._get_or_create_session(
            session_id=session_id,
            title_hint=title_hint,
            entry_mode=session_entry_mode,
            run_kind=run_kind,
            domain_workspace_id=domain_workspace_id,
            subject_id=subject_id,
            agent_monitor_id=agent_monitor_id,
            trigger_kind=trigger_kind,
            run_preset_id=run_preset_id,
            workflow_recipe_version_id=workflow_recipe_version_id,
        )
        iteration = PromptIteration(
            id=str(uuid.uuid4()),
            session_id=session.id,
            parent_iteration_id=parent_iteration_id,
            mode=mode,
            status='completed',
            input_payload_json=_json_dumps(request_payload),
            output_payload_json=_json_dumps(output_payload),
            provider=provider,
            model=model,
        )
        self.db.add(iteration)
        session.latest_iteration_id = iteration.id
        session.run_kind = run_kind
        if domain_workspace_id is not None:
            session.domain_workspace_id = domain_workspace_id
        if subject_id is not None:
            session.subject_id = subject_id
        if agent_monitor_id is not None:
            session.agent_monitor_id = agent_monitor_id
        if trigger_kind is not None:
            session.trigger_kind = trigger_kind
        if run_preset_id is not None:
            session.run_preset_id = run_preset_id
        if workflow_recipe_version_id is not None:
            session.workflow_recipe_version_id = workflow_recipe_version_id
        await self.db.commit()
        await self.db.refresh(iteration)
        await self.db.refresh(session)
        return PromptIterationRef(session_id=session.id, iteration_id=iteration.id)

    async def _get_or_create_session(
        self,
        *,
        session_id: str | None,
        title_hint: str,
        entry_mode: str,
        run_kind: str,
        domain_workspace_id: str | None,
        subject_id: str | None,
        agent_monitor_id: str | None,
        trigger_kind: str | None,
        run_preset_id: str | None,
        workflow_recipe_version_id: str | None,
    ) -> PromptSession:
        if session_id:
            session = await self.db.get(PromptSession, session_id)
            if session is None:
                raise PromptAgentRequestError(
                    'PROMPT_SESSION_NOT_FOUND',
                    'prompt session does not exist',
                    status_code=404,
                )
            if run_preset_id:
                session.run_preset_id = run_preset_id
            if workflow_recipe_version_id:
                session.workflow_recipe_version_id = workflow_recipe_version_id
            if domain_workspace_id:
                session.domain_workspace_id = domain_workspace_id
            if subject_id:
                session.subject_id = subject_id
            if agent_monitor_id:
                session.agent_monitor_id = agent_monitor_id
            if trigger_kind:
                session.trigger_kind = trigger_kind
            session.run_kind = run_kind
            return session

        session = PromptSession(
            id=str(uuid.uuid4()),
            title=title_hint,
            entry_mode=entry_mode,
            status='active',
            run_kind=run_kind,
            domain_workspace_id=domain_workspace_id,
            subject_id=subject_id,
            agent_monitor_id=agent_monitor_id,
            trigger_kind=trigger_kind,
            run_preset_id=run_preset_id,
            workflow_recipe_version_id=workflow_recipe_version_id,
            metadata_json=_json_dumps({'created_by': 'prompt_agent'}),
        )
        self.db.add(session)
        await self.db.flush()
        return session
