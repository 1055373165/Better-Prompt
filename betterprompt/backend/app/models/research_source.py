from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResearchSource(Base):
    __tablename__ = 'research_sources'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('domain_workspaces.id'), index=True)
    subject_id: Mapped[str | None] = mapped_column(ForeignKey('workspace_subjects.id'), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    canonical_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_json: Mapped[str] = mapped_column(Text, default='{}')
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ingest_status: Mapped[str] = mapped_column(String(40), default='ready')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
