from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.workflow_asset import (
    CreateEvaluationProfileRequest,
    CreateEvaluationProfileVersionRequest,
    EvaluationProfileDetail,
    ListEvaluationProfilesResponse,
    ListEvaluationProfileVersionsResponse,
    UpdateEvaluationProfileRequest,
)
from app.services.workflow_asset_service import (
    EvaluationProfileService,
    WorkflowAssetNotFoundError,
    WorkflowAssetValidationError,
)

router = APIRouter(prefix='/evaluation-profiles', tags=['evaluation-profiles'])


def _asset_error(status_code: int, exc: WorkflowAssetNotFoundError | WorkflowAssetValidationError) -> HTTPException:
    return HTTPException(status_code=status_code, detail={'code': exc.code, 'message': exc.message})


@router.get('', response_model=ListEvaluationProfilesResponse)
async def list_evaluation_profiles(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    archived: bool = False,
) -> ListEvaluationProfilesResponse:
    service = EvaluationProfileService(db)
    return await service.list_evaluation_profiles(page=page, page_size=page_size, q=q, archived=archived)


@router.post('', response_model=EvaluationProfileDetail, status_code=status.HTTP_201_CREATED)
async def create_evaluation_profile(request: CreateEvaluationProfileRequest, db: DbSession) -> EvaluationProfileDetail:
    service = EvaluationProfileService(db)
    try:
        return await service.create_evaluation_profile(request)
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/{evaluation_profile_id}', response_model=EvaluationProfileDetail)
async def get_evaluation_profile(evaluation_profile_id: str, db: DbSession) -> EvaluationProfileDetail:
    service = EvaluationProfileService(db)
    profile = await service.get_evaluation_profile(evaluation_profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'EVALUATION_PROFILE_NOT_FOUND', 'message': 'EVALUATION_PROFILE_NOT_FOUND'},
        )
    return profile


@router.patch('/{evaluation_profile_id}', response_model=EvaluationProfileDetail)
async def update_evaluation_profile(
    evaluation_profile_id: str,
    request: UpdateEvaluationProfileRequest,
    db: DbSession,
) -> EvaluationProfileDetail:
    service = EvaluationProfileService(db)
    try:
        return await service.update_evaluation_profile(evaluation_profile_id, request)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/{evaluation_profile_id}/versions', response_model=ListEvaluationProfileVersionsResponse)
async def list_evaluation_profile_versions(
    evaluation_profile_id: str,
    db: DbSession,
) -> ListEvaluationProfileVersionsResponse:
    service = EvaluationProfileService(db)
    try:
        return await service.list_versions(evaluation_profile_id)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post(
    '/{evaluation_profile_id}/versions',
    response_model=EvaluationProfileDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation_profile_version(
    evaluation_profile_id: str,
    request: CreateEvaluationProfileVersionRequest,
    db: DbSession,
) -> EvaluationProfileDetail:
    service = EvaluationProfileService(db)
    try:
        return await service.create_version(evaluation_profile_id, request)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc
