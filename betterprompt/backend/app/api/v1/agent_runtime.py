from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.agent_runtime import (
    AgentAlertDetail,
    AgentMonitorDetail,
    AgentRunDetail,
    CreateAgentMonitorRequest,
    CreateWatchlistItemRequest,
    CreateWatchlistRequest,
    FreshnessRecordDetail,
    ListAgentAlertsResponse,
    ListAgentMonitorsResponse,
    ListAgentRunsResponse,
    ListFreshnessRecordsResponse,
    ListWatchlistItemsResponse,
    ListWatchlistsResponse,
    UpdateAgentAlertRequest,
    UpdateAgentMonitorRequest,
    UpdateWatchlistRequest,
    WatchlistDetail,
    WatchlistItemDetail,
)
from app.services.agent_runtime_service import (
    AgentAlertService,
    AgentMonitorService,
    AgentRuntimeNotFoundError,
    AgentRuntimeValidationError,
    FreshnessRecordService,
    WatchlistService,
)

router = APIRouter(tags=['agent-runtime'])


def _runtime_error(
    status_code: int,
    exc: AgentRuntimeNotFoundError | AgentRuntimeValidationError,
) -> HTTPException:
    return HTTPException(status_code=status_code, detail={'code': exc.code, 'message': exc.message})


@router.get('/watchlists', response_model=ListWatchlistsResponse)
async def list_watchlists(
    db: DbSession,
    workspace_id: str | None = None,
    archived: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> ListWatchlistsResponse:
    service = WatchlistService(db)
    return await service.list_watchlists(
        workspace_id=workspace_id,
        archived=archived,
        page=page,
        page_size=page_size,
    )


@router.post('/watchlists', response_model=WatchlistDetail, status_code=status.HTTP_201_CREATED)
async def create_watchlist(request: CreateWatchlistRequest, db: DbSession) -> WatchlistDetail:
    service = WatchlistService(db)
    try:
        return await service.create_watchlist(request)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except AgentRuntimeValidationError as exc:
        raise _runtime_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/watchlists/{watchlist_id}', response_model=WatchlistDetail)
async def get_watchlist(watchlist_id: str, db: DbSession) -> WatchlistDetail:
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)
    if watchlist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'WATCHLIST_NOT_FOUND', 'message': 'WATCHLIST_NOT_FOUND'},
        )
    return watchlist


@router.patch('/watchlists/{watchlist_id}', response_model=WatchlistDetail)
async def update_watchlist(
    watchlist_id: str,
    request: UpdateWatchlistRequest,
    db: DbSession,
) -> WatchlistDetail:
    service = WatchlistService(db)
    try:
        return await service.update_watchlist(watchlist_id, request)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except AgentRuntimeValidationError as exc:
        raise _runtime_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/watchlists/{watchlist_id}/items', response_model=ListWatchlistItemsResponse)
async def list_watchlist_items(watchlist_id: str, db: DbSession) -> ListWatchlistItemsResponse:
    service = WatchlistService(db)
    try:
        return await service.list_items(watchlist_id)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.post(
    '/watchlists/{watchlist_id}/items',
    response_model=WatchlistItemDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_watchlist_item(
    watchlist_id: str,
    request: CreateWatchlistItemRequest,
    db: DbSession,
) -> WatchlistItemDetail:
    service = WatchlistService(db)
    try:
        return await service.create_item(watchlist_id, request)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except AgentRuntimeValidationError as exc:
        raise _runtime_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/agent-monitors', response_model=ListAgentMonitorsResponse)
async def list_agent_monitors(
    db: DbSession,
    workspace_id: str | None = None,
    subject_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ListAgentMonitorsResponse:
    service = AgentMonitorService(db)
    return await service.list_monitors(
        workspace_id=workspace_id,
        subject_id=subject_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.post('/agent-monitors', response_model=AgentMonitorDetail, status_code=status.HTTP_201_CREATED)
async def create_agent_monitor(
    request: CreateAgentMonitorRequest,
    db: DbSession,
) -> AgentMonitorDetail:
    service = AgentMonitorService(db)
    try:
        return await service.create_monitor(request)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except AgentRuntimeValidationError as exc:
        raise _runtime_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/agent-monitors/{monitor_id}', response_model=AgentMonitorDetail)
async def get_agent_monitor(monitor_id: str, db: DbSession) -> AgentMonitorDetail:
    service = AgentMonitorService(db)
    monitor = await service.get_monitor(monitor_id)
    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'AGENT_MONITOR_NOT_FOUND', 'message': 'AGENT_MONITOR_NOT_FOUND'},
        )
    return monitor


@router.patch('/agent-monitors/{monitor_id}', response_model=AgentMonitorDetail)
async def update_agent_monitor(
    monitor_id: str,
    request: UpdateAgentMonitorRequest,
    db: DbSession,
) -> AgentMonitorDetail:
    service = AgentMonitorService(db)
    try:
        return await service.update_monitor(monitor_id, request)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except AgentRuntimeValidationError as exc:
        raise _runtime_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.post('/agent-monitors/{monitor_id}/trigger', response_model=AgentRunDetail)
async def trigger_agent_monitor(monitor_id: str, db: DbSession) -> AgentRunDetail:
    service = AgentMonitorService(db)
    try:
        return await service.trigger_monitor(monitor_id)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc
    except AgentRuntimeValidationError as exc:
        raise _runtime_error(status.HTTP_400_BAD_REQUEST, exc) from exc


@router.get('/agent-monitors/{monitor_id}/runs', response_model=ListAgentRunsResponse)
async def list_agent_runs(monitor_id: str, db: DbSession) -> ListAgentRunsResponse:
    service = AgentMonitorService(db)
    try:
        return await service.list_runs(monitor_id)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.get('/agent-runs/{run_id}', response_model=AgentRunDetail)
async def get_agent_run(run_id: str, db: DbSession) -> AgentRunDetail:
    service = AgentMonitorService(db)
    run = await service.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'AGENT_RUN_NOT_FOUND', 'message': 'AGENT_RUN_NOT_FOUND'},
        )
    return run


@router.get('/agent-alerts', response_model=ListAgentAlertsResponse)
async def list_agent_alerts(
    db: DbSession,
    workspace_id: str | None = None,
    subject_id: str | None = None,
    status: str | None = None,
) -> ListAgentAlertsResponse:
    service = AgentAlertService(db)
    return await service.list_alerts(workspace_id=workspace_id, subject_id=subject_id, status=status)


@router.get('/agent-alerts/{alert_id}', response_model=AgentAlertDetail)
async def get_agent_alert(alert_id: str, db: DbSession) -> AgentAlertDetail:
    service = AgentAlertService(db)
    alert = await service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'AGENT_ALERT_NOT_FOUND', 'message': 'AGENT_ALERT_NOT_FOUND'},
        )
    return alert


@router.patch('/agent-alerts/{alert_id}', response_model=AgentAlertDetail)
async def update_agent_alert(
    alert_id: str,
    request: UpdateAgentAlertRequest,
    db: DbSession,
) -> AgentAlertDetail:
    service = AgentAlertService(db)
    try:
        return await service.update_alert(alert_id, request)
    except AgentRuntimeNotFoundError as exc:
        raise _runtime_error(status.HTTP_404_NOT_FOUND, exc) from exc


@router.get('/freshness-records', response_model=ListFreshnessRecordsResponse)
async def list_freshness_records(
    db: DbSession,
    workspace_id: str | None = None,
    subject_id: str | None = None,
    source_id: str | None = None,
    report_id: str | None = None,
    status: str | None = None,
) -> ListFreshnessRecordsResponse:
    service = FreshnessRecordService(db)
    return await service.list_records(
        workspace_id=workspace_id,
        subject_id=subject_id,
        source_id=source_id,
        report_id=report_id,
        status=status,
    )


@router.get('/freshness-records/{record_id}', response_model=FreshnessRecordDetail)
async def get_freshness_record(record_id: str, db: DbSession) -> FreshnessRecordDetail:
    service = FreshnessRecordService(db)
    record = await service.get_record(record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'FRESHNESS_RECORD_NOT_FOUND', 'message': 'FRESHNESS_RECORD_NOT_FOUND'},
        )
    return record
