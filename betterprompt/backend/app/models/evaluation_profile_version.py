from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvaluationProfileVersion(Base):
    __tablename__ = 'evaluation_profile_versions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    evaluation_profile_id: Mapped[str] = mapped_column(ForeignKey('evaluation_profiles.id'), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    rules_json: Mapped[str] = mapped_column(Text)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
