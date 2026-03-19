from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_alert import AgentAlert
from app.models.agent_monitor import AgentMonitor
from app.models.agent_run import AgentRun
from app.models.domain_workspace import DomainWorkspace
from app.models.freshness_record import FreshnessRecord
from app.models.prompt_session import PromptSession
from app.models.run_preset import RunPreset
from app.models.watchlist import Watchlist
from app.models.watchlist_item import WatchlistItem
from app.models.workflow_recipe_version import WorkflowRecipeVersion
from app.models.workspace_subject import WorkspaceSubject
from app.schemas.agent_runtime import (
    AgentAlertDetail,
    AgentAlertSummary,
    AgentMonitorDetail,
    AgentMonitorSummary,
    AgentRunDetail,
    AgentRunSummary,
    CreateAgentMonitorRequest,
    CreateWatchlistItemRequest,
    CreateWatchlistRequest,
    FreshnessRecordDetail,
    FreshnessRecordSummary,
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
    WatchlistItemSummary,
    WatchlistSummary,
)
from app.schemas.workflow_asset import RunPresetLaunchRequest
from app.services.llm import PromptLLMConfigurationError, PromptLLMRequestError
from app.services.prompt_agent.errors import PromptAgentRequestError
from app.services.prompt_agent_service import PromptAgentService
from app.services.run_preset_launch_service import RunPresetLaunchService


MAX_PAGE_SIZE = 100
PROMPT_SESSION_ENTRY_MODES = {'generate', 'debug', 'evaluate'}


class AgentRuntimeNotFoundError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


class AgentRuntimeValidationError(Exception):
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


def _as_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class WatchlistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_watchlists(
        self,
        *,
        workspace_id: str | None = None,
        archived: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> ListWatchlistsResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(Watchlist)
        query = query.where(Watchlist.archived_at.is_not(None) if archived else Watchlist.archived_at.is_(None))
        if workspace_id:
            query = query.where(Watchlist.workspace_id == workspace_id)
        query = query.order_by(Watchlist.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = [self._to_summary(item) for item in result.scalars().all()]
        return ListWatchlistsResponse(items=items)

    async def create_watchlist(self, request: CreateWatchlistRequest) -> WatchlistDetail:
        await self._require_workspace(request.workspace_id)
        watchlist = Watchlist(
            id=str(uuid.uuid4()),
            workspace_id=request.workspace_id,
            name=request.name,
            description=request.description,
            status='active',
        )
        self.db.add(watchlist)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(watchlist)
        return self._to_detail(watchlist)

    async def get_watchlist(self, watchlist_id: str) -> WatchlistDetail | None:
        watchlist = await self.db.get(Watchlist, watchlist_id)
        if watchlist is None:
            return None
        return self._to_detail(watchlist)

    async def update_watchlist(
        self,
        watchlist_id: str,
        request: UpdateWatchlistRequest,
    ) -> WatchlistDetail:
        watchlist = await self._require_watchlist(watchlist_id)
        if 'name' in request.model_fields_set:
            watchlist.name = request.name
        if 'description' in request.model_fields_set:
            watchlist.description = request.description
        if 'status' in request.model_fields_set:
            watchlist.status = request.status
        if 'archived_at' in request.model_fields_set:
            watchlist.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(watchlist)
        return self._to_detail(watchlist)

    async def list_items(self, watchlist_id: str) -> ListWatchlistItemsResponse:
        await self._require_watchlist(watchlist_id)
        result = await self.db.execute(
            select(WatchlistItem)
            .where(WatchlistItem.watchlist_id == watchlist_id)
            .order_by(WatchlistItem.sort_order.asc(), WatchlistItem.updated_at.desc())
        )
        items = [self._to_item_summary(item) for item in result.scalars().all()]
        return ListWatchlistItemsResponse(items=items)

    async def create_item(
        self,
        watchlist_id: str,
        request: CreateWatchlistItemRequest,
    ) -> WatchlistItemDetail:
        watchlist = await self._require_watchlist(watchlist_id)
        await self._validate_subject_membership(watchlist.workspace_id, request.subject_id)
        existing = await self.db.execute(
            select(WatchlistItem)
            .where(
                WatchlistItem.watchlist_id == watchlist_id,
                WatchlistItem.subject_id == request.subject_id,
            )
            .limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            raise AgentRuntimeValidationError(
                'WATCHLIST_ITEM_INVALID',
                'subject already exists in watchlist',
            )

        item = WatchlistItem(
            id=str(uuid.uuid4()),
            watchlist_id=watchlist_id,
            subject_id=request.subject_id,
            sort_order=request.sort_order,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(item)
        return self._to_item_detail(item)

    async def _require_workspace(self, workspace_id: str) -> DomainWorkspace:
        workspace = await self.db.get(DomainWorkspace, workspace_id)
        if workspace is None:
            raise AgentRuntimeNotFoundError('DOMAIN_WORKSPACE_NOT_FOUND')
        return workspace

    async def _require_watchlist(self, watchlist_id: str) -> Watchlist:
        watchlist = await self.db.get(Watchlist, watchlist_id)
        if watchlist is None:
            raise AgentRuntimeNotFoundError('WATCHLIST_NOT_FOUND')
        return watchlist

    async def _validate_subject_membership(self, workspace_id: str, subject_id: str) -> WorkspaceSubject:
        subject = await self.db.get(WorkspaceSubject, subject_id)
        if subject is None:
            raise AgentRuntimeNotFoundError('WORKSPACE_SUBJECT_NOT_FOUND')
        if subject.workspace_id != workspace_id:
            raise AgentRuntimeValidationError(
                'WATCHLIST_ITEM_INVALID',
                'subject does not belong to watchlist workspace',
            )
        return subject

    def _to_summary(self, watchlist: Watchlist) -> WatchlistSummary:
        return WatchlistSummary(
            id=watchlist.id,
            workspace_id=watchlist.workspace_id,
            name=watchlist.name,
            description=watchlist.description,
            status=watchlist.status,
            updated_at=watchlist.updated_at,
        )

    def _to_detail(self, watchlist: Watchlist) -> WatchlistDetail:
        return WatchlistDetail(
            **self._to_summary(watchlist).model_dump(),
            created_at=watchlist.created_at,
            archived_at=watchlist.archived_at,
        )

    def _to_item_summary(self, item: WatchlistItem) -> WatchlistItemSummary:
        return WatchlistItemSummary(
            id=item.id,
            watchlist_id=item.watchlist_id,
            subject_id=item.subject_id,
            sort_order=item.sort_order,
            updated_at=item.updated_at,
        )

    def _to_item_detail(self, item: WatchlistItem) -> WatchlistItemDetail:
        return WatchlistItemDetail(
            **self._to_item_summary(item).model_dump(),
            created_at=item.created_at,
        )


class AgentMonitorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_monitors(
        self,
        *,
        workspace_id: str | None = None,
        subject_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ListAgentMonitorsResponse:
        page, page_size = _normalize_page(page, page_size)
        query = select(AgentMonitor)
        if workspace_id:
            query = query.where(AgentMonitor.workspace_id == workspace_id)
        if subject_id:
            query = query.where(AgentMonitor.subject_id == subject_id)
        if status:
            query = query.where(AgentMonitor.status == status)
        query = query.order_by(AgentMonitor.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = [self._to_summary(item) for item in result.scalars().all()]
        return ListAgentMonitorsResponse(items=items)

    async def create_monitor(self, request: CreateAgentMonitorRequest) -> AgentMonitorDetail:
        await self._require_workspace(request.workspace_id)
        await self._validate_scope(
            workspace_id=request.workspace_id,
            watchlist_id=request.watchlist_id,
            subject_id=request.subject_id,
            run_preset_id=request.run_preset_id,
            workflow_recipe_version_id=request.workflow_recipe_version_id,
        )
        monitor = AgentMonitor(
            id=str(uuid.uuid4()),
            workspace_id=request.workspace_id,
            watchlist_id=request.watchlist_id,
            subject_id=request.subject_id,
            run_preset_id=request.run_preset_id,
            workflow_recipe_version_id=request.workflow_recipe_version_id,
            monitor_type=request.monitor_type,
            status='active',
            trigger_config_json=_dump_json(request.trigger_config),
            alert_policy_json=_dump_json(request.alert_policy),
        )
        self.db.add(monitor)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(monitor)
        return self._to_detail(monitor)

    async def get_monitor(self, monitor_id: str) -> AgentMonitorDetail | None:
        monitor = await self.db.get(AgentMonitor, monitor_id)
        if monitor is None:
            return None
        return self._to_detail(monitor)

    async def update_monitor(
        self,
        monitor_id: str,
        request: UpdateAgentMonitorRequest,
    ) -> AgentMonitorDetail:
        monitor = await self._require_monitor(monitor_id)
        if 'status' in request.model_fields_set:
            monitor.status = request.status
        if 'trigger_config' in request.model_fields_set:
            monitor.trigger_config_json = _dump_json(request.trigger_config or {})
        if 'alert_policy' in request.model_fields_set:
            monitor.alert_policy_json = _dump_json(request.alert_policy or {})
        if 'next_run_at' in request.model_fields_set:
            monitor.next_run_at = request.next_run_at
        if 'archived_at' in request.model_fields_set:
            monitor.archived_at = request.archived_at

        await self.db.commit()
        await self.db.refresh(monitor)
        return self._to_detail(monitor)

    async def trigger_monitor(
        self,
        monitor_id: str,
        *,
        trigger_kind: str = 'manual',
    ) -> AgentRunDetail:
        monitor = await self._require_monitor(monitor_id)
        if monitor.archived_at is not None or monitor.status == 'archived':
            raise AgentRuntimeValidationError(
                'AGENT_MONITOR_TRIGGER_INVALID',
                'cannot trigger an archived monitor',
            )

        previous_run_id = await self._latest_run_id(monitor.id)
        now = _utcnow()
        run = AgentRun(
            id=str(uuid.uuid4()),
            monitor_id=monitor.id,
            workspace_id=monitor.workspace_id,
            subject_id=monitor.subject_id,
            previous_run_id=previous_run_id,
            trigger_kind=trigger_kind,
            run_status='running',
            input_freshness_json='{}',
            change_summary_json=_dump_json({'trigger_kind': trigger_kind, 'state': 'running'}),
            conclusion_summary='Monitor trigger is running',
            started_at=now,
        )
        monitor.last_run_at = now
        self.db.add(run)
        await self.db.flush()
        try:
            if not monitor.run_preset_id:
                raise AgentRuntimeValidationError(
                    'AGENT_MONITOR_TRIGGER_INVALID',
                    'manual trigger currently requires run_preset_id',
                )

            launch_service = RunPresetLaunchService(self.db)
            prompt_agent_service = PromptAgentService(self.db)
            mode, payload = await launch_service.build_launch_request(
                monitor.run_preset_id,
                RunPresetLaunchRequest(
                    domain_workspace_id=monitor.workspace_id,
                    subject_id=monitor.subject_id,
                ),
            )

            session = PromptSession(
                id=str(uuid.uuid4()),
                title=await self._build_session_title(monitor),
                entry_mode=self._session_entry_mode_for_launch(mode, payload),
                status='active',
                run_kind='agent_run',
                domain_workspace_id=monitor.workspace_id,
                subject_id=monitor.subject_id,
                agent_monitor_id=monitor.id,
                trigger_kind=trigger_kind,
                run_preset_id=monitor.run_preset_id,
                workflow_recipe_version_id=monitor.workflow_recipe_version_id,
                metadata_json=_dump_json(
                    {
                        'created_by': 'agent_monitor',
                        'trigger_kind': trigger_kind,
                        'monitor_type': monitor.monitor_type,
                        'watchlist_id': monitor.watchlist_id,
                    }
                ),
            )
            run.prompt_session_id = session.id
            self.db.add(session)
            await self.db.flush()

            payload = payload.model_copy(
                update={
                    'session_id': session.id,
                    'agent_monitor_id': monitor.id,
                    'trigger_kind': trigger_kind,
                }
            )

            if mode == 'generate':
                response = await prompt_agent_service.generate(payload)
            elif mode == 'debug':
                response = await prompt_agent_service.debug(payload)
            elif mode == 'evaluate':
                response = await prompt_agent_service.evaluate(payload)
            else:
                response = await prompt_agent_service.continue_optimization(payload)

            run.prompt_session_id = response.iteration.session_id or session.id
            run.prompt_iteration_id = response.iteration.iteration_id
            run.run_status = 'completed'
            run.finished_at = _utcnow()
            run.change_summary_json = _dump_json(
                {'trigger_kind': trigger_kind, 'state': 'completed', 'mode': mode}
            )
            run.conclusion_summary = f'Monitor trigger completed via {mode} run'
            await launch_service.mark_used(monitor.run_preset_id)
        except (
            AgentRuntimeNotFoundError,
            AgentRuntimeValidationError,
            PromptAgentRequestError,
            PromptLLMConfigurationError,
            PromptLLMRequestError,
        ) as exc:
            run.run_status = 'failed'
            run.finished_at = _utcnow()
            run.change_summary_json = _dump_json(
                {
                    'trigger_kind': trigger_kind,
                    'state': 'failed',
                    'error_code': getattr(exc, 'code', exc.__class__.__name__),
                }
            )
            run.conclusion_summary = self._trigger_error_message(exc)
            await self.db.commit()

        await self.db.refresh(run)
        return self._to_run_detail(run)

    async def list_runs(self, monitor_id: str) -> ListAgentRunsResponse:
        await self._require_monitor(monitor_id)
        result = await self.db.execute(
            select(AgentRun)
            .where(AgentRun.monitor_id == monitor_id)
            .order_by(AgentRun.created_at.desc())
        )
        items = [self._to_run_summary(item) for item in result.scalars().all()]
        return ListAgentRunsResponse(items=items)

    async def get_run(self, run_id: str) -> AgentRunDetail | None:
        run = await self.db.get(AgentRun, run_id)
        if run is None:
            return None
        return self._to_run_detail(run)

    async def _validate_scope(
        self,
        *,
        workspace_id: str,
        watchlist_id: str | None,
        subject_id: str | None,
        run_preset_id: str | None,
        workflow_recipe_version_id: str | None,
    ) -> None:
        if watchlist_id:
            watchlist = await self.db.get(Watchlist, watchlist_id)
            if watchlist is None:
                raise AgentRuntimeNotFoundError('WATCHLIST_NOT_FOUND')
            if watchlist.workspace_id != workspace_id:
                raise AgentRuntimeValidationError(
                    'AGENT_MONITOR_INVALID',
                    'watchlist does not belong to workspace',
                )

        if subject_id:
            subject = await self.db.get(WorkspaceSubject, subject_id)
            if subject is None:
                raise AgentRuntimeNotFoundError('WORKSPACE_SUBJECT_NOT_FOUND')
            if subject.workspace_id != workspace_id:
                raise AgentRuntimeValidationError(
                    'AGENT_MONITOR_INVALID',
                    'subject does not belong to workspace',
                )

        if run_preset_id and await self.db.get(RunPreset, run_preset_id) is None:
            raise AgentRuntimeNotFoundError('RUN_PRESET_NOT_FOUND')

        if workflow_recipe_version_id and await self.db.get(
            WorkflowRecipeVersion,
            workflow_recipe_version_id,
        ) is None:
            raise AgentRuntimeNotFoundError('WORKFLOW_RECIPE_VERSION_NOT_FOUND')

    async def _require_workspace(self, workspace_id: str) -> DomainWorkspace:
        workspace = await self.db.get(DomainWorkspace, workspace_id)
        if workspace is None:
            raise AgentRuntimeNotFoundError('DOMAIN_WORKSPACE_NOT_FOUND')
        return workspace

    async def _require_monitor(self, monitor_id: str) -> AgentMonitor:
        monitor = await self.db.get(AgentMonitor, monitor_id)
        if monitor is None:
            raise AgentRuntimeNotFoundError('AGENT_MONITOR_NOT_FOUND')
        return monitor

    async def _latest_run_id(self, monitor_id: str) -> str | None:
        result = await self.db.execute(
            select(AgentRun.id)
            .where(AgentRun.monitor_id == monitor_id)
            .order_by(AgentRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    def _session_entry_mode_for_launch(self, mode: str, payload: Any) -> str:
        if mode in PROMPT_SESSION_ENTRY_MODES:
            return mode
        source_mode = _as_str(getattr(payload, 'mode', None))
        if source_mode in PROMPT_SESSION_ENTRY_MODES:
            return source_mode
        return 'generate'

    async def _build_session_title(self, monitor: AgentMonitor) -> str:
        if monitor.subject_id:
            subject = await self.db.get(WorkspaceSubject, monitor.subject_id)
            if subject is not None and subject.display_name:
                return f'{subject.display_name} agent rerun'
        if monitor.watchlist_id:
            watchlist = await self.db.get(Watchlist, monitor.watchlist_id)
            if watchlist is not None and watchlist.name:
                return f'{watchlist.name} agent rerun'
        return f'{monitor.monitor_type} agent rerun'

    def _trigger_error_message(self, exc: Exception) -> str:
        message = getattr(exc, 'message', None)
        if isinstance(message, str) and message.strip():
            return message
        return str(exc) or exc.__class__.__name__

    def _to_summary(self, monitor: AgentMonitor) -> AgentMonitorSummary:
        return AgentMonitorSummary(
            id=monitor.id,
            workspace_id=monitor.workspace_id,
            watchlist_id=monitor.watchlist_id,
            subject_id=monitor.subject_id,
            run_preset_id=monitor.run_preset_id,
            workflow_recipe_version_id=monitor.workflow_recipe_version_id,
            monitor_type=monitor.monitor_type,
            status=monitor.status,
            next_run_at=monitor.next_run_at,
            updated_at=monitor.updated_at,
        )

    def _to_detail(self, monitor: AgentMonitor) -> AgentMonitorDetail:
        return AgentMonitorDetail(
            **self._to_summary(monitor).model_dump(),
            trigger_config=_load_json_dict(monitor.trigger_config_json),
            alert_policy=_load_json_dict(monitor.alert_policy_json),
            last_run_at=monitor.last_run_at,
            created_at=monitor.created_at,
            archived_at=monitor.archived_at,
        )

    def _to_run_summary(self, run: AgentRun) -> AgentRunSummary:
        return AgentRunSummary(
            id=run.id,
            monitor_id=run.monitor_id,
            workspace_id=run.workspace_id,
            subject_id=run.subject_id,
            trigger_kind=run.trigger_kind,
            run_status=run.run_status,
            prompt_session_id=run.prompt_session_id,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )

    def _to_run_detail(self, run: AgentRun) -> AgentRunDetail:
        return AgentRunDetail(
            **self._to_run_summary(run).model_dump(),
            previous_run_id=run.previous_run_id,
            prompt_iteration_id=run.prompt_iteration_id,
            input_freshness=_load_json_dict(run.input_freshness_json),
            change_summary=_load_json_dict(run.change_summary_json),
            conclusion_summary=run.conclusion_summary,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )


class AgentAlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_alerts(
        self,
        *,
        workspace_id: str | None = None,
        subject_id: str | None = None,
        status: str | None = None,
    ) -> ListAgentAlertsResponse:
        query = select(AgentAlert)
        if workspace_id:
            query = query.where(AgentAlert.workspace_id == workspace_id)
        if subject_id:
            query = query.where(AgentAlert.subject_id == subject_id)
        if status:
            query = query.where(AgentAlert.status == status)
        result = await self.db.execute(query.order_by(AgentAlert.created_at.desc()))
        items = [self._to_summary(item) for item in result.scalars().all()]
        return ListAgentAlertsResponse(items=items)

    async def get_alert(self, alert_id: str) -> AgentAlertDetail | None:
        alert = await self.db.get(AgentAlert, alert_id)
        if alert is None:
            return None
        return self._to_detail(alert)

    async def update_alert(
        self,
        alert_id: str,
        request: UpdateAgentAlertRequest,
    ) -> AgentAlertDetail:
        alert = await self._require_alert(alert_id)
        alert.status = request.status
        if 'read_at' in request.model_fields_set:
            alert.read_at = request.read_at
        elif request.status == 'read':
            alert.read_at = _utcnow()
        elif request.status == 'unread':
            alert.read_at = None

        await self.db.commit()
        await self.db.refresh(alert)
        return self._to_detail(alert)

    async def _require_alert(self, alert_id: str) -> AgentAlert:
        alert = await self.db.get(AgentAlert, alert_id)
        if alert is None:
            raise AgentRuntimeNotFoundError('AGENT_ALERT_NOT_FOUND')
        return alert

    def _to_summary(self, alert: AgentAlert) -> AgentAlertSummary:
        return AgentAlertSummary(
            id=alert.id,
            workspace_id=alert.workspace_id,
            subject_id=alert.subject_id,
            run_id=alert.run_id,
            severity=alert.severity,
            status=alert.status,
            title=alert.title,
            created_at=alert.created_at,
        )

    def _to_detail(self, alert: AgentAlert) -> AgentAlertDetail:
        return AgentAlertDetail(
            **self._to_summary(alert).model_dump(),
            summary_text=alert.summary_text,
            payload=_load_json_dict(alert.payload_json),
            updated_at=alert.updated_at,
            read_at=alert.read_at,
        )


class FreshnessRecordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_records(
        self,
        *,
        workspace_id: str | None = None,
        subject_id: str | None = None,
        source_id: str | None = None,
        report_id: str | None = None,
        status: str | None = None,
    ) -> ListFreshnessRecordsResponse:
        query = select(FreshnessRecord)
        if workspace_id:
            query = query.where(FreshnessRecord.workspace_id == workspace_id)
        if subject_id:
            query = query.where(FreshnessRecord.subject_id == subject_id)
        if source_id:
            query = query.where(FreshnessRecord.source_id == source_id)
        if report_id:
            query = query.where(FreshnessRecord.report_id == report_id)
        if status:
            query = query.where(FreshnessRecord.status == status)
        result = await self.db.execute(
            query.order_by(FreshnessRecord.observed_at.desc(), FreshnessRecord.updated_at.desc())
        )
        items = [self._to_summary(item) for item in result.scalars().all()]
        return ListFreshnessRecordsResponse(items=items)

    async def get_record(self, record_id: str) -> FreshnessRecordDetail | None:
        record = await self.db.get(FreshnessRecord, record_id)
        if record is None:
            return None
        return self._to_detail(record)

    def _to_summary(self, record: FreshnessRecord) -> FreshnessRecordSummary:
        return FreshnessRecordSummary(
            id=record.id,
            workspace_id=record.workspace_id,
            subject_id=record.subject_id,
            source_id=record.source_id,
            report_id=record.report_id,
            status=record.status,
            observed_at=record.observed_at,
            data_timestamp=record.data_timestamp,
        )

    def _to_detail(self, record: FreshnessRecord) -> FreshnessRecordDetail:
        return FreshnessRecordDetail(
            **self._to_summary(record).model_dump(),
            last_checked_at=record.last_checked_at,
            details=_load_json_dict(record.details_json),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
