from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_asset import PromptAsset
from app.models.prompt_asset_version import PromptAssetVersion
from app.models.prompt_category import PromptCategory
from app.schemas.prompt_asset import (
    CreatePromptAssetRequest,
    CreatePromptAssetVersionRequest,
    CreatePromptCategoryRequest,
    ListPromptAssetsResponse,
    ListPromptAssetVersionsResponse,
    ListPromptCategoryTreeResponse,
    PromptAssetDetail,
    PromptAssetSummary,
    PromptAssetVersionDetail,
    PromptAssetVersionSummary,
    PromptCategoryTreeItem,
    UpdatePromptAssetRequest,
    UpdatePromptCategoryRequest,
)

MAX_PAGE_SIZE = 200


class PromptAssetNotFoundError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


class PromptAssetValidationError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


def _normalize_page(page: int, page_size: int) -> tuple[int, int]:
    safe_page = max(page, 1)
    safe_page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    return safe_page, safe_page_size


def _dump_json(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load_json_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


async def _next_asset_version_number(db: AsyncSession, asset_id: str) -> int:
    result = await db.execute(
        select(func.max(PromptAssetVersion.version_number)).where(PromptAssetVersion.asset_id == asset_id)
    )
    return (result.scalar_one_or_none() or 0) + 1


class PromptCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tree(self) -> ListPromptCategoryTreeResponse:
        categories = await self._load_all_categories()
        return ListPromptCategoryTreeResponse(items=self._build_tree(categories))

    async def create_category(self, request: CreatePromptCategoryRequest) -> PromptCategoryTreeItem:
        parent = await self._require_parent(request.parent_id)
        category = PromptCategory(
            id=str(uuid.uuid4()),
            parent_id=parent.id if parent else None,
            name=request.name.strip(),
            path=self._build_path(request.name.strip(), parent),
            depth=(parent.depth + 1) if parent else 0,
            sort_order=request.sort_order,
        )
        self.db.add(category)
        await self.db.commit()
        return await self._get_tree_item(category.id)

    async def update_category(
        self,
        category_id: str,
        request: UpdatePromptCategoryRequest,
    ) -> PromptCategoryTreeItem:
        category = await self._require_category(category_id)

        if 'name' in request.model_fields_set and request.name is not None:
            category.name = request.name.strip()

        if 'sort_order' in request.model_fields_set and request.sort_order is not None:
            category.sort_order = request.sort_order

        if 'parent_id' in request.model_fields_set:
            parent = await self._require_parent(request.parent_id)
            if parent and parent.id == category.id:
                raise PromptAssetValidationError('PROMPT_CATEGORY_INVALID_PARENT', 'category cannot parent itself')
            if parent:
                await self._ensure_not_descendant(category, parent.id)
            category.parent_id = parent.id if parent else None

        await self._refresh_subtree(category.id)
        await self.db.commit()
        return await self._get_tree_item(category.id)

    async def delete_category(self, category_id: str) -> None:
        category = await self._require_category(category_id)

        child_exists = await self.db.execute(
            select(PromptCategory.id).where(PromptCategory.parent_id == category.id).limit(1)
        )
        if child_exists.scalar_one_or_none():
            raise PromptAssetValidationError('PROMPT_CATEGORY_NOT_EMPTY', 'category still has child groups')

        asset_exists = await self.db.execute(
            select(PromptAsset.id)
            .where(PromptAsset.category_id == category.id, PromptAsset.archived_at.is_(None))
            .limit(1)
        )
        if asset_exists.scalar_one_or_none():
            raise PromptAssetValidationError('PROMPT_CATEGORY_NOT_EMPTY', 'category still has prompts')

        await self.db.delete(category)
        await self.db.commit()

    async def _require_category(self, category_id: str) -> PromptCategory:
        category = await self.db.get(PromptCategory, category_id)
        if category is None:
            raise PromptAssetNotFoundError('PROMPT_CATEGORY_NOT_FOUND')
        return category

    async def _require_parent(self, parent_id: str | None) -> PromptCategory | None:
        if not parent_id:
            return None
        return await self._require_category(parent_id)

    async def _ensure_not_descendant(self, category: PromptCategory, candidate_parent_id: str) -> None:
        current = await self.db.get(PromptCategory, candidate_parent_id)
        while current is not None:
            if current.id == category.id:
                raise PromptAssetValidationError(
                    'PROMPT_CATEGORY_INVALID_PARENT',
                    'category cannot move inside its own subtree',
                )
            if not current.parent_id:
                return
            current = await self.db.get(PromptCategory, current.parent_id)

    async def _refresh_subtree(self, root_id: str) -> None:
        categories = await self._load_all_categories()
        by_id = {item.id: item for item in categories}
        children_by_parent: dict[str | None, list[PromptCategory]] = defaultdict(list)
        for item in categories:
            children_by_parent[item.parent_id].append(item)
        for siblings in children_by_parent.values():
            siblings.sort(key=lambda item: (item.sort_order, item.name.lower()))

        root = by_id[root_id]
        parent = by_id.get(root.parent_id)

        def assign(node: PromptCategory, parent_node: PromptCategory | None) -> None:
            node.depth = (parent_node.depth + 1) if parent_node else 0
            node.path = self._build_path(node.name, parent_node)
            for child in children_by_parent.get(node.id, []):
                assign(child, node)

        assign(root, parent)

    async def _get_tree_item(self, category_id: str) -> PromptCategoryTreeItem:
        categories = await self._load_all_categories()
        tree = self._build_tree(categories)
        found = self._find_tree_item(tree, category_id)
        if found is None:
            raise PromptAssetNotFoundError('PROMPT_CATEGORY_NOT_FOUND')
        return found

    async def _load_all_categories(self) -> list[PromptCategory]:
        result = await self.db.execute(
            select(PromptCategory).order_by(PromptCategory.depth.asc(), PromptCategory.sort_order.asc(), PromptCategory.name.asc())
        )
        return list(result.scalars().all())

    def _build_path(self, name: str, parent: PromptCategory | None) -> str:
        cleaned = name.strip()
        if parent is None or not parent.path:
            return cleaned
        return f'{parent.path}/{cleaned}'

    def _build_tree(self, categories: list[PromptCategory]) -> list[PromptCategoryTreeItem]:
        items_by_id = {
            item.id: PromptCategoryTreeItem(
                id=item.id,
                name=item.name,
                path=item.path,
                depth=item.depth,
                sort_order=item.sort_order,
            )
            for item in categories
        }
        roots: list[PromptCategoryTreeItem] = []
        for item in categories:
            tree_item = items_by_id[item.id]
            if item.parent_id and item.parent_id in items_by_id:
                items_by_id[item.parent_id].children.append(tree_item)
            else:
                roots.append(tree_item)
        return roots

    def _find_tree_item(
        self,
        items: list[PromptCategoryTreeItem],
        category_id: str,
    ) -> PromptCategoryTreeItem | None:
        for item in items:
            if item.id == category_id:
                return item
            found = self._find_tree_item(item.children, category_id)
            if found is not None:
                return found
        return None


class PromptAssetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_prompt_assets(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        q: str | None = None,
        category_id: str | None = None,
        favorites_only: bool = False,
        archived: bool = False,
    ) -> ListPromptAssetsResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(PromptAsset)
        query = query.where(PromptAsset.archived_at.is_not(None) if archived else PromptAsset.archived_at.is_(None))

        if category_id:
            query = query.where(PromptAsset.category_id == category_id)
        if favorites_only:
            query = query.where(PromptAsset.is_favorite.is_(True))
        if q:
            search_term = f'%{q.strip()}%'
            query = query.where(
                or_(
                    PromptAsset.name.ilike(search_term),
                    PromptAsset.description.ilike(search_term),
                )
            )

        query = query.order_by(PromptAsset.is_favorite.desc(), PromptAsset.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        assets = list(result.scalars().all())
        version_map = await self._load_current_versions({item.current_version_id for item in assets if item.current_version_id})
        return ListPromptAssetsResponse(items=[self._to_summary(item, version_map.get(item.current_version_id)) for item in assets])

    async def create_prompt_asset(self, request: CreatePromptAssetRequest) -> PromptAssetDetail:
        if request.category_id:
            await self._require_category(request.category_id)

        asset = PromptAsset(
            id=str(uuid.uuid4()),
            category_id=request.category_id,
            name=request.name.strip(),
            description=request.description,
            is_favorite=False,
            tags_json=_dump_json(request.tags),
        )
        version = PromptAssetVersion(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            version_number=1,
            content=request.content,
            source_iteration_id=request.source_iteration_id,
            source_asset_version_id=None,
            change_summary=request.change_summary,
        )
        asset.current_version_id = version.id
        self.db.add(asset)
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        return await self.get_prompt_asset(asset.id)

    async def get_prompt_asset(self, asset_id: str) -> PromptAssetDetail:
        asset = await self._require_asset(asset_id)
        version = await self._get_current_version(asset.current_version_id)
        return self._to_detail(asset, version)

    async def update_prompt_asset(
        self,
        asset_id: str,
        request: UpdatePromptAssetRequest,
    ) -> PromptAssetDetail:
        asset = await self._require_asset(asset_id)

        if 'category_id' in request.model_fields_set:
            if request.category_id:
                await self._require_category(request.category_id)
            asset.category_id = request.category_id
        if 'name' in request.model_fields_set and request.name is not None:
            asset.name = request.name.strip()
        if 'description' in request.model_fields_set:
            asset.description = request.description
        if 'is_favorite' in request.model_fields_set and request.is_favorite is not None:
            asset.is_favorite = request.is_favorite
        if 'tags' in request.model_fields_set and request.tags is not None:
            asset.tags_json = _dump_json(request.tags)
        if 'archived_at' in request.model_fields_set:
            asset.archived_at = request.archived_at

        await self.db.commit()
        return await self.get_prompt_asset(asset.id)

    async def archive_prompt_asset(self, asset_id: str) -> None:
        asset = await self._require_asset(asset_id)
        asset.archived_at = datetime.utcnow()
        await self.db.commit()

    async def list_versions(self, asset_id: str) -> ListPromptAssetVersionsResponse:
        await self._require_asset(asset_id)
        result = await self.db.execute(
            select(PromptAssetVersion)
            .where(PromptAssetVersion.asset_id == asset_id)
            .order_by(PromptAssetVersion.version_number.desc())
        )
        items = [self._to_version_summary(item) for item in result.scalars().all()]
        return ListPromptAssetVersionsResponse(items=items)

    async def create_version(
        self,
        asset_id: str,
        request: CreatePromptAssetVersionRequest,
    ) -> PromptAssetDetail:
        asset = await self._require_asset(asset_id)
        if request.source_asset_version_id:
            await self._require_version(request.source_asset_version_id)

        version = PromptAssetVersion(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            version_number=await _next_asset_version_number(self.db, asset_id),
            content=request.content,
            source_iteration_id=request.source_iteration_id,
            source_asset_version_id=request.source_asset_version_id,
            change_summary=request.change_summary,
        )
        asset.current_version_id = version.id
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        return await self.get_prompt_asset(asset_id)

    async def _require_asset(self, asset_id: str) -> PromptAsset:
        asset = await self.db.get(PromptAsset, asset_id)
        if asset is None:
            raise PromptAssetNotFoundError('PROMPT_ASSET_NOT_FOUND')
        return asset

    async def _require_version(self, version_id: str) -> PromptAssetVersion:
        version = await self.db.get(PromptAssetVersion, version_id)
        if version is None:
            raise PromptAssetNotFoundError('PROMPT_ASSET_VERSION_NOT_FOUND')
        return version

    async def _require_category(self, category_id: str) -> PromptCategory:
        category = await self.db.get(PromptCategory, category_id)
        if category is None:
            raise PromptAssetNotFoundError('PROMPT_CATEGORY_NOT_FOUND')
        return category

    async def _get_current_version(self, version_id: str | None) -> PromptAssetVersion | None:
        if not version_id:
            return None
        return await self.db.get(PromptAssetVersion, version_id)

    async def _load_current_versions(self, version_ids: set[str]) -> dict[str, PromptAssetVersion]:
        if not version_ids:
            return {}
        result = await self.db.execute(select(PromptAssetVersion).where(PromptAssetVersion.id.in_(version_ids)))
        return {item.id: item for item in result.scalars().all()}

    def _to_summary(
        self,
        asset: PromptAsset,
        current_version: PromptAssetVersion | None,
    ) -> PromptAssetSummary:
        return PromptAssetSummary(
            id=asset.id,
            category_id=asset.category_id,
            name=asset.name,
            description=asset.description,
            is_favorite=asset.is_favorite,
            tags=_load_json_list(asset.tags_json),
            current_version=self._to_version_summary(current_version),
            updated_at=asset.updated_at,
        )

    def _to_detail(
        self,
        asset: PromptAsset,
        current_version: PromptAssetVersion | None,
    ) -> PromptAssetDetail:
        return PromptAssetDetail(
            id=asset.id,
            category_id=asset.category_id,
            name=asset.name,
            description=asset.description,
            is_favorite=asset.is_favorite,
            tags=_load_json_list(asset.tags_json),
            current_version=self._to_version_detail(current_version),
            updated_at=asset.updated_at,
            created_at=asset.created_at,
            archived_at=asset.archived_at,
        )

    def _to_version_summary(self, version: PromptAssetVersion | None) -> PromptAssetVersionSummary | None:
        if version is None:
            return None
        return PromptAssetVersionSummary(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
        )

    def _to_version_detail(self, version: PromptAssetVersion | None) -> PromptAssetVersionDetail | None:
        if version is None:
            return None
        return PromptAssetVersionDetail(
            id=version.id,
            version_number=version.version_number,
            change_summary=version.change_summary,
            created_at=version.created_at,
            content=version.content,
            source_iteration_id=version.source_iteration_id,
            source_asset_version_id=version.source_asset_version_id,
        )
