from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.workflow_asset import (
    ContextPackDetail,
    CreateContextPackRequest,
    CreateContextPackVersionRequest,
    ListContextPacksResponse,
    ListContextPackVersionsResponse,
    UpdateContextPackRequest,
)
from app.services.workflow_asset_service import (
    ContextPackService,
    WorkflowAssetNotFoundError,
    WorkflowAssetValidationError,
)

router = APIRouter(prefix='/context-packs', tags=['context-packs'])


def _asset_error(status_code: int, exc: WorkflowAssetNotFoundError | WorkflowAssetValidationError) -> HTTPException:
    return HTTPException(status_code=status_code, detail={'code': exc.code, 'message': exc.message})


@router.get('', response_model=ListContextPacksResponse)
async def list_context_packs(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    archived: bool = False,
) -> ListContextPacksResponse:
    service = ContextPackService(db)
    return await service.list_context_packs(page=page, page_size=page_size, q=q, archived=archived)


@router.post('', response_model=ContextPackDetail, status_code=status.HTTP_201_CREATED)
async def create_context_pack(request: CreateContextPackRequest, db: DbSession) -> ContextPackDetail:
    service = ContextPackService(db)
    try:
        return await service.create_context_pack(request)
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/{context_pack_id}', response_model=ContextPackDetail)
async def get_context_pack(context_pack_id: str, db: DbSession) -> ContextPackDetail:
    service = ContextPackService(db)
    context_pack = await service.get_context_pack(context_pack_id)
    if context_pack is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'CONTEXT_PACK_NOT_FOUND', 'message': 'CONTEXT_PACK_NOT_FOUND'},
        )
    return context_pack


@router.patch('/{context_pack_id}', response_model=ContextPackDetail)
async def update_context_pack(
    context_pack_id: str,
    request: UpdateContextPackRequest,
    db: DbSession,
) -> ContextPackDetail:
    service = ContextPackService(db)
    try:
        return await service.update_context_pack(context_pack_id, request)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/{context_pack_id}/versions', response_model=ListContextPackVersionsResponse)
async def list_context_pack_versions(context_pack_id: str, db: DbSession) -> ListContextPackVersionsResponse:
    service = ContextPackService(db)
    try:
        return await service.list_versions(context_pack_id)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post('/{context_pack_id}/versions', response_model=ContextPackDetail, status_code=status.HTTP_201_CREATED)
async def create_context_pack_version(
    context_pack_id: str,
    request: CreateContextPackVersionRequest,
    db: DbSession,
) -> ContextPackDetail:
    service = ContextPackService(db)
    try:
        return await service.create_version(context_pack_id, request)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc
