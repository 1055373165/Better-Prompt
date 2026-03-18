from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowAssetVersionSummary(BaseModel):
    id: str
    version_number: int
    change_summary: str | None = None
    created_at: datetime


class ContextPackSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    current_version: WorkflowAssetVersionSummary | None = None
    updated_at: datetime


class ContextPackDetail(ContextPackSummary):
    created_at: datetime
    archived_at: datetime | None = None


class ListContextPacksResponse(BaseModel):
    items: list[ContextPackSummary] = Field(default_factory=list)


class CreateContextPackRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    source_iteration_id: str | None = None
    change_summary: str | None = None


class UpdateContextPackRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = None
    archived_at: datetime | None = None


class CreateContextPackVersionRequest(BaseModel):
    payload: dict[str, object] = Field(default_factory=dict)
    source_iteration_id: str | None = None
    change_summary: str | None = None


class ListContextPackVersionsResponse(BaseModel):
    items: list[WorkflowAssetVersionSummary] = Field(default_factory=list)


class EvaluationProfileSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    current_version: WorkflowAssetVersionSummary | None = None
    updated_at: datetime


class EvaluationProfileDetail(EvaluationProfileSummary):
    created_at: datetime
    archived_at: datetime | None = None


class ListEvaluationProfilesResponse(BaseModel):
    items: list[EvaluationProfileSummary] = Field(default_factory=list)


class CreateEvaluationProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    rules: dict[str, object] = Field(default_factory=dict)
    change_summary: str | None = None


class UpdateEvaluationProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    archived_at: datetime | None = None


class CreateEvaluationProfileVersionRequest(BaseModel):
    rules: dict[str, object] = Field(default_factory=dict)
    change_summary: str | None = None


class ListEvaluationProfileVersionsResponse(BaseModel):
    items: list[WorkflowAssetVersionSummary] = Field(default_factory=list)


class WorkflowRecipeSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    domain_hint: str | None = None
    current_version: WorkflowAssetVersionSummary | None = None
    updated_at: datetime


class WorkflowRecipeDetail(WorkflowRecipeSummary):
    created_at: datetime
    archived_at: datetime | None = None


class ListWorkflowRecipesResponse(BaseModel):
    items: list[WorkflowRecipeSummary] = Field(default_factory=list)


class CreateWorkflowRecipeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    domain_hint: str | None = Field(default=None, max_length=80)
    definition: dict[str, object] = Field(default_factory=dict)
    source_iteration_id: str | None = None
    change_summary: str | None = None


class UpdateWorkflowRecipeRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    domain_hint: str | None = Field(default=None, max_length=80)
    archived_at: datetime | None = None


class CreateWorkflowRecipeVersionRequest(BaseModel):
    definition: dict[str, object] = Field(default_factory=dict)
    source_iteration_id: str | None = None
    change_summary: str | None = None


class ListWorkflowRecipeVersionsResponse(BaseModel):
    items: list[WorkflowAssetVersionSummary] = Field(default_factory=list)


class RunPresetSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    last_used_at: datetime | None = None
    updated_at: datetime


class RunPresetDetail(RunPresetSummary):
    definition: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    archived_at: datetime | None = None


class ListRunPresetsResponse(BaseModel):
    items: list[RunPresetSummary] = Field(default_factory=list)


class CreateRunPresetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    definition: dict[str, object] = Field(default_factory=dict)


class UpdateRunPresetRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    definition: dict[str, object] | None = None
    archived_at: datetime | None = None
