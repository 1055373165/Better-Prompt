"""SQLAlchemy ORM models — 8 tables covering all v2 protocol state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    locked_requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    architecture_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | in_progress | completed
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    phases: Mapped[list[Phase]] = relationship(back_populates="project", cascade="all, delete-orphan")
    decisions: Mapped[list[Decision]] = relationship(back_populates="project", cascade="all, delete-orphan")
    backtrack_logs: Mapped[list[BacktrackLog]] = relationship(back_populates="project", cascade="all, delete-orphan")
    change_logs: Mapped[list[ChangeLog]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    adr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="decided"
    )  # decided | verified | overturned
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    spike_required: Mapped[bool] = mapped_column(Boolean, default=False)
    spike_result: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # passed | failed | not_applicable
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped[Project] = relationship(back_populates="decisions")


class Phase(Base):
    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    phase_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | in_progress | completed
    checkpoint_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    project: Mapped[Project] = relationship(back_populates="phases")
    tasks: Mapped[list[Task]] = relationship(back_populates="phase", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("phases.id"), nullable=False)
    task_number: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | in_progress | completed | skipped
    depth_level: Mapped[int] = mapped_column(Integer, default=1)

    phase: Mapped[Phase] = relationship(back_populates="tasks")
    mdus: Mapped[list[MDU]] = relationship(back_populates="task", cascade="all, delete-orphan")


class MDU(Base):
    __tablename__ = "mdus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    mdu_number: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | in_progress | completed | skipped | blocked
    skip_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code_changes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    review_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    batch_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    task: Mapped[Task] = relationship(back_populates="mdus")
    dependencies: Mapped[list[MDUDependency]] = relationship(
        back_populates="mdu",
        foreign_keys="MDUDependency.mdu_id",
        cascade="all, delete-orphan",
    )
    dependents: Mapped[list[MDUDependency]] = relationship(
        back_populates="depends_on",
        foreign_keys="MDUDependency.depends_on_mdu_id",
    )


class MDUDependency(Base):
    __tablename__ = "mdu_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mdu_id: Mapped[int] = mapped_column(ForeignKey("mdus.id"), nullable=False)
    depends_on_mdu_id: Mapped[int] = mapped_column(ForeignKey("mdus.id"), nullable=False)

    mdu: Mapped[MDU] = relationship(back_populates="dependencies", foreign_keys=[mdu_id])
    depends_on: Mapped[MDU] = relationship(back_populates="dependents", foreign_keys=[depends_on_mdu_id])


class BacktrackLog(Base):
    __tablename__ = "backtrack_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(100), nullable=False)
    root_cause_category: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # requirement | architecture | tech_selection | decomposition | implementation
    backtrack_target_step: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_mdus: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped[Project] = relationship(back_populates="backtrack_logs")


class ChangeLog(Base):
    __tablename__ = "change_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    change_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # init | backtrack | change_request | skip | phase_complete | resume
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped[Project] = relationship(back_populates="change_logs")
