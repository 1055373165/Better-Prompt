from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context_pack import ContextPack
from app.models.context_pack_version import ContextPackVersion
from app.models.evaluation_profile import EvaluationProfile
from app.models.evaluation_profile_version import EvaluationProfileVersion
from app.models.prompt_asset_version import PromptAssetVersion
from app.models.run_preset import RunPreset
from app.models.workflow_recipe import WorkflowRecipe
from app.models.workflow_recipe_version import WorkflowRecipeVersion
from app.schemas.workflow_asset import (
    ContextPackDetail,
    ContextPackSummary,
    ContextPackVersionDetail,
    CreateContextPackRequest,
    CreateContextPackVersionRequest,
    CreateEvaluationProfileRequest,
    CreateEvaluationProfileVersionRequest,
    CreateRunPresetRequest,
    CreateWorkflowRecipeRequest,
    CreateWorkflowRecipeVersionRequest,
    EvaluationProfileDetail,
    EvaluationProfileSummary,
    EvaluationProfileVersionDetail,
    ListContextPacksResponse,
    ListContextPackVersionsResponse,
    ListEvaluationProfilesResponse,
    ListEvaluationProfileVersionsResponse,
    ListRunPresetsResponse,
    ListWorkflowRecipesResponse,
    ListWorkflowRecipeVersionsResponse,
    RunPresetDetail,
    RunPresetSummary,
    UpdateContextPackRequest,
    UpdateEvaluationProfileRequest,
    UpdateRunPresetRequest,
    UpdateWorkflowRecipeRequest,
    WorkflowAssetVersionSummary,
    WorkflowRecipeDetail,
    WorkflowRecipeSummary,
    WorkflowRecipeVersionDetail,
)


MAX_PAGE_SIZE = 100
ALLOWED_RECIPE_STEP_MODES = {'generate', 'debug', 'evaluate', 'continue'}


class WorkflowAssetNotFoundError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


class WorkflowAssetValidationError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


def _normalize_page(page: int, page_size: int) -> tuple[int, int]:
    safe_page = max(page, 1)
    safe_page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    return safe_page, safe_page_size


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load_json(raw_value: str | None, default: Any) -> Any:
    if not raw_value:
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def _load_json_dict(raw_value: str | None) -> dict[str, Any]:
    payload = _load_json(raw_value, {})
    return payload if isinstance(payload, dict) else {}


def _load_json_list(raw_value: str | None) -> list[str]:
    payload = _load_json(raw_value, [])
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, str)]


async def _next_version_number(
    db: AsyncSession,
    version_model: type[ContextPackVersion] | type[EvaluationProfileVersion] | type[WorkflowRecipeVersion],
    foreign_key_column,
    asset_id: str,
) -> int:
    result = await db.execute(select(func.max(version_model.version_number)).where(foreign_key_column == asset_id))
    return (result.scalar_one_or_none() or 0) + 1


class ContextPackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_context_packs(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        q: str | None = None,
        archived: bool = False,
    ) -> ListContextPacksResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(ContextPack)
        query = query.where(ContextPack.archived_at.is_not(None) if archived else ContextPack.archived_at.is_(None))
        if q:
            search_term = f'%{q.strip()}%'
            query = query.where(
                or_(
                    ContextPack.name.ilike(search_term),
                    ContextPack.description.ilike(search_term),
                )
            )
        query = query.order_by(ContextPack.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        context_packs = result.scalars().all()

        version_ids = {item.current_version_id for item in context_packs if item.current_version_id}
        version_map = await self._load_current_versions(version_ids)
        items = [self._to_summary(item, version_map.get(item.current_version_id)) for item in context_packs]
        return ListContextPacksResponse(items=items)

    async def create_context_pack(self, request: CreateContextPackRequest) -> ContextPackDetail:
        context_pack = ContextPack(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            tags_json=_dump_json(request.tags),
        )
        version = ContextPackVersion(
            id=str(uuid.uuid4()),
            context_pack_id=context_pack.id,
            version_number=1,
            payload_json=_dump_json(request.payload),
            source_iteration_id=request.source_iteration_id,
            change_summary=request.change_summary,
        )
        context_pack.current_version_id = version.id
        self.db.add(context_pack)
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(context_pack)
        await self.db.refresh(version)
        return self._to_detail(context_pack, version)

    async def get_context_pack(self, context_pack_id: str) -> ContextPackDetail | None:
        context_pack = await self.db.get(ContextPack, context_pack_id)
        if context_pack is None:
            return None
        version = await self._get_current_version(context_pack.current_version_id)
        return self._to_detail(context_pack, version)

    async def update_context_pack(
        self,
        context_pack_id: str,
        request: UpdateContextPackRequest,
    ) -> ContextPackDetail:
        context_pack = await self._require_context_pack(context_pack_id)
        if 'name' in request.model_fields_set:
            context_pack.name = request.name
        if 'description' in request.model_fields_set:
            context_pack.description = request.description
        if 'tags' in request.model_fields_set:
            context_pack.tags_json = _dump_json(request.tags or [])
        if 'archived_at' in request.model_fields_set:
            context_pack.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(context_pack)
        version = await self._get_current_version(context_pack.current_version_id)
        return self._to_detail(context_pack, version)

    async def list_versions(self, context_pack_id: str) -> ListContextPackVersionsResponse:
        await self._require_context_pack(context_pack_id)
        result = await self.db.execute(
            select(ContextPackVersion)
            .where(ContextPackVersion.context_pack_id == context_pack_id)
            .order_by(ContextPackVersion.version_number.desc())
        )
        items = [self._to_version_detail(version) for version in result.scalars().all()]
        return ListContextPackVersionsResponse(items=items)

    async def create_version(
        self,
        context_pack_id: str,
        request: CreateContextPackVersionRequest,
    ) -> ContextPackDetail:
        context_pack = await self._require_context_pack(context_pack_id)
        version_number = await _next_version_number(
            self.db,
            ContextPackVersion,
            ContextPackVersion.context_pack_id,
            context_pack_id,
        )
        version = ContextPackVersion(
            id=str(uuid.uuid4()),
            context_pack_id=context_pack_id,
            version_number=version_number,
            payload_json=_dump_json(request.payload),
            source_iteration_id=request.source_iteration_id,
            change_summary=request.change_summary,
        )
        context_pack.current_version_id = version.id
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(context_pack)
        await self.db.refresh(version)
        return self._to_detail(context_pack, version)

    async def _require_context_pack(self, context_pack_id: str) -> ContextPack:
        context_pack = await self.db.get(ContextPack, context_pack_id)
        if context_pack is None:
            raise WorkflowAssetNotFoundError('CONTEXT_PACK_NOT_FOUND')
        return context_pack

    async def _get_current_version(self, version_id: str | None) -> ContextPackVersion | None:
        if not version_id:
            return None
        return await self.db.get(ContextPackVersion, version_id)

    async def _load_current_versions(self, version_ids: set[str]) -> dict[str, ContextPackVersion]:
        if not version_ids:
            return {}
        result = await self.db.execute(select(ContextPackVersion).where(ContextPackVersion.id.in_(version_ids)))
        return {item.id: item for item in result.scalars().all()}

    def _to_summary(
        self,
        context_pack: ContextPack,
        current_version: ContextPackVersion | None,
    ) -> ContextPackSummary:
        return ContextPackSummary(
            id=context_pack.id,
            name=context_pack.name,
            description=context_pack.description,
            tags=_load_json_list(context_pack.tags_json),
            current_version=self._to_version_summary(current_version),
            updated_at=context_pack.updated_at,
        )

    def _to_detail(
        self,
        context_pack: ContextPack,
        current_version: ContextPackVersion | None,
    ) -> ContextPackDetail:
        summary = self._to_summary(context_pack, current_version)
        return ContextPackDetail(
            id=summary.id,
            name=summary.name,
            description=summary.description,
            tags=summary.tags,
            current_version=self._to_version_detail(current_version),
            updated_at=summary.updated_at,
            created_at=context_pack.created_at,
            archived_at=context_pack.archived_at,
        )

    def _to_version_summary(self, version: ContextPackVersion | None) -> WorkflowAssetVersionSummary | None:
        if version is None:
            return None
        return WorkflowAssetVersionSummary(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
        )

    def _to_version_detail(self, version: ContextPackVersion | None) -> ContextPackVersionDetail | None:
        if version is None:
            return None
        return ContextPackVersionDetail(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
            payload=_load_json_dict(version.payload_json),
            source_iteration_id=version.source_iteration_id,
        )


class EvaluationProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_evaluation_profiles(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        q: str | None = None,
        archived: bool = False,
    ) -> ListEvaluationProfilesResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(EvaluationProfile)
        query = query.where(
            EvaluationProfile.archived_at.is_not(None) if archived else EvaluationProfile.archived_at.is_(None)
        )
        if q:
            search_term = f'%{q.strip()}%'
            query = query.where(
                or_(
                    EvaluationProfile.name.ilike(search_term),
                    EvaluationProfile.description.ilike(search_term),
                )
            )
        query = query.order_by(EvaluationProfile.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        profiles = result.scalars().all()

        version_ids = {item.current_version_id for item in profiles if item.current_version_id}
        version_map = await self._load_current_versions(version_ids)
        items = [self._to_summary(item, version_map.get(item.current_version_id)) for item in profiles]
        return ListEvaluationProfilesResponse(items=items)

    async def create_evaluation_profile(self, request: CreateEvaluationProfileRequest) -> EvaluationProfileDetail:
        profile = EvaluationProfile(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
        )
        version = EvaluationProfileVersion(
            id=str(uuid.uuid4()),
            evaluation_profile_id=profile.id,
            version_number=1,
            rules_json=_dump_json(request.rules),
            change_summary=request.change_summary,
        )
        profile.current_version_id = version.id
        self.db.add(profile)
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(profile)
        await self.db.refresh(version)
        return self._to_detail(profile, version)

    async def get_evaluation_profile(self, evaluation_profile_id: str) -> EvaluationProfileDetail | None:
        profile = await self.db.get(EvaluationProfile, evaluation_profile_id)
        if profile is None:
            return None
        version = await self._get_current_version(profile.current_version_id)
        return self._to_detail(profile, version)

    async def update_evaluation_profile(
        self,
        evaluation_profile_id: str,
        request: UpdateEvaluationProfileRequest,
    ) -> EvaluationProfileDetail:
        profile = await self._require_profile(evaluation_profile_id)
        if 'name' in request.model_fields_set:
            profile.name = request.name
        if 'description' in request.model_fields_set:
            profile.description = request.description
        if 'archived_at' in request.model_fields_set:
            profile.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(profile)
        version = await self._get_current_version(profile.current_version_id)
        return self._to_detail(profile, version)

    async def list_versions(self, evaluation_profile_id: str) -> ListEvaluationProfileVersionsResponse:
        await self._require_profile(evaluation_profile_id)
        result = await self.db.execute(
            select(EvaluationProfileVersion)
            .where(EvaluationProfileVersion.evaluation_profile_id == evaluation_profile_id)
            .order_by(EvaluationProfileVersion.version_number.desc())
        )
        items = [self._to_version_detail(version) for version in result.scalars().all()]
        return ListEvaluationProfileVersionsResponse(items=items)

    async def create_version(
        self,
        evaluation_profile_id: str,
        request: CreateEvaluationProfileVersionRequest,
    ) -> EvaluationProfileDetail:
        profile = await self._require_profile(evaluation_profile_id)
        version_number = await _next_version_number(
            self.db,
            EvaluationProfileVersion,
            EvaluationProfileVersion.evaluation_profile_id,
            evaluation_profile_id,
        )
        version = EvaluationProfileVersion(
            id=str(uuid.uuid4()),
            evaluation_profile_id=evaluation_profile_id,
            version_number=version_number,
            rules_json=_dump_json(request.rules),
            change_summary=request.change_summary,
        )
        profile.current_version_id = version.id
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(profile)
        await self.db.refresh(version)
        return self._to_detail(profile, version)

    async def _require_profile(self, evaluation_profile_id: str) -> EvaluationProfile:
        profile = await self.db.get(EvaluationProfile, evaluation_profile_id)
        if profile is None:
            raise WorkflowAssetNotFoundError('EVALUATION_PROFILE_NOT_FOUND')
        return profile

    async def _get_current_version(self, version_id: str | None) -> EvaluationProfileVersion | None:
        if not version_id:
            return None
        return await self.db.get(EvaluationProfileVersion, version_id)

    async def _load_current_versions(self, version_ids: set[str]) -> dict[str, EvaluationProfileVersion]:
        if not version_ids:
            return {}
        result = await self.db.execute(
            select(EvaluationProfileVersion).where(EvaluationProfileVersion.id.in_(version_ids))
        )
        return {item.id: item for item in result.scalars().all()}

    def _to_summary(
        self,
        profile: EvaluationProfile,
        current_version: EvaluationProfileVersion | None,
    ) -> EvaluationProfileSummary:
        return EvaluationProfileSummary(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            current_version=self._to_version_summary(current_version),
            updated_at=profile.updated_at,
        )

    def _to_detail(
        self,
        profile: EvaluationProfile,
        current_version: EvaluationProfileVersion | None,
    ) -> EvaluationProfileDetail:
        summary = self._to_summary(profile, current_version)
        return EvaluationProfileDetail(
            id=summary.id,
            name=summary.name,
            description=summary.description,
            current_version=self._to_version_detail(current_version),
            updated_at=summary.updated_at,
            created_at=profile.created_at,
            archived_at=profile.archived_at,
        )

    def _to_version_summary(self, version: EvaluationProfileVersion | None) -> WorkflowAssetVersionSummary | None:
        if version is None:
            return None
        return WorkflowAssetVersionSummary(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
        )

    def _to_version_detail(
        self,
        version: EvaluationProfileVersion | None,
    ) -> EvaluationProfileVersionDetail | None:
        if version is None:
            return None
        return EvaluationProfileVersionDetail(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
            rules=_load_json_dict(version.rules_json),
        )


class WorkflowRecipeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_workflow_recipes(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        q: str | None = None,
        archived: bool = False,
        domain_hint: str | None = None,
    ) -> ListWorkflowRecipesResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(WorkflowRecipe)
        query = query.where(WorkflowRecipe.archived_at.is_not(None) if archived else WorkflowRecipe.archived_at.is_(None))
        if q:
            search_term = f'%{q.strip()}%'
            query = query.where(
                or_(
                    WorkflowRecipe.name.ilike(search_term),
                    WorkflowRecipe.description.ilike(search_term),
                )
            )
        if domain_hint:
            query = query.where(WorkflowRecipe.domain_hint == domain_hint)
        query = query.order_by(WorkflowRecipe.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        recipes = result.scalars().all()

        version_ids = {item.current_version_id for item in recipes if item.current_version_id}
        version_map = await self._load_current_versions(version_ids)
        items = [self._to_summary(item, version_map.get(item.current_version_id)) for item in recipes]
        return ListWorkflowRecipesResponse(items=items)

    async def create_workflow_recipe(self, request: CreateWorkflowRecipeRequest) -> WorkflowRecipeDetail:
        self._validate_definition(request.definition)
        recipe = WorkflowRecipe(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            domain_hint=request.domain_hint,
        )
        version = WorkflowRecipeVersion(
            id=str(uuid.uuid4()),
            workflow_recipe_id=recipe.id,
            version_number=1,
            definition_json=_dump_json(request.definition),
            source_iteration_id=request.source_iteration_id,
            change_summary=request.change_summary,
        )
        recipe.current_version_id = version.id
        self.db.add(recipe)
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(recipe)
        await self.db.refresh(version)
        return self._to_detail(recipe, version)

    async def get_workflow_recipe(self, workflow_recipe_id: str) -> WorkflowRecipeDetail | None:
        recipe = await self.db.get(WorkflowRecipe, workflow_recipe_id)
        if recipe is None:
            return None
        version = await self._get_current_version(recipe.current_version_id)
        return self._to_detail(recipe, version)

    async def update_workflow_recipe(
        self,
        workflow_recipe_id: str,
        request: UpdateWorkflowRecipeRequest,
    ) -> WorkflowRecipeDetail:
        recipe = await self._require_recipe(workflow_recipe_id)
        if 'name' in request.model_fields_set:
            recipe.name = request.name
        if 'description' in request.model_fields_set:
            recipe.description = request.description
        if 'domain_hint' in request.model_fields_set:
            recipe.domain_hint = request.domain_hint
        if 'archived_at' in request.model_fields_set:
            recipe.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(recipe)
        version = await self._get_current_version(recipe.current_version_id)
        return self._to_detail(recipe, version)

    async def list_versions(self, workflow_recipe_id: str) -> ListWorkflowRecipeVersionsResponse:
        await self._require_recipe(workflow_recipe_id)
        result = await self.db.execute(
            select(WorkflowRecipeVersion)
            .where(WorkflowRecipeVersion.workflow_recipe_id == workflow_recipe_id)
            .order_by(WorkflowRecipeVersion.version_number.desc())
        )
        items = [self._to_version_detail(version) for version in result.scalars().all()]
        return ListWorkflowRecipeVersionsResponse(items=items)

    async def create_version(
        self,
        workflow_recipe_id: str,
        request: CreateWorkflowRecipeVersionRequest,
    ) -> WorkflowRecipeDetail:
        self._validate_definition(request.definition)
        recipe = await self._require_recipe(workflow_recipe_id)
        version_number = await _next_version_number(
            self.db,
            WorkflowRecipeVersion,
            WorkflowRecipeVersion.workflow_recipe_id,
            workflow_recipe_id,
        )
        version = WorkflowRecipeVersion(
            id=str(uuid.uuid4()),
            workflow_recipe_id=workflow_recipe_id,
            version_number=version_number,
            definition_json=_dump_json(request.definition),
            source_iteration_id=request.source_iteration_id,
            change_summary=request.change_summary,
        )
        recipe.current_version_id = version.id
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(recipe)
        await self.db.refresh(version)
        return self._to_detail(recipe, version)

    async def _require_recipe(self, workflow_recipe_id: str) -> WorkflowRecipe:
        recipe = await self.db.get(WorkflowRecipe, workflow_recipe_id)
        if recipe is None:
            raise WorkflowAssetNotFoundError('WORKFLOW_RECIPE_NOT_FOUND')
        return recipe

    async def _get_current_version(self, version_id: str | None) -> WorkflowRecipeVersion | None:
        if not version_id:
            return None
        return await self.db.get(WorkflowRecipeVersion, version_id)

    async def _load_current_versions(self, version_ids: set[str]) -> dict[str, WorkflowRecipeVersion]:
        if not version_ids:
            return {}
        result = await self.db.execute(select(WorkflowRecipeVersion).where(WorkflowRecipeVersion.id.in_(version_ids)))
        return {item.id: item for item in result.scalars().all()}

    def _validate_definition(self, definition: dict[str, Any]) -> None:
        steps = definition.get('steps')
        if steps is None:
            return
        if not isinstance(steps, list):
            raise WorkflowAssetValidationError(
                'WORKFLOW_RECIPE_DEFINITION_INVALID',
                'workflow recipe steps must be a list',
            )
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise WorkflowAssetValidationError(
                    'WORKFLOW_RECIPE_DEFINITION_INVALID',
                    f'workflow recipe step {index} must be an object',
                )
            mode = step.get('mode')
            if mode not in ALLOWED_RECIPE_STEP_MODES:
                raise WorkflowAssetValidationError(
                    'WORKFLOW_RECIPE_DEFINITION_INVALID',
                    f'workflow recipe step {index} has invalid mode',
                )

    def _to_summary(
        self,
        recipe: WorkflowRecipe,
        current_version: WorkflowRecipeVersion | None,
    ) -> WorkflowRecipeSummary:
        return WorkflowRecipeSummary(
            id=recipe.id,
            name=recipe.name,
            description=recipe.description,
            domain_hint=recipe.domain_hint,
            current_version=self._to_version_summary(current_version),
            updated_at=recipe.updated_at,
        )

    def _to_detail(
        self,
        recipe: WorkflowRecipe,
        current_version: WorkflowRecipeVersion | None,
    ) -> WorkflowRecipeDetail:
        summary = self._to_summary(recipe, current_version)
        return WorkflowRecipeDetail(
            id=summary.id,
            name=summary.name,
            description=summary.description,
            domain_hint=summary.domain_hint,
            current_version=self._to_version_detail(current_version),
            updated_at=summary.updated_at,
            created_at=recipe.created_at,
            archived_at=recipe.archived_at,
        )

    def _to_version_summary(self, version: WorkflowRecipeVersion | None) -> WorkflowAssetVersionSummary | None:
        if version is None:
            return None
        return WorkflowAssetVersionSummary(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
        )

    def _to_version_detail(self, version: WorkflowRecipeVersion | None) -> WorkflowRecipeVersionDetail | None:
        if version is None:
            return None
        return WorkflowRecipeVersionDetail(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
            definition=_load_json_dict(version.definition_json),
            source_iteration_id=version.source_iteration_id,
        )


class RunPresetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_run_presets(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        q: str | None = None,
        archived: bool = False,
    ) -> ListRunPresetsResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(RunPreset)
        query = query.where(RunPreset.archived_at.is_not(None) if archived else RunPreset.archived_at.is_(None))
        if q:
            search_term = f'%{q.strip()}%'
            query = query.where(
                or_(
                    RunPreset.name.ilike(search_term),
                    RunPreset.description.ilike(search_term),
                )
            )
        query = query.order_by(RunPreset.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = [self._to_summary(item) for item in result.scalars().all()]
        return ListRunPresetsResponse(items=items)

    async def create_run_preset(self, request: CreateRunPresetRequest) -> RunPresetDetail:
        await self._validate_definition(request.definition)
        preset = RunPreset(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            definition_json=_dump_json(request.definition),
        )
        self.db.add(preset)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(preset)
        return self._to_detail(preset)

    async def get_run_preset(self, run_preset_id: str) -> RunPresetDetail | None:
        preset = await self.db.get(RunPreset, run_preset_id)
        if preset is None:
            return None
        return self._to_detail(preset)

    async def update_run_preset(self, run_preset_id: str, request: UpdateRunPresetRequest) -> RunPresetDetail:
        preset = await self._require_preset(run_preset_id)
        if 'definition' in request.model_fields_set:
            await self._validate_definition(request.definition or {})
            preset.definition_json = _dump_json(request.definition or {})
        if 'name' in request.model_fields_set:
            preset.name = request.name
        if 'description' in request.model_fields_set:
            preset.description = request.description
        if 'archived_at' in request.model_fields_set:
            preset.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(preset)
        return self._to_detail(preset)

    async def _require_preset(self, run_preset_id: str) -> RunPreset:
        preset = await self.db.get(RunPreset, run_preset_id)
        if preset is None:
            raise WorkflowAssetNotFoundError('RUN_PRESET_NOT_FOUND')
        return preset

    async def _validate_definition(self, definition: dict[str, Any]) -> None:
        definition_mode = definition.get('mode')
        if definition_mode is not None and definition_mode not in ALLOWED_RECIPE_STEP_MODES:
            raise WorkflowAssetValidationError(
                'RUN_PRESET_DEFINITION_INVALID',
                'mode must be one of generate/debug/evaluate/continue',
            )

        run_settings = definition.get('run_settings', {})
        if run_settings is None:
            run_settings = {}
        if not isinstance(run_settings, dict):
            raise WorkflowAssetValidationError(
                'RUN_PRESET_DEFINITION_INVALID',
                'run_settings must be an object',
            )

        context_pack_version_ids = definition.get('context_pack_version_ids', [])
        if context_pack_version_ids is None:
            context_pack_version_ids = []
        if not isinstance(context_pack_version_ids, list) or not all(
            isinstance(item, str) for item in context_pack_version_ids
        ):
            raise WorkflowAssetValidationError(
                'RUN_PRESET_REFERENCE_INVALID',
                'context_pack_version_ids must be a list of ids',
            )

        prompt_asset_version_id = definition.get('prompt_asset_version_id')
        if prompt_asset_version_id:
            if await self.db.get(PromptAssetVersion, prompt_asset_version_id) is None:
                raise WorkflowAssetValidationError(
                    'RUN_PRESET_REFERENCE_INVALID',
                    'prompt asset version reference does not exist',
                )

        for context_pack_version_id in context_pack_version_ids:
            if await self.db.get(ContextPackVersion, context_pack_version_id) is None:
                raise WorkflowAssetValidationError(
                    'RUN_PRESET_REFERENCE_INVALID',
                    'context pack version reference does not exist',
                )

        evaluation_profile_version_id = definition.get('evaluation_profile_version_id')
        if evaluation_profile_version_id:
            if await self.db.get(EvaluationProfileVersion, evaluation_profile_version_id) is None:
                raise WorkflowAssetValidationError(
                    'RUN_PRESET_REFERENCE_INVALID',
                    'evaluation profile version reference does not exist',
                )

        workflow_recipe_version_id = definition.get('workflow_recipe_version_id')
        if workflow_recipe_version_id:
            if await self.db.get(WorkflowRecipeVersion, workflow_recipe_version_id) is None:
                raise WorkflowAssetValidationError(
                    'RUN_PRESET_REFERENCE_INVALID',
                    'workflow recipe version reference does not exist',
                )

    def _to_summary(self, preset: RunPreset) -> RunPresetSummary:
        return RunPresetSummary(
            id=preset.id,
            name=preset.name,
            description=preset.description,
            last_used_at=preset.last_used_at,
            updated_at=preset.updated_at,
        )

    def _to_detail(self, preset: RunPreset) -> RunPresetDetail:
        return RunPresetDetail(
            **self._to_summary(preset).model_dump(),
            definition=_load_json_dict(preset.definition_json),
            created_at=preset.created_at,
            archived_at=preset.archived_at,
        )
