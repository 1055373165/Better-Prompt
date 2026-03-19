from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.prompt_session import (
    CreatePromptSessionRequest,
    ListPromptSessionsResponse,
    PromptSessionDetail,
    PromptSessionRunKind,
)
from app.services.prompt_session_service import PromptSessionService

router = APIRouter(prefix='/prompt-sessions', tags=['prompt-sessions'])


@router.post('', response_model=PromptSessionDetail)
async def create_prompt_session(request: CreatePromptSessionRequest, db: DbSession) -> PromptSessionDetail:
    service = PromptSessionService(db)
    return await service.create_session(request)


@router.get('', response_model=ListPromptSessionsResponse)
async def list_prompt_sessions(
    db: DbSession,
    run_kind: PromptSessionRunKind | None = None,
    domain_workspace_id: str | None = None,
    subject_id: str | None = None,
    agent_monitor_id: str | None = None,
    trigger_kind: str | None = None,
    run_preset_id: str | None = None,
    workflow_recipe_version_id: str | None = None,
) -> ListPromptSessionsResponse:
    service = PromptSessionService(db)
    return await service.list_sessions(
        run_kind=run_kind,
        domain_workspace_id=domain_workspace_id,
        subject_id=subject_id,
        agent_monitor_id=agent_monitor_id,
        trigger_kind=trigger_kind,
        run_preset_id=run_preset_id,
        workflow_recipe_version_id=workflow_recipe_version_id,
    )


@router.get('/{session_id}', response_model=PromptSessionDetail)
async def get_prompt_session(session_id: str, db: DbSession) -> PromptSessionDetail:
    service = PromptSessionService(db)
    session = await service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail='Prompt session not found')
    return session
