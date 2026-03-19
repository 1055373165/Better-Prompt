from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import DbSession
from app.schemas.prompt_asset import (
    CreatePromptAssetRequest,
    CreatePromptAssetVersionRequest,
    CreatePromptCategoryRequest,
    ListPromptAssetsResponse,
    ListPromptAssetVersionsResponse,
    ListPromptCategoryTreeResponse,
    PromptAssetDetail,
    PromptCategoryTreeItem,
    UpdatePromptAssetRequest,
    UpdatePromptCategoryRequest,
)
from app.services.prompt_asset_service import (
    PromptAssetNotFoundError,
    PromptAssetService,
    PromptAssetValidationError,
    PromptCategoryService,
)

router = APIRouter(tags=['prompt-assets'])


def _to_http_exception(exc: PromptAssetNotFoundError | PromptAssetValidationError) -> HTTPException:
    if isinstance(exc, PromptAssetNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return HTTPException(status_code=status_code, detail={'code': exc.code, 'message': exc.message})


@router.get('/prompt-categories/tree', response_model=ListPromptCategoryTreeResponse)
async def list_prompt_category_tree(db: DbSession) -> ListPromptCategoryTreeResponse:
    service = PromptCategoryService(db)
    return await service.list_tree()


@router.post('/prompt-categories', response_model=PromptCategoryTreeItem, status_code=status.HTTP_201_CREATED)
async def create_prompt_category(
    request: CreatePromptCategoryRequest,
    db: DbSession,
) -> PromptCategoryTreeItem:
    service = PromptCategoryService(db)
    try:
        return await service.create_category(request)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc


@router.patch('/prompt-categories/{category_id}', response_model=PromptCategoryTreeItem)
async def update_prompt_category(
    category_id: str,
    request: UpdatePromptCategoryRequest,
    db: DbSession,
) -> PromptCategoryTreeItem:
    service = PromptCategoryService(db)
    try:
        return await service.update_category(category_id, request)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc


@router.delete('/prompt-categories/{category_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_category(category_id: str, db: DbSession) -> Response:
    service = PromptCategoryService(db)
    try:
        await service.delete_category(category_id)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/prompt-assets', response_model=ListPromptAssetsResponse)
async def list_prompt_assets(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=200),
    q: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
    favorites_only: bool = Query(default=False),
    archived: bool = Query(default=False),
) -> ListPromptAssetsResponse:
    service = PromptAssetService(db)
    return await service.list_prompt_assets(
        page=page,
        page_size=page_size,
        q=q,
        category_id=category_id,
        favorites_only=favorites_only,
        archived=archived,
    )


@router.post('/prompt-assets', response_model=PromptAssetDetail, status_code=status.HTTP_201_CREATED)
async def create_prompt_asset(
    request: CreatePromptAssetRequest,
    db: DbSession,
) -> PromptAssetDetail:
    service = PromptAssetService(db)
    try:
        return await service.create_prompt_asset(request)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc


@router.get('/prompt-assets/{asset_id}', response_model=PromptAssetDetail)
async def get_prompt_asset(asset_id: str, db: DbSession) -> PromptAssetDetail:
    service = PromptAssetService(db)
    try:
        return await service.get_prompt_asset(asset_id)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc


@router.patch('/prompt-assets/{asset_id}', response_model=PromptAssetDetail)
async def update_prompt_asset(
    asset_id: str,
    request: UpdatePromptAssetRequest,
    db: DbSession,
) -> PromptAssetDetail:
    service = PromptAssetService(db)
    try:
        return await service.update_prompt_asset(asset_id, request)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc


@router.delete('/prompt-assets/{asset_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_asset(asset_id: str, db: DbSession) -> Response:
    service = PromptAssetService(db)
    try:
        await service.archive_prompt_asset(asset_id)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/prompt-assets/{asset_id}/versions', response_model=ListPromptAssetVersionsResponse)
async def list_prompt_asset_versions(asset_id: str, db: DbSession) -> ListPromptAssetVersionsResponse:
    service = PromptAssetService(db)
    try:
        return await service.list_versions(asset_id)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc


@router.post('/prompt-assets/{asset_id}/versions', response_model=PromptAssetDetail, status_code=status.HTTP_201_CREATED)
async def create_prompt_asset_version(
    asset_id: str,
    request: CreatePromptAssetVersionRequest,
    db: DbSession,
) -> PromptAssetDetail:
    service = PromptAssetService(db)
    try:
        return await service.create_version(asset_id, request)
    except (PromptAssetNotFoundError, PromptAssetValidationError) as exc:
        raise _to_http_exception(exc) from exc
