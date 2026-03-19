from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FreshnessRecord(Base):
    __tablename__ = 'freshness_records'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('domain_workspaces.id'), index=True)
    subject_id: Mapped[str | None] = mapped_column(ForeignKey('workspace_subjects.id'), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey('research_sources.id'), nullable=True, index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey('research_reports.id'), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
