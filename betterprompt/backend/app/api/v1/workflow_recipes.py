from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.workflow_asset import (
    CreateWorkflowRecipeRequest,
    CreateWorkflowRecipeVersionRequest,
    ListWorkflowRecipesResponse,
    ListWorkflowRecipeVersionsResponse,
    UpdateWorkflowRecipeRequest,
    WorkflowRecipeDetail,
)
from app.services.workflow_asset_service import (
    WorkflowAssetNotFoundError,
    WorkflowAssetValidationError,
    WorkflowRecipeService,
)

router = APIRouter(prefix='/workflow-recipes', tags=['workflow-recipes'])


def _asset_error(status_code: int, exc: WorkflowAssetNotFoundError | WorkflowAssetValidationError) -> HTTPException:
    return HTTPException(status_code=status_code, detail={'code': exc.code, 'message': exc.message})


@router.get('', response_model=ListWorkflowRecipesResponse)
async def list_workflow_recipes(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    archived: bool = False,
    domain_hint: str | None = None,
) -> ListWorkflowRecipesResponse:
    service = WorkflowRecipeService(db)
    return await service.list_workflow_recipes(
        page=page,
        page_size=page_size,
        q=q,
        archived=archived,
        domain_hint=domain_hint,
    )


@router.post('', response_model=WorkflowRecipeDetail, status_code=status.HTTP_201_CREATED)
async def create_workflow_recipe(request: CreateWorkflowRecipeRequest, db: DbSession) -> WorkflowRecipeDetail:
    service = WorkflowRecipeService(db)
    try:
        return await service.create_workflow_recipe(request)
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/{workflow_recipe_id}', response_model=WorkflowRecipeDetail)
async def get_workflow_recipe(workflow_recipe_id: str, db: DbSession) -> WorkflowRecipeDetail:
    service = WorkflowRecipeService(db)
    recipe = await service.get_workflow_recipe(workflow_recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'WORKFLOW_RECIPE_NOT_FOUND', 'message': 'WORKFLOW_RECIPE_NOT_FOUND'},
        )
    return recipe


@router.patch('/{workflow_recipe_id}', response_model=WorkflowRecipeDetail)
async def update_workflow_recipe(
    workflow_recipe_id: str,
    request: UpdateWorkflowRecipeRequest,
    db: DbSession,
) -> WorkflowRecipeDetail:
    service = WorkflowRecipeService(db)
    try:
        return await service.update_workflow_recipe(workflow_recipe_id, request)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/{workflow_recipe_id}/versions', response_model=ListWorkflowRecipeVersionsResponse)
async def list_workflow_recipe_versions(
    workflow_recipe_id: str,
    db: DbSession,
) -> ListWorkflowRecipeVersionsResponse:
    service = WorkflowRecipeService(db)
    try:
        return await service.list_versions(workflow_recipe_id)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post('/{workflow_recipe_id}/versions', response_model=WorkflowRecipeDetail, status_code=status.HTTP_201_CREATED)
async def create_workflow_recipe_version(
    workflow_recipe_id: str,
    request: CreateWorkflowRecipeVersionRequest,
    db: DbSession,
) -> WorkflowRecipeDetail:
    service = WorkflowRecipeService(db)
    try:
        return await service.create_version(workflow_recipe_id, request)
    except WorkflowAssetNotFoundError as exc:
        raise _asset_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except WorkflowAssetValidationError as exc:
        raise _asset_error(status.HTTP_400_BAD_REQUEST, exc) from exc
