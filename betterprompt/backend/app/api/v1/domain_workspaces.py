from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.domain_workspace import (
    CreateDomainWorkspaceRequest,
    CreateResearchReportRequest,
    CreateResearchReportVersionRequest,
    CreateResearchSourceRequest,
    CreateWorkspaceSubjectRequest,
    DomainWorkspaceDetail,
    ListDomainWorkspacesResponse,
    ListResearchReportsResponse,
    ListResearchReportVersionsResponse,
    ListResearchSourcesResponse,
    ListWorkspaceSubjectsResponse,
    ResearchReportDetail,
    ResearchSourceDetail,
    UpdateDomainWorkspaceRequest,
    UpdateResearchReportRequest,
    UpdateResearchSourceRequest,
    UpdateWorkspaceSubjectRequest,
    WorkspaceSubjectDetail,
)
from app.services.domain_workspace_service import (
    DomainWorkspaceNotFoundError,
    DomainWorkspaceService,
    DomainWorkspaceValidationError,
    ResearchReportService,
    ResearchSourceService,
    WorkspaceSubjectService,
)

router = APIRouter(tags=['domain-workspaces'])


def _workspace_error(
    status_code: int,
    exc: DomainWorkspaceNotFoundError | DomainWorkspaceValidationError,
) -> HTTPException:
    return HTTPException(status_code=status_code, detail={'code': exc.code, 'message': exc.message})


@router.get('/domain-workspaces', response_model=ListDomainWorkspacesResponse)
async def list_domain_workspaces(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    workspace_type: str | None = None,
    archived: bool = False,
) -> ListDomainWorkspacesResponse:
    service = DomainWorkspaceService(db)
    return await service.list_workspaces(
        page=page,
        page_size=page_size,
        workspace_type=workspace_type,
        archived=archived,
    )


@router.post('/domain-workspaces', response_model=DomainWorkspaceDetail, status_code=status.HTTP_201_CREATED)
async def create_domain_workspace(
    request: CreateDomainWorkspaceRequest,
    db: DbSession,
) -> DomainWorkspaceDetail:
    service = DomainWorkspaceService(db)
    try:
        return await service.create_workspace(request)
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/domain-workspaces/{workspace_id}', response_model=DomainWorkspaceDetail)
async def get_domain_workspace(workspace_id: str, db: DbSession) -> DomainWorkspaceDetail:
    service = DomainWorkspaceService(db)
    workspace = await service.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'DOMAIN_WORKSPACE_NOT_FOUND', 'message': 'DOMAIN_WORKSPACE_NOT_FOUND'},
        )
    return workspace


@router.patch('/domain-workspaces/{workspace_id}', response_model=DomainWorkspaceDetail)
async def update_domain_workspace(
    workspace_id: str,
    request: UpdateDomainWorkspaceRequest,
    db: DbSession,
) -> DomainWorkspaceDetail:
    service = DomainWorkspaceService(db)
    try:
        return await service.update_workspace(workspace_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/domain-workspaces/{workspace_id}/subjects', response_model=ListWorkspaceSubjectsResponse)
async def list_workspace_subjects(
    workspace_id: str,
    db: DbSession,
    subject_type: str | None = None,
    q: str | None = None,
) -> ListWorkspaceSubjectsResponse:
    service = WorkspaceSubjectService(db)
    try:
        return await service.list_subjects(workspace_id, subject_type=subject_type, q=q)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post(
    '/domain-workspaces/{workspace_id}/subjects',
    response_model=WorkspaceSubjectDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace_subject(
    workspace_id: str,
    request: CreateWorkspaceSubjectRequest,
    db: DbSession,
) -> WorkspaceSubjectDetail:
    service = WorkspaceSubjectService(db)
    try:
        return await service.create_subject(workspace_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/workspace-subjects/{subject_id}', response_model=WorkspaceSubjectDetail)
async def get_workspace_subject(subject_id: str, db: DbSession) -> WorkspaceSubjectDetail:
    service = WorkspaceSubjectService(db)
    subject = await service.get_subject(subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'WORKSPACE_SUBJECT_NOT_FOUND', 'message': 'WORKSPACE_SUBJECT_NOT_FOUND'},
        )
    return subject


@router.patch('/workspace-subjects/{subject_id}', response_model=WorkspaceSubjectDetail)
async def update_workspace_subject(
    subject_id: str,
    request: UpdateWorkspaceSubjectRequest,
    db: DbSession,
) -> WorkspaceSubjectDetail:
    service = WorkspaceSubjectService(db)
    try:
        return await service.update_subject(subject_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/domain-workspaces/{workspace_id}/sources', response_model=ListResearchSourcesResponse)
async def list_research_sources(
    workspace_id: str,
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    subject_id: str | None = None,
    source_type: str | None = None,
) -> ListResearchSourcesResponse:
    service = ResearchSourceService(db)
    try:
        return await service.list_sources(
            workspace_id,
            page=page,
            page_size=page_size,
            subject_id=subject_id,
            source_type=source_type,
        )
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post(
    '/domain-workspaces/{workspace_id}/sources',
    response_model=ResearchSourceDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_research_source(
    workspace_id: str,
    request: CreateResearchSourceRequest,
    db: DbSession,
) -> ResearchSourceDetail:
    service = ResearchSourceService(db)
    try:
        return await service.create_source(workspace_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/research-sources/{source_id}', response_model=ResearchSourceDetail)
async def get_research_source(source_id: str, db: DbSession) -> ResearchSourceDetail:
    service = ResearchSourceService(db)
    source = await service.get_source(source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'RESEARCH_SOURCE_NOT_FOUND', 'message': 'RESEARCH_SOURCE_NOT_FOUND'},
        )
    return source


@router.patch('/research-sources/{source_id}', response_model=ResearchSourceDetail)
async def update_research_source(
    source_id: str,
    request: UpdateResearchSourceRequest,
    db: DbSession,
) -> ResearchSourceDetail:
    service = ResearchSourceService(db)
    try:
        return await service.update_source(source_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/domain-workspaces/{workspace_id}/reports', response_model=ListResearchReportsResponse)
async def list_research_reports(
    workspace_id: str,
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    subject_id: str | None = None,
    report_type: str | None = None,
) -> ListResearchReportsResponse:
    service = ResearchReportService(db)
    try:
        return await service.list_reports(
            workspace_id,
            page=page,
            page_size=page_size,
            subject_id=subject_id,
            report_type=report_type,
        )
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post(
    '/domain-workspaces/{workspace_id}/reports',
    response_model=ResearchReportDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_research_report(
    workspace_id: str,
    request: CreateResearchReportRequest,
    db: DbSession,
) -> ResearchReportDetail:
    service = ResearchReportService(db)
    try:
        return await service.create_report(workspace_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/research-reports/{report_id}', response_model=ResearchReportDetail)
async def get_research_report(report_id: str, db: DbSession) -> ResearchReportDetail:
    service = ResearchReportService(db)
    report = await service.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'RESEARCH_REPORT_NOT_FOUND', 'message': 'RESEARCH_REPORT_NOT_FOUND'},
        )
    return report


@router.patch('/research-reports/{report_id}', response_model=ResearchReportDetail)
async def update_research_report(
    report_id: str,
    request: UpdateResearchReportRequest,
    db: DbSession,
) -> ResearchReportDetail:
    service = ResearchReportService(db)
    try:
        return await service.update_report(report_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/research-reports/{report_id}/versions', response_model=ListResearchReportVersionsResponse)
async def list_research_report_versions(
    report_id: str,
    db: DbSession,
) -> ListResearchReportVersionsResponse:
    service = ResearchReportService(db)
    try:
        return await service.list_versions(report_id)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post(
    '/research-reports/{report_id}/versions',
    response_model=ResearchReportDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_research_report_version(
    report_id: str,
    request: CreateResearchReportVersionRequest,
    db: DbSession,
) -> ResearchReportDetail:
    service = ResearchReportService(db)
    try:
        return await service.create_version(report_id, request)
    except DomainWorkspaceNotFoundError as exc:
        raise _workspace_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except DomainWorkspaceValidationError as exc:
        raise _workspace_error(status.HTTP_400_BAD_REQUEST, exc) from exc
