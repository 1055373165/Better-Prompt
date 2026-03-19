from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_session import PromptSession
from app.models.run_preset import RunPreset
from app.models.workflow_recipe import WorkflowRecipe
from app.models.workflow_recipe_version import WorkflowRecipeVersion
from app.schemas.prompt_session import (
    CreatePromptSessionRequest,
    ListPromptSessionsResponse,
    PromptSessionDetail,
    PromptSessionSummary,
)


class PromptSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, request: CreatePromptSessionRequest) -> PromptSessionDetail:
        session = PromptSession(
            id=str(uuid.uuid4()),
            title=request.title,
            entry_mode=request.entry_mode,
            status='active',
            run_kind=request.run_kind,
            domain_workspace_id=request.domain_workspace_id,
            subject_id=request.subject_id,
            agent_monitor_id=request.agent_monitor_id,
            trigger_kind=request.trigger_kind,
            metadata_json=json.dumps(request.metadata, ensure_ascii=False),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return self._to_detail(session)

    async def get_session(self, session_id: str) -> PromptSessionDetail | None:
        session = await self.db.get(PromptSession, session_id)
        if session is None:
            return None
        run_preset_names, workflow_recipe_refs = await self._build_provenance_maps([session])
        return self._to_detail(
            session,
            run_preset_name=run_preset_names.get(session.run_preset_id),
            workflow_recipe_ref=workflow_recipe_refs.get(session.workflow_recipe_version_id),
        )

    async def list_sessions(
        self,
        *,
        run_kind: str | None = None,
        domain_workspace_id: str | None = None,
        subject_id: str | None = None,
        agent_monitor_id: str | None = None,
        trigger_kind: str | None = None,
        run_preset_id: str | None = None,
        workflow_recipe_version_id: str | None = None,
    ) -> ListPromptSessionsResponse:
        query = select(PromptSession)
        if run_kind is not None:
            query = query.where(PromptSession.run_kind == run_kind)
        if domain_workspace_id is not None:
            query = query.where(PromptSession.domain_workspace_id == domain_workspace_id)
        if subject_id is not None:
            query = query.where(PromptSession.subject_id == subject_id)
        if agent_monitor_id is not None:
            query = query.where(PromptSession.agent_monitor_id == agent_monitor_id)
        if trigger_kind is not None:
            query = query.where(PromptSession.trigger_kind == trigger_kind)
        if run_preset_id is not None:
            query = query.where(PromptSession.run_preset_id == run_preset_id)
        if workflow_recipe_version_id is not None:
            query = query.where(PromptSession.workflow_recipe_version_id == workflow_recipe_version_id)

        result = await self.db.execute(query.order_by(PromptSession.updated_at.desc()))
        sessions = result.scalars().all()
        run_preset_names, workflow_recipe_refs = await self._build_provenance_maps(sessions)
        items = [
            self._to_summary(
                item,
                run_preset_name=run_preset_names.get(item.run_preset_id),
                workflow_recipe_ref=workflow_recipe_refs.get(item.workflow_recipe_version_id),
            )
            for item in sessions
        ]
        return ListPromptSessionsResponse(items=items)

    async def _build_provenance_maps(
        self,
        sessions: list[PromptSession],
    ) -> tuple[dict[str, str], dict[str, tuple[str | None, int | None]]]:
        run_preset_ids = {session.run_preset_id for session in sessions if session.run_preset_id}
        workflow_recipe_version_ids = {
            session.workflow_recipe_version_id for session in sessions if session.workflow_recipe_version_id
        }

        run_preset_names: dict[str, str] = {}
        if run_preset_ids:
            result = await self.db.execute(select(RunPreset.id, RunPreset.name).where(RunPreset.id.in_(run_preset_ids)))
            run_preset_names = {preset_id: preset_name for preset_id, preset_name in result.all()}

        workflow_recipe_refs: dict[str, tuple[str | None, int | None]] = {}
        if workflow_recipe_version_ids:
            result = await self.db.execute(
                select(
                    WorkflowRecipeVersion.id,
                    WorkflowRecipe.name,
                    WorkflowRecipeVersion.version_number,
                )
                .join(WorkflowRecipe, WorkflowRecipe.id == WorkflowRecipeVersion.workflow_recipe_id)
                .where(WorkflowRecipeVersion.id.in_(workflow_recipe_version_ids))
            )
            workflow_recipe_refs = {
                version_id: (workflow_recipe_name, version_number)
                for version_id, workflow_recipe_name, version_number in result.all()
            }

        return run_preset_names, workflow_recipe_refs

    def _to_summary(
        self,
        session: PromptSession,
        *,
        run_preset_name: str | None = None,
        workflow_recipe_ref: tuple[str | None, int | None] | None = None,
    ) -> PromptSessionSummary:
        workflow_recipe_name, workflow_recipe_version_number = workflow_recipe_ref or (None, None)
        return PromptSessionSummary(
            id=session.id,
            title=session.title,
            entry_mode=session.entry_mode,
            status=session.status,
            run_kind=session.run_kind,
            domain_workspace_id=session.domain_workspace_id,
            subject_id=session.subject_id,
            agent_monitor_id=session.agent_monitor_id,
            trigger_kind=session.trigger_kind,
            run_preset_id=session.run_preset_id,
            run_preset_name=run_preset_name,
            workflow_recipe_version_id=session.workflow_recipe_version_id,
            workflow_recipe_name=workflow_recipe_name,
            workflow_recipe_version_number=workflow_recipe_version_number,
            latest_iteration_id=session.latest_iteration_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _to_detail(
        self,
        session: PromptSession,
        *,
        run_preset_name: str | None = None,
        workflow_recipe_ref: tuple[str | None, int | None] | None = None,
    ) -> PromptSessionDetail:
        metadata = json.loads(session.metadata_json) if session.metadata_json else {}
        return PromptSessionDetail(
            **self._to_summary(
                session,
                run_preset_name=run_preset_name,
                workflow_recipe_ref=workflow_recipe_ref,
            ).model_dump(),
            metadata=metadata,
        )
