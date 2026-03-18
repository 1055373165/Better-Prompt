from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContextPackVersion(Base):
    __tablename__ = 'context_pack_versions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    context_pack_id: Mapped[str] = mapped_column(ForeignKey('context_packs.id'), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[str] = mapped_column(Text)
    source_iteration_id: Mapped[str | None] = mapped_column(ForeignKey('prompt_iterations.id'), nullable=True, index=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
