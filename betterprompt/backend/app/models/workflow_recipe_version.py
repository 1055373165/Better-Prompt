from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkflowRecipeVersion(Base):
    __tablename__ = 'workflow_recipe_versions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_recipe_id: Mapped[str] = mapped_column(ForeignKey('workflow_recipes.id'), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    definition_json: Mapped[str] = mapped_column(Text)
    source_iteration_id: Mapped[str | None] = mapped_column(ForeignKey('prompt_iterations.id'), nullable=True, index=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
