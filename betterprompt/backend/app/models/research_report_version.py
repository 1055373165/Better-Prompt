from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResearchReportVersion(Base):
    __tablename__ = 'research_report_versions'
    __table_args__ = (
        UniqueConstraint('report_id', 'version_number', name='uq_research_report_versions_report_id_version_number'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey('research_reports.id'), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    content_json: Mapped[str] = mapped_column(Text, default='{}')
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_session_id: Mapped[str | None] = mapped_column(ForeignKey('prompt_sessions.id'), nullable=True, index=True)
    source_iteration_id: Mapped[str | None] = mapped_column(
        ForeignKey('prompt_iterations.id'),
        nullable=True,
        index=True,
    )
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
