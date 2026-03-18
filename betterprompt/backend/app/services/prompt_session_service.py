from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_session import PromptSession
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
        return self._to_detail(session)

    async def list_sessions(self) -> ListPromptSessionsResponse:
        result = await self.db.execute(select(PromptSession).order_by(PromptSession.updated_at.desc()))
        items = [self._to_summary(item) for item in result.scalars().all()]
        return ListPromptSessionsResponse(items=items)

    def _to_summary(self, session: PromptSession) -> PromptSessionSummary:
        return PromptSessionSummary(
            id=session.id,
            title=session.title,
            entry_mode=session.entry_mode,
            status=session.status,
            run_kind=session.run_kind,
            run_preset_id=session.run_preset_id,
            workflow_recipe_version_id=session.workflow_recipe_version_id,
            latest_iteration_id=session.latest_iteration_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _to_detail(self, session: PromptSession) -> PromptSessionDetail:
        metadata = json.loads(session.metadata_json) if session.metadata_json else {}
        return PromptSessionDetail(**self._to_summary(session).model_dump(), metadata=metadata)
