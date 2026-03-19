from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromptSession(Base):
    __tablename__ = 'prompt_sessions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    entry_mode: Mapped[str] = mapped_column(String(32), default='generate')
    status: Mapped[str] = mapped_column(String(32), default='active')
    run_kind: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    domain_workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey('domain_workspaces.id'),
        nullable=True,
        index=True,
    )
    subject_id: Mapped[str | None] = mapped_column(
        ForeignKey('workspace_subjects.id'),
        nullable=True,
        index=True,
    )
    agent_monitor_id: Mapped[str | None] = mapped_column(
        ForeignKey('agent_monitors.id'),
        nullable=True,
        index=True,
    )
    trigger_kind: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    run_preset_id: Mapped[str | None] = mapped_column(ForeignKey('run_presets.id'), nullable=True, index=True)
    workflow_recipe_version_id: Mapped[str | None] = mapped_column(
        ForeignKey('workflow_recipe_versions.id'),
        nullable=True,
        index=True,
    )
    latest_iteration_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
