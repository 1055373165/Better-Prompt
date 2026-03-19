from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context_pack import ContextPack
from app.models.domain_workspace import DomainWorkspace
from app.models.evaluation_profile import EvaluationProfile
from app.models.prompt_iteration import PromptIteration
from app.models.prompt_session import PromptSession
from app.models.research_report import ResearchReport
from app.models.research_report_version import ResearchReportVersion
from app.models.research_source import ResearchSource
from app.models.run_preset import RunPreset
from app.models.workflow_recipe_version import WorkflowRecipeVersion
from app.models.workspace_subject import WorkspaceSubject
from app.schemas.domain_workspace import (
    CreateDomainWorkspaceRequest,
    CreateResearchReportRequest,
    CreateResearchReportVersionRequest,
    CreateResearchSourceRequest,
    CreateWorkspaceSubjectRequest,
    DomainWorkspaceDetail,
    DomainWorkspaceSummary,
    ListDomainWorkspacesResponse,
    ListResearchReportsResponse,
    ListResearchReportVersionsResponse,
    ListResearchSourcesResponse,
    ListWorkspaceSubjectsResponse,
    ResearchReportDetail,
    ResearchReportSummary,
    ResearchReportVersionDetail,
    ResearchReportVersionSummary,
    ResearchSourceDetail,
    ResearchSourceSummary,
    UpdateDomainWorkspaceRequest,
    UpdateResearchReportRequest,
    UpdateResearchSourceRequest,
    UpdateWorkspaceSubjectRequest,
    WorkspaceSubjectDetail,
    WorkspaceSubjectSummary,
)


MAX_PAGE_SIZE = 100


class DomainWorkspaceNotFoundError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


class DomainWorkspaceValidationError(Exception):
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


async def _count_rows(db: AsyncSession, model, *conditions) -> int:
    query = select(func.count()).select_from(model)
    if conditions:
        query = query.where(*conditions)
    result = await db.execute(query)
    return int(result.scalar_one() or 0)


async def _next_report_version_number(db: AsyncSession, report_id: str) -> int:
    result = await db.execute(
        select(func.max(ResearchReportVersion.version_number))
        .where(ResearchReportVersion.report_id == report_id)
    )
    return int(result.scalar_one_or_none() or 0) + 1


class DomainWorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_workspaces(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        workspace_type: str | None = None,
        archived: bool = False,
    ) -> ListDomainWorkspacesResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(DomainWorkspace)
        query = query.where(
            DomainWorkspace.archived_at.is_not(None) if archived else DomainWorkspace.archived_at.is_(None)
        )
        if workspace_type:
            query = query.where(DomainWorkspace.workspace_type == workspace_type)
        query = query.order_by(DomainWorkspace.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = [self._to_summary(item) for item in result.scalars().all()]
        return ListDomainWorkspacesResponse(items=items)

    async def create_workspace(self, request: CreateDomainWorkspaceRequest) -> DomainWorkspaceDetail:
        await self._validate_config(request.config)
        workspace = DomainWorkspace(
            id=str(uuid.uuid4()),
            workspace_type=request.workspace_type,
            name=request.name,
            description=request.description,
            status='active',
            config_json=_dump_json(request.config),
        )
        self.db.add(workspace)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(workspace)
        return await self._to_detail(workspace)

    async def get_workspace(self, workspace_id: str) -> DomainWorkspaceDetail | None:
        workspace = await self.db.get(DomainWorkspace, workspace_id)
        if workspace is None:
            return None
        return await self._to_detail(workspace)

    async def update_workspace(
        self,
        workspace_id: str,
        request: UpdateDomainWorkspaceRequest,
    ) -> DomainWorkspaceDetail:
        workspace = await self._require_workspace(workspace_id)
        if 'config' in request.model_fields_set:
            await self._validate_config(request.config or {})
            workspace.config_json = _dump_json(request.config or {})
        if 'name' in request.model_fields_set:
            workspace.name = request.name
        if 'description' in request.model_fields_set:
            workspace.description = request.description
        if 'status' in request.model_fields_set:
            workspace.status = request.status
        if 'archived_at' in request.model_fields_set:
            workspace.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(workspace)
        return await self._to_detail(workspace)

    async def _require_workspace(self, workspace_id: str) -> DomainWorkspace:
        workspace = await self.db.get(DomainWorkspace, workspace_id)
        if workspace is None:
            raise DomainWorkspaceNotFoundError('DOMAIN_WORKSPACE_NOT_FOUND')
        return workspace

    async def _validate_config(self, config: dict[str, Any]) -> None:
        default_run_preset_id = config.get('default_run_preset_id')
        if default_run_preset_id and await self.db.get(RunPreset, default_run_preset_id) is None:
            raise DomainWorkspaceValidationError(
                'DOMAIN_WORKSPACE_CONFIG_INVALID',
                'default run preset does not exist',
            )

        default_recipe_version_id = config.get('default_recipe_version_id')
        if default_recipe_version_id and await self.db.get(WorkflowRecipeVersion, default_recipe_version_id) is None:
            raise DomainWorkspaceValidationError(
                'DOMAIN_WORKSPACE_CONFIG_INVALID',
                'default workflow recipe version does not exist',
            )

        default_context_pack_ids = config.get('default_context_pack_ids', [])
        if default_context_pack_ids is None:
            default_context_pack_ids = []
        if not isinstance(default_context_pack_ids, list) or not all(
            isinstance(item, str) for item in default_context_pack_ids
        ):
            raise DomainWorkspaceValidationError(
                'DOMAIN_WORKSPACE_CONFIG_INVALID',
                'default_context_pack_ids must be a list of ids',
            )
        for context_pack_id in default_context_pack_ids:
            if await self.db.get(ContextPack, context_pack_id) is None:
                raise DomainWorkspaceValidationError(
                    'DOMAIN_WORKSPACE_CONFIG_INVALID',
                    'default context pack does not exist',
                )

        default_evaluation_profile_id = config.get('default_evaluation_profile_id')
        if default_evaluation_profile_id and await self.db.get(
            EvaluationProfile,
            default_evaluation_profile_id,
        ) is None:
            raise DomainWorkspaceValidationError(
                'DOMAIN_WORKSPACE_CONFIG_INVALID',
                'default evaluation profile does not exist',
            )

    def _to_summary(self, workspace: DomainWorkspace) -> DomainWorkspaceSummary:
        return DomainWorkspaceSummary(
            id=workspace.id,
            workspace_type=workspace.workspace_type,
            name=workspace.name,
            description=workspace.description,
            status=workspace.status,
            updated_at=workspace.updated_at,
        )

    async def _to_detail(self, workspace: DomainWorkspace) -> DomainWorkspaceDetail:
        subject_count = await _count_rows(
            self.db,
            WorkspaceSubject,
            WorkspaceSubject.workspace_id == workspace.id,
        )
        source_count = await _count_rows(
            self.db,
            ResearchSource,
            ResearchSource.workspace_id == workspace.id,
        )
        report_count = await _count_rows(
            self.db,
            ResearchReport,
            ResearchReport.workspace_id == workspace.id,
        )
        return DomainWorkspaceDetail(
            **self._to_summary(workspace).model_dump(),
            config=_load_json_dict(workspace.config_json),
            subject_count=subject_count,
            source_count=source_count,
            report_count=report_count,
            created_at=workspace.created_at,
            archived_at=workspace.archived_at,
        )


class WorkspaceSubjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_subjects(
        self,
        workspace_id: str,
        *,
        subject_type: str | None = None,
        q: str | None = None,
    ) -> ListWorkspaceSubjectsResponse:
        await self._require_workspace(workspace_id)
        query = select(WorkspaceSubject).where(WorkspaceSubject.workspace_id == workspace_id)
        if subject_type:
            query = query.where(WorkspaceSubject.subject_type == subject_type)
        if q:
            search_term = f'%{q.strip()}%'
            query = query.where(
                or_(
                    WorkspaceSubject.display_name.ilike(search_term),
                    WorkspaceSubject.external_key.ilike(search_term),
                )
            )
        result = await self.db.execute(query.order_by(WorkspaceSubject.updated_at.desc()))
        items = [self._to_detail(item) for item in result.scalars().all()]
        return ListWorkspaceSubjectsResponse(items=items)

    async def create_subject(
        self,
        workspace_id: str,
        request: CreateWorkspaceSubjectRequest,
    ) -> WorkspaceSubjectDetail:
        await self._require_workspace(workspace_id)
        await self._ensure_external_key_available(
            workspace_id,
            request.subject_type,
            request.external_key,
        )
        subject = WorkspaceSubject(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            subject_type=request.subject_type,
            external_key=request.external_key,
            display_name=request.display_name,
            metadata_json=_dump_json(request.metadata),
            status='active',
        )
        self.db.add(subject)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(subject)
        return self._to_detail(subject)

    async def get_subject(self, subject_id: str) -> WorkspaceSubjectDetail | None:
        subject = await self.db.get(WorkspaceSubject, subject_id)
        if subject is None:
            return None
        return self._to_detail(subject)

    async def update_subject(
        self,
        subject_id: str,
        request: UpdateWorkspaceSubjectRequest,
    ) -> WorkspaceSubjectDetail:
        subject = await self._require_subject(subject_id)
        if 'external_key' in request.model_fields_set:
            await self._ensure_external_key_available(
                subject.workspace_id,
                subject.subject_type,
                request.external_key,
                exclude_subject_id=subject.id,
            )
            subject.external_key = request.external_key
        if 'display_name' in request.model_fields_set:
            subject.display_name = request.display_name
        if 'metadata' in request.model_fields_set:
            subject.metadata_json = _dump_json(request.metadata or {})
        if 'status' in request.model_fields_set:
            subject.status = request.status

        await self.db.commit()
        await self.db.refresh(subject)
        return self._to_detail(subject)

    async def _require_workspace(self, workspace_id: str) -> DomainWorkspace:
        workspace = await self.db.get(DomainWorkspace, workspace_id)
        if workspace is None:
            raise DomainWorkspaceNotFoundError('DOMAIN_WORKSPACE_NOT_FOUND')
        return workspace

    async def _require_subject(self, subject_id: str) -> WorkspaceSubject:
        subject = await self.db.get(WorkspaceSubject, subject_id)
        if subject is None:
            raise DomainWorkspaceNotFoundError('WORKSPACE_SUBJECT_NOT_FOUND')
        return subject

    async def _ensure_external_key_available(
        self,
        workspace_id: str,
        subject_type: str,
        external_key: str | None,
        *,
        exclude_subject_id: str | None = None,
    ) -> None:
        if not external_key:
            return
        query = select(WorkspaceSubject).where(
            WorkspaceSubject.workspace_id == workspace_id,
            WorkspaceSubject.subject_type == subject_type,
            WorkspaceSubject.external_key == external_key,
        )
        if exclude_subject_id:
            query = query.where(WorkspaceSubject.id != exclude_subject_id)
        result = await self.db.execute(query.limit(1))
        if result.scalar_one_or_none() is not None:
            raise DomainWorkspaceValidationError(
                'WORKSPACE_SUBJECT_INVALID',
                'external_key already exists for this workspace subject type',
            )

    def _to_summary(self, subject: WorkspaceSubject) -> WorkspaceSubjectSummary:
        return WorkspaceSubjectSummary(
            id=subject.id,
            workspace_id=subject.workspace_id,
            subject_type=subject.subject_type,
            external_key=subject.external_key,
            display_name=subject.display_name,
            status=subject.status,
            updated_at=subject.updated_at,
        )

    def _to_detail(self, subject: WorkspaceSubject) -> WorkspaceSubjectDetail:
        return WorkspaceSubjectDetail(
            **self._to_summary(subject).model_dump(),
            metadata=_load_json_dict(subject.metadata_json),
            created_at=subject.created_at,
        )


class ResearchSourceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sources(
        self,
        workspace_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        subject_id: str | None = None,
        source_type: str | None = None,
    ) -> ListResearchSourcesResponse:
        await self._require_workspace(workspace_id)
        page, page_size = _normalize_page(page, page_size)
        query = select(ResearchSource).where(ResearchSource.workspace_id == workspace_id)
        if subject_id:
            query = query.where(ResearchSource.subject_id == subject_id)
        if source_type:
            query = query.where(ResearchSource.source_type == source_type)
        query = query.order_by(ResearchSource.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = [self._to_detail(item) for item in result.scalars().all()]
        return ListResearchSourcesResponse(items=items)

    async def create_source(
        self,
        workspace_id: str,
        request: CreateResearchSourceRequest,
    ) -> ResearchSourceDetail:
        await self._require_workspace(workspace_id)
        await self._validate_subject_membership(workspace_id, request.subject_id)
        source = ResearchSource(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            subject_id=request.subject_id,
            source_type=request.source_type,
            canonical_uri=request.canonical_uri,
            title=request.title,
            content_json=_dump_json(request.content),
            source_timestamp=request.source_timestamp,
            ingest_status='ready',
        )
        self.db.add(source)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(source)
        return self._to_detail(source)

    async def get_source(self, source_id: str) -> ResearchSourceDetail | None:
        source = await self.db.get(ResearchSource, source_id)
        if source is None:
            return None
        return self._to_detail(source)

    async def update_source(
        self,
        source_id: str,
        request: UpdateResearchSourceRequest,
    ) -> ResearchSourceDetail:
        source = await self._require_source(source_id)
        if 'subject_id' in request.model_fields_set:
            await self._validate_subject_membership(source.workspace_id, request.subject_id)
            source.subject_id = request.subject_id
        if 'canonical_uri' in request.model_fields_set:
            source.canonical_uri = request.canonical_uri
        if 'title' in request.model_fields_set:
            source.title = request.title
        if 'content' in request.model_fields_set:
            source.content_json = _dump_json(request.content or {})
        if 'source_timestamp' in request.model_fields_set:
            source.source_timestamp = request.source_timestamp
        if 'ingest_status' in request.model_fields_set:
            source.ingest_status = request.ingest_status

        await self.db.commit()
        await self.db.refresh(source)
        return self._to_detail(source)

    async def _require_workspace(self, workspace_id: str) -> DomainWorkspace:
        workspace = await self.db.get(DomainWorkspace, workspace_id)
        if workspace is None:
            raise DomainWorkspaceNotFoundError('DOMAIN_WORKSPACE_NOT_FOUND')
        return workspace

    async def _require_source(self, source_id: str) -> ResearchSource:
        source = await self.db.get(ResearchSource, source_id)
        if source is None:
            raise DomainWorkspaceNotFoundError('RESEARCH_SOURCE_NOT_FOUND')
        return source

    async def _validate_subject_membership(self, workspace_id: str, subject_id: str | None) -> None:
        if subject_id is None:
            return
        subject = await self.db.get(WorkspaceSubject, subject_id)
        if subject is None or subject.workspace_id != workspace_id:
            raise DomainWorkspaceValidationError(
                'WORKSPACE_SOURCE_INVALID',
                'subject does not belong to workspace',
            )

    def _to_summary(self, source: ResearchSource) -> ResearchSourceSummary:
        return ResearchSourceSummary(
            id=source.id,
            workspace_id=source.workspace_id,
            subject_id=source.subject_id,
            source_type=source.source_type,
            canonical_uri=source.canonical_uri,
            title=source.title,
            source_timestamp=source.source_timestamp,
            ingest_status=source.ingest_status,
            updated_at=source.updated_at,
        )

    def _to_detail(self, source: ResearchSource) -> ResearchSourceDetail:
        return ResearchSourceDetail(
            **self._to_summary(source).model_dump(),
            content=_load_json_dict(source.content_json),
            created_at=source.created_at,
        )


class ResearchReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_reports(
        self,
        workspace_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        subject_id: str | None = None,
        report_type: str | None = None,
    ) -> ListResearchReportsResponse:
        await self._require_workspace(workspace_id)
        page, page_size = _normalize_page(page, page_size)
        query = select(ResearchReport).where(ResearchReport.workspace_id == workspace_id)
        if subject_id:
            query = query.where(ResearchReport.subject_id == subject_id)
        if report_type:
            query = query.where(ResearchReport.report_type == report_type)
        query = query.order_by(ResearchReport.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        reports = result.scalars().all()
        version_ids = {item.latest_version_id for item in reports if item.latest_version_id}
        version_map = await self._load_versions(version_ids)
        items = [self._to_summary(item, version_map.get(item.latest_version_id)) for item in reports]
        return ListResearchReportsResponse(items=items)

    async def create_report(
        self,
        workspace_id: str,
        request: CreateResearchReportRequest,
    ) -> ResearchReportDetail:
        await self._require_workspace(workspace_id)
        await self._validate_subject_membership(workspace_id, request.subject_id)
        await self._validate_source_refs(request.source_session_id, request.source_iteration_id)

        report = ResearchReport(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            subject_id=request.subject_id,
            report_type=request.report_type,
            title=request.title,
            status='active',
        )
        version = ResearchReportVersion(
            id=str(uuid.uuid4()),
            report_id=report.id,
            version_number=1,
            content_json=_dump_json(request.content),
            summary_text=request.summary_text,
            source_session_id=request.source_session_id,
            source_iteration_id=request.source_iteration_id,
            confidence_score=request.confidence_score,
        )
        report.latest_version_id = version.id
        self.db.add(report)
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(report)
        await self.db.refresh(version)
        return self._to_detail(report, version)

    async def get_report(self, report_id: str) -> ResearchReportDetail | None:
        report = await self.db.get(ResearchReport, report_id)
        if report is None:
            return None
        latest_version = await self._get_latest_version(report.latest_version_id)
        return self._to_detail(report, latest_version)

    async def update_report(
        self,
        report_id: str,
        request: UpdateResearchReportRequest,
    ) -> ResearchReportDetail:
        report = await self._require_report(report_id)
        if 'subject_id' in request.model_fields_set:
            await self._validate_subject_membership(report.workspace_id, request.subject_id)
            report.subject_id = request.subject_id
        if 'report_type' in request.model_fields_set:
            report.report_type = request.report_type
        if 'title' in request.model_fields_set:
            report.title = request.title
        if 'status' in request.model_fields_set:
            report.status = request.status
        if 'archived_at' in request.model_fields_set:
            report.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(report)
        latest_version = await self._get_latest_version(report.latest_version_id)
        return self._to_detail(report, latest_version)

    async def list_versions(self, report_id: str) -> ListResearchReportVersionsResponse:
        await self._require_report(report_id)
        result = await self.db.execute(
            select(ResearchReportVersion)
            .where(ResearchReportVersion.report_id == report_id)
            .order_by(ResearchReportVersion.version_number.desc())
        )
        items = [self._to_version_detail(item) for item in result.scalars().all()]
        return ListResearchReportVersionsResponse(items=items)

    async def create_version(
        self,
        report_id: str,
        request: CreateResearchReportVersionRequest,
    ) -> ResearchReportDetail:
        report = await self._require_report(report_id)
        await self._validate_source_refs(request.source_session_id, request.source_iteration_id)
        version_number = await _next_report_version_number(self.db, report_id)
        version = ResearchReportVersion(
            id=str(uuid.uuid4()),
            report_id=report_id,
            version_number=version_number,
            content_json=_dump_json(request.content),
            summary_text=request.summary_text,
            source_session_id=request.source_session_id,
            source_iteration_id=request.source_iteration_id,
            confidence_score=request.confidence_score,
        )
        report.latest_version_id = version.id
        self.db.add(version)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(report)
        await self.db.refresh(version)
        return self._to_detail(report, version)

    async def _require_workspace(self, workspace_id: str) -> DomainWorkspace:
        workspace = await self.db.get(DomainWorkspace, workspace_id)
        if workspace is None:
            raise DomainWorkspaceNotFoundError('DOMAIN_WORKSPACE_NOT_FOUND')
        return workspace

    async def _require_report(self, report_id: str) -> ResearchReport:
        report = await self.db.get(ResearchReport, report_id)
        if report is None:
            raise DomainWorkspaceNotFoundError('RESEARCH_REPORT_NOT_FOUND')
        return report

    async def _validate_subject_membership(self, workspace_id: str, subject_id: str | None) -> None:
        if subject_id is None:
            return
        subject = await self.db.get(WorkspaceSubject, subject_id)
        if subject is None or subject.workspace_id != workspace_id:
            raise DomainWorkspaceValidationError(
                'WORKSPACE_RUN_INVALID',
                'subject does not belong to workspace',
            )

    async def _validate_source_refs(
        self,
        source_session_id: str | None,
        source_iteration_id: str | None,
    ) -> None:
        if source_session_id and await self.db.get(PromptSession, source_session_id) is None:
            raise DomainWorkspaceValidationError(
                'RESEARCH_REPORT_VERSION_INVALID',
                'source session does not exist',
            )
        if source_iteration_id and await self.db.get(PromptIteration, source_iteration_id) is None:
            raise DomainWorkspaceValidationError(
                'RESEARCH_REPORT_VERSION_INVALID',
                'source iteration does not exist',
            )

    async def _get_latest_version(self, version_id: str | None) -> ResearchReportVersion | None:
        if not version_id:
            return None
        return await self.db.get(ResearchReportVersion, version_id)

    async def _load_versions(self, version_ids: set[str]) -> dict[str, ResearchReportVersion]:
        if not version_ids:
            return {}
        result = await self.db.execute(
            select(ResearchReportVersion)
            .where(ResearchReportVersion.id.in_(version_ids))
        )
        return {item.id: item for item in result.scalars().all()}

    def _to_summary(
        self,
        report: ResearchReport,
        latest_version: ResearchReportVersion | None,
    ) -> ResearchReportSummary:
        return ResearchReportSummary(
            id=report.id,
            workspace_id=report.workspace_id,
            subject_id=report.subject_id,
            report_type=report.report_type,
            title=report.title,
            status=report.status,
            latest_version=self._to_version_summary(latest_version),
            updated_at=report.updated_at,
        )

    def _to_detail(
        self,
        report: ResearchReport,
        latest_version: ResearchReportVersion | None,
    ) -> ResearchReportDetail:
        summary = self._to_summary(report, latest_version)
        return ResearchReportDetail(
            **summary.model_dump(exclude={'latest_version'}),
            latest_version=self._to_version_detail(latest_version),
            created_at=report.created_at,
            archived_at=report.archived_at,
        )

    def _to_version_summary(
        self,
        version: ResearchReportVersion | None,
    ) -> ResearchReportVersionSummary | None:
        if version is None:
            return None
        confidence_score = float(version.confidence_score) if version.confidence_score is not None else None
        return ResearchReportVersionSummary(
            id=version.id,
            version_number=version.version_number,
            summary_text=version.summary_text,
            confidence_score=confidence_score,
            created_at=version.created_at,
        )

    def _to_version_detail(
        self,
        version: ResearchReportVersion | None,
    ) -> ResearchReportVersionDetail | None:
        if version is None:
            return None
        return ResearchReportVersionDetail(
            **self._to_version_summary(version).model_dump(),
            content=_load_json_dict(version.content_json),
            source_session_id=version.source_session_id,
            source_iteration_id=version.source_iteration_id,
        )
