from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WatchlistItem(Base):
    __tablename__ = 'watchlist_items'
    __table_args__ = (
        UniqueConstraint('watchlist_id', 'subject_id', name='uq_watchlist_items_watchlist_subject'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    watchlist_id: Mapped[str] = mapped_column(ForeignKey('watchlists.id'), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey('workspace_subjects.id'), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
