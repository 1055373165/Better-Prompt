from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.prompt_agent import (
    ContinuePromptResponse,
    DebugPromptResponse,
    EvaluatePromptResponse,
    GeneratePromptResponse,
)
from app.schemas.workflow_asset import (
    CreateRunPresetRequest,
    ListRunPresetsResponse,
    RunPresetLaunchRequest,
    RunPresetDetail,
    UpdateRunPresetRequest,
)
from app.services.llm import PromptLLMConfigurationError, PromptLLMRequestError
from app.services.prompt_agent.errors import PromptAgentRequestError
from app.services.prompt_agent_service import PromptAgentService
from app.services.run_preset_launch_service import RunPresetLaunchService
from app.services.workflow_asset_service import (
    RunPresetService,
    WorkflowAssetNotFoundError,
    WorkflowAssetValidationError,
)

router = APIRouter(prefix='/run-presets', tags=['run-presets'])


def _asset_error(status_code: int, exc: WorkflowAssetNotFoundError | WorkflowAssetValidationError) -> HTTPException:
    return HTTPException(status_code=status_code, detail={'code': exc.code, 'message': exc.message})


@router.get('', response_model=ListRunPresetsResponse)
async def list_run_presets(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    archived: bool = False,
) -> ListRunPresetsResponse:
    service = RunPresetService(db)
    return await service.list_run_presets(page=page, page_size=page_size, q=q, archived=archived)


@router.post('', response_model=RunPresetDetail, status_code=status.HTTP_201_CREATED)
async def create_run_preset(request: CreateRunPresetRequest, db: DbSession) -> RunPresetDetail:
    service = RunPresetService(db)
    try:
        return await service.create_run_preset(request)
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/{run_preset_id}', response_model=RunPresetDetail)
async def get_run_preset(run_preset_id: str, db: DbSession) -> RunPresetDetail:
    service = RunPresetService(db)
    run_preset = await service.get_run_preset(run_preset_id)
    if run_preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'RUN_PRESET_NOT_FOUND', 'message': 'RUN_PRESET_NOT_FOUND'},
        )
    return run_preset


@router.patch('/{run_preset_id}', response_model=RunPresetDetail)
async def update_run_preset(
    run_preset_id: str,
    request: UpdateRunPresetRequest,
    db: DbSession,
) -> RunPresetDetail:
    service = RunPresetService(db)
    try:
        return await service.update_run_preset(run_preset_id, request)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.post(
    '/{run_preset_id}/launch',
    response_model=GeneratePromptResponse | DebugPromptResponse | EvaluatePromptResponse | ContinuePromptResponse,
)
async def launch_run_preset(
    run_preset_id: str,
    request: RunPresetLaunchRequest,
    db: DbSession,
) -> GeneratePromptResponse | DebugPromptResponse | EvaluatePromptResponse | ContinuePromptResponse:
    launch_service = RunPresetLaunchService(db)
    prompt_agent_service = PromptAgentService(db)
    try:
        mode, payload = await launch_service.build_launch_request(run_preset_id, request)
        if mode == 'generate':
            response = await prompt_agent_service.generate(payload)
        elif mode == 'debug':
            response = await prompt_agent_service.debug(payload)
        elif mode == 'evaluate':
            response = await prompt_agent_service.evaluate(payload)
        else:
            response = await prompt_agent_service.continue_optimization(payload)
        await launch_service.mark_used(run_preset_id)
        return response
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc
    except PromptAgentRequestError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={'code': exc.code, 'message': exc.message},
        ) from exc
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
