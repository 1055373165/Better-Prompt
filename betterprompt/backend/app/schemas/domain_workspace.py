from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DomainWorkspaceSummary(BaseModel):
    id: str
    workspace_type: str
    name: str
    description: str | None = None
    status: str
    updated_at: datetime


class DomainWorkspaceDetail(DomainWorkspaceSummary):
    config: dict[str, Any] = Field(default_factory=dict)
    subject_count: int = 0
    source_count: int = 0
    report_count: int = 0
    created_at: datetime
    archived_at: datetime | None = None


class ListDomainWorkspacesResponse(BaseModel):
    items: list[DomainWorkspaceSummary] = Field(default_factory=list)


class CreateDomainWorkspaceRequest(BaseModel):
    workspace_type: str = Field(..., min_length=1, max_length=80)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class UpdateDomainWorkspaceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=40)
    config: dict[str, Any] | None = None
    archived_at: datetime | None = None


class WorkspaceSubjectSummary(BaseModel):
    id: str
    workspace_id: str
    subject_type: str
    external_key: str | None = None
    display_name: str
    status: str
    updated_at: datetime


class WorkspaceSubjectDetail(WorkspaceSubjectSummary):
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ListWorkspaceSubjectsResponse(BaseModel):
    items: list[WorkspaceSubjectSummary] = Field(default_factory=list)


class CreateWorkspaceSubjectRequest(BaseModel):
    subject_type: str = Field(..., min_length=1, max_length=80)
    external_key: str | None = Field(default=None, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateWorkspaceSubjectRequest(BaseModel):
    external_key: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    metadata: dict[str, Any] | None = None
    status: str | None = Field(default=None, min_length=1, max_length=40)


class ResearchSourceSummary(BaseModel):
    id: str
    workspace_id: str
    subject_id: str | None = None
    source_type: str
    canonical_uri: str | None = None
    title: str | None = None
    source_timestamp: datetime | None = None
    ingest_status: str
    updated_at: datetime


class ResearchSourceDetail(ResearchSourceSummary):
    content: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ListResearchSourcesResponse(BaseModel):
    items: list[ResearchSourceSummary] = Field(default_factory=list)


class CreateResearchSourceRequest(BaseModel):
    subject_id: str | None = None
    source_type: str = Field(..., min_length=1, max_length=40)
    canonical_uri: str | None = Field(default=None, max_length=2048)
    title: str | None = Field(default=None, max_length=255)
    content: dict[str, Any] = Field(default_factory=dict)
    source_timestamp: datetime | None = None


class UpdateResearchSourceRequest(BaseModel):
    subject_id: str | None = None
    canonical_uri: str | None = Field(default=None, max_length=2048)
    title: str | None = Field(default=None, max_length=255)
    content: dict[str, Any] | None = None
    source_timestamp: datetime | None = None
    ingest_status: str | None = Field(default=None, min_length=1, max_length=40)


class ResearchReportVersionSummary(BaseModel):
    id: str
    version_number: int
    summary_text: str | None = None
    confidence_score: float | None = None
    created_at: datetime


class ResearchReportVersionDetail(ResearchReportVersionSummary):
    content: dict[str, Any] = Field(default_factory=dict)
    source_session_id: str | None = None
    source_iteration_id: str | None = None


class ResearchReportSummary(BaseModel):
    id: str
    workspace_id: str
    subject_id: str | None = None
    report_type: str
    title: str
    status: str
    latest_version: ResearchReportVersionSummary | None = None
    updated_at: datetime


class ResearchReportDetail(ResearchReportSummary):
    latest_version: ResearchReportVersionDetail | None = None
    created_at: datetime
    archived_at: datetime | None = None


class ListResearchReportsResponse(BaseModel):
    items: list[ResearchReportSummary] = Field(default_factory=list)


class ListResearchReportVersionsResponse(BaseModel):
    items: list[ResearchReportVersionDetail] = Field(default_factory=list)


class CreateResearchReportRequest(BaseModel):
    subject_id: str | None = None
    report_type: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=255)
    content: dict[str, Any] = Field(default_factory=dict)
    source_session_id: str | None = None
    source_iteration_id: str | None = None
    summary_text: str | None = None
    confidence_score: float | None = None


class UpdateResearchReportRequest(BaseModel):
    subject_id: str | None = None
    report_type: str | None = Field(default=None, min_length=1, max_length=80)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=40)
    archived_at: datetime | None = None


class CreateResearchReportVersionRequest(BaseModel):
    content: dict[str, Any] = Field(default_factory=dict)
    source_session_id: str | None = None
    source_iteration_id: str | None = None
    summary_text: str | None = None
    confidence_score: float | None = None
