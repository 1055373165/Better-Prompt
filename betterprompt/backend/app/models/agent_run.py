from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentRun(Base):
    __tablename__ = 'agent_runs'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    monitor_id: Mapped[str] = mapped_column(ForeignKey('agent_monitors.id'), index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('domain_workspaces.id'), index=True)
    subject_id: Mapped[str | None] = mapped_column(ForeignKey('workspace_subjects.id'), nullable=True, index=True)
    previous_run_id: Mapped[str | None] = mapped_column(ForeignKey('agent_runs.id'), nullable=True, index=True)
    prompt_session_id: Mapped[str | None] = mapped_column(ForeignKey('prompt_sessions.id'), nullable=True, index=True)
    prompt_iteration_id: Mapped[str | None] = mapped_column(
        ForeignKey('prompt_iterations.id'),
        nullable=True,
        index=True,
    )
    trigger_kind: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    run_status: Mapped[str] = mapped_column(String(40), default='completed', index=True)
    input_freshness_json: Mapped[str] = mapped_column(Text, default='{}')
    change_summary_json: Mapped[str] = mapped_column(Text, default='{}')
    conclusion_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
