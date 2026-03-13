from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PromptSessionEntryMode = Literal['generate', 'debug', 'evaluate']
PromptSessionStatus = Literal['active', 'archived']


class CreatePromptSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    entry_mode: PromptSessionEntryMode = 'generate'
    metadata: dict[str, object] = Field(default_factory=dict)


class PromptSessionSummary(BaseModel):
    id: str
    title: str
    entry_mode: PromptSessionEntryMode
    status: PromptSessionStatus
    latest_iteration_id: str | None = None
    created_at: datetime
    updated_at: datetime


class PromptSessionDetail(PromptSessionSummary):
    metadata: dict[str, object] = Field(default_factory=dict)


class ListPromptSessionsResponse(BaseModel):
    items: list[PromptSessionSummary] = Field(default_factory=list)
