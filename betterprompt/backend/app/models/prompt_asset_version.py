from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromptAssetVersion(Base):
    __tablename__ = 'prompt_asset_versions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('prompt_assets.id'), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    source_iteration_id: Mapped[str | None] = mapped_column(ForeignKey('prompt_iterations.id'), nullable=True, index=True)
    source_asset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey('prompt_asset_versions.id'),
        nullable=True,
        index=True,
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
