from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentMonitor(Base):
    __tablename__ = 'agent_monitors'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('domain_workspaces.id'), index=True)
    watchlist_id: Mapped[str | None] = mapped_column(ForeignKey('watchlists.id'), nullable=True, index=True)
    subject_id: Mapped[str | None] = mapped_column(ForeignKey('workspace_subjects.id'), nullable=True, index=True)
    run_preset_id: Mapped[str | None] = mapped_column(ForeignKey('run_presets.id'), nullable=True, index=True)
    workflow_recipe_version_id: Mapped[str | None] = mapped_column(
        ForeignKey('workflow_recipe_versions.id'),
        nullable=True,
        index=True,
    )
    monitor_type: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(40), default='active', index=True)
    trigger_config_json: Mapped[str] = mapped_column(Text, default='{}')
    alert_policy_json: Mapped[str] = mapped_column(Text, default='{}')
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
