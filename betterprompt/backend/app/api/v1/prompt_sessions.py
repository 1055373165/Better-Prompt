from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.prompt_session import CreatePromptSessionRequest, ListPromptSessionsResponse, PromptSessionDetail
from app.services.prompt_session_service import PromptSessionService

router = APIRouter(prefix='/prompt-sessions', tags=['prompt-sessions'])


@router.post('', response_model=PromptSessionDetail)
async def create_prompt_session(request: CreatePromptSessionRequest, db: DbSession) -> PromptSessionDetail:
    service = PromptSessionService(db)
    return await service.create_session(request)


@router.get('', response_model=ListPromptSessionsResponse)
async def list_prompt_sessions(db: DbSession) -> ListPromptSessionsResponse:
    service = PromptSessionService(db)
    return await service.list_sessions()


@router.get('/{session_id}', response_model=PromptSessionDetail)
async def get_prompt_session(session_id: str, db: DbSession) -> PromptSessionDetail:
    service = PromptSessionService(db)
    session = await service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail='Prompt session not found')
    return session
