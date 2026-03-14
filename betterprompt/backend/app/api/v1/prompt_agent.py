from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession
from app.schemas.prompt_agent import (
    ContinuePromptRequest,
    ContinuePromptResponse,
    DebugPromptRequest,
    DebugPromptResponse,
    EvaluatePromptRequest,
    EvaluatePromptResponse,
    GeneratePromptRequest,
    GeneratePromptResponse,
)
from app.services.llm import PromptLLMConfigurationError, PromptLLMRequestError
from app.services.prompt_agent_service import PromptAgentService

router = APIRouter(prefix='/prompt-agent', tags=['prompt-agent'])


@router.post('/generate', response_model=GeneratePromptResponse)
async def generate_prompt(request: GeneratePromptRequest, db: DbSession) -> GeneratePromptResponse:
    service = PromptAgentService(db)
    try:
        return await service.generate(request)
    except PromptLLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except PromptLLMRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post('/generate/stream')
async def generate_prompt_stream(request: GeneratePromptRequest, db: DbSession):
    service = PromptAgentService(db)
    return StreamingResponse(
        service.generate_stream(request),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@router.post('/debug', response_model=DebugPromptResponse)
async def debug_prompt(request: DebugPromptRequest, db: DbSession) -> DebugPromptResponse:
    service = PromptAgentService(db)
    return await service.debug(request)


@router.post('/evaluate', response_model=EvaluatePromptResponse)
async def evaluate_prompt(request: EvaluatePromptRequest, db: DbSession) -> EvaluatePromptResponse:
    service = PromptAgentService(db)
    return await service.evaluate(request)


@router.post('/continue', response_model=ContinuePromptResponse)
async def continue_optimization(request: ContinuePromptRequest, db: DbSession) -> ContinuePromptResponse:
    service = PromptAgentService(db)
    return await service.continue_optimization(request)
