from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PromptCategoryTreeItem(BaseModel):
    id: str
    name: str
    path: str
    depth: int
    sort_order: int
    children: list['PromptCategoryTreeItem'] = Field(default_factory=list)


class CreatePromptCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    parent_id: str | None = None
    sort_order: int = 0


class UpdatePromptCategoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_id: str | None = None
    sort_order: int | None = None


class PromptAssetVersionSummary(BaseModel):
    id: str
    version_number: int
    change_summary: str | None = None
    created_at: datetime


class PromptAssetVersionDetail(PromptAssetVersionSummary):
    content: str
    source_iteration_id: str | None = None
    source_asset_version_id: str | None = None


class PromptAssetSummary(BaseModel):
    id: str
    category_id: str | None = None
    name: str
    description: str | None = None
    is_favorite: bool
    tags: list[str] = Field(default_factory=list)
    current_version: PromptAssetVersionSummary | None = None
    updated_at: datetime


class PromptAssetDetail(BaseModel):
    id: str
    category_id: str | None = None
    name: str
    description: str | None = None
    is_favorite: bool
    tags: list[str] = Field(default_factory=list)
    current_version: PromptAssetVersionDetail | None = None
    updated_at: datetime
    created_at: datetime
    archived_at: datetime | None = None


class ListPromptAssetsResponse(BaseModel):
    items: list[PromptAssetSummary] = Field(default_factory=list)


class ListPromptCategoryTreeResponse(BaseModel):
    items: list[PromptCategoryTreeItem] = Field(default_factory=list)


class CreatePromptAssetRequest(BaseModel):
    category_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    source_iteration_id: str | None = None
    change_summary: str | None = None


class UpdatePromptAssetRequest(BaseModel):
    category_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_favorite: bool | None = None
    tags: list[str] | None = None
    archived_at: datetime | None = None


class CreatePromptAssetVersionRequest(BaseModel):
    content: str = Field(..., min_length=1)
    source_iteration_id: str | None = None
    source_asset_version_id: str | None = None
    change_summary: str | None = None


class ListPromptAssetVersionsResponse(BaseModel):
    items: list[PromptAssetVersionSummary] = Field(default_factory=list)
