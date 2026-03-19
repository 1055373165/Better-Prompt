from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


WatchlistStatus = Literal['active', 'archived']
AgentMonitorStatus = Literal['active', 'paused', 'archived']
AgentRunStatus = Literal['queued', 'running', 'completed', 'failed', 'skipped']
AgentAlertStatus = Literal['unread', 'read', 'archived']
FreshnessStatus = Literal['fresh', 'aging', 'stale']


class WatchlistSummary(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str | None = None
    status: WatchlistStatus
    updated_at: datetime


class WatchlistDetail(WatchlistSummary):
    created_at: datetime
    archived_at: datetime | None = None


class ListWatchlistsResponse(BaseModel):
    items: list[WatchlistSummary] = Field(default_factory=list)


class CreateWatchlistRequest(BaseModel):
    workspace_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class UpdateWatchlistRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: WatchlistStatus | None = None
    archived_at: datetime | None = None


class WatchlistItemSummary(BaseModel):
    id: str
    watchlist_id: str
    subject_id: str
    sort_order: int
    updated_at: datetime


class WatchlistItemDetail(WatchlistItemSummary):
    created_at: datetime


class ListWatchlistItemsResponse(BaseModel):
    items: list[WatchlistItemSummary] = Field(default_factory=list)


class CreateWatchlistItemRequest(BaseModel):
    subject_id: str
    sort_order: int = 0


class AgentMonitorSummary(BaseModel):
    id: str
    workspace_id: str
    watchlist_id: str | None = None
    subject_id: str | None = None
    run_preset_id: str | None = None
    workflow_recipe_version_id: str | None = None
    monitor_type: str
    status: AgentMonitorStatus
    next_run_at: datetime | None = None
    updated_at: datetime


class AgentMonitorDetail(AgentMonitorSummary):
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    alert_policy: dict[str, Any] = Field(default_factory=dict)
    last_run_at: datetime | None = None
    created_at: datetime
    archived_at: datetime | None = None


class ListAgentMonitorsResponse(BaseModel):
    items: list[AgentMonitorSummary] = Field(default_factory=list)


class CreateAgentMonitorRequest(BaseModel):
    workspace_id: str
    watchlist_id: str | None = None
    subject_id: str | None = None
    run_preset_id: str | None = None
    workflow_recipe_version_id: str | None = None
    monitor_type: str = Field(..., min_length=1, max_length=40)
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    alert_policy: dict[str, Any] = Field(default_factory=dict)


class UpdateAgentMonitorRequest(BaseModel):
    status: AgentMonitorStatus | None = None
    trigger_config: dict[str, Any] | None = None
    alert_policy: dict[str, Any] | None = None
    next_run_at: datetime | None = None
    archived_at: datetime | None = None


class AgentRunSummary(BaseModel):
    id: str
    monitor_id: str
    workspace_id: str
    subject_id: str | None = None
    trigger_kind: str | None = None
    run_status: AgentRunStatus
    prompt_session_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AgentRunDetail(AgentRunSummary):
    previous_run_id: str | None = None
    prompt_iteration_id: str | None = None
    input_freshness: dict[str, Any] = Field(default_factory=dict)
    change_summary: dict[str, Any] = Field(default_factory=dict)
    conclusion_summary: str | None = None
    created_at: datetime
    updated_at: datetime


class ListAgentRunsResponse(BaseModel):
    items: list[AgentRunSummary] = Field(default_factory=list)


class AgentAlertSummary(BaseModel):
    id: str
    workspace_id: str
    subject_id: str | None = None
    run_id: str
    severity: str
    status: AgentAlertStatus
    title: str
    created_at: datetime


class AgentAlertDetail(AgentAlertSummary):
    summary_text: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime
    read_at: datetime | None = None


class ListAgentAlertsResponse(BaseModel):
    items: list[AgentAlertSummary] = Field(default_factory=list)


class UpdateAgentAlertRequest(BaseModel):
    status: AgentAlertStatus
    read_at: datetime | None = None


class FreshnessRecordSummary(BaseModel):
    id: str
    workspace_id: str
    subject_id: str | None = None
    source_id: str | None = None
    report_id: str | None = None
    status: FreshnessStatus
    observed_at: datetime
    data_timestamp: datetime | None = None


class FreshnessRecordDetail(FreshnessRecordSummary):
    last_checked_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ListFreshnessRecordsResponse(BaseModel):
    items: list[FreshnessRecordSummary] = Field(default_factory=list)
