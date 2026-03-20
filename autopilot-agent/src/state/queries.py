"""State read/write operations — Project CRUD, Phase CRUD, MDU CRUD, ADR/logs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.state.database import get_session
from src.state.models import (
    BacktrackLog,
    ChangeLog,
    Decision,
    MDU,
    MDUDependency,
    Phase,
    Project,
    Task,
)


# ============================================================
# Project CRUD
# ============================================================

def create_project(db_path: Path, name: str, goal: str) -> Project:
    """Create a new project."""
    with get_session(db_path) as session:
        project = Project(name=name, goal=goal, status="in_progress")
        session.add(project)
        session.commit()
        session.refresh(project)
        return project


def get_project(db_path: Path, project_id: int) -> Optional[Project]:
    """Get project by ID."""
    with get_session(db_path) as session:
        return session.get(Project, project_id)


def update_project(db_path: Path, project_id: int, **kwargs) -> None:
    """Update project fields."""
    kwargs["updated_at"] = datetime.now(timezone.utc)
    with get_session(db_path) as session:
        session.execute(
            update(Project).where(Project.id == project_id).values(**kwargs)
        )
        session.commit()


# ============================================================
# Phase CRUD
# ============================================================

def create_phase(db_path: Path, project_id: int, phase_number: int, name: str) -> Phase:
    """Create a new phase."""
    with get_session(db_path) as session:
        phase = Phase(project_id=project_id, phase_number=phase_number, name=name)
        session.add(phase)
        session.commit()
        session.refresh(phase)
        return phase


def get_phases(db_path: Path, project_id: int) -> list[Phase]:
    """Get all phases for a project."""
    with get_session(db_path) as session:
        stmt = select(Phase).where(Phase.project_id == project_id).order_by(Phase.phase_number)
        return list(session.scalars(stmt).all())


def update_phase(db_path: Path, phase_id: int, **kwargs) -> None:
    """Update phase fields."""
    with get_session(db_path) as session:
        session.execute(
            update(Phase).where(Phase.id == phase_id).values(**kwargs)
        )
        session.commit()


# ============================================================
# Task CRUD
# ============================================================

def create_task(db_path: Path, phase_id: int, task_number: str, name: str, depth_level: int = 1) -> Task:
    """Create a new task."""
    with get_session(db_path) as session:
        task = Task(phase_id=phase_id, task_number=task_number, name=name, depth_level=depth_level)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def get_tasks(db_path: Path, phase_id: int) -> list[Task]:
    """Get all tasks for a phase."""
    with get_session(db_path) as session:
        stmt = select(Task).where(Task.phase_id == phase_id).order_by(Task.task_number)
        return list(session.scalars(stmt).all())


# ============================================================
# MDU CRUD + dependency queries + state transitions
# ============================================================

def create_mdu(
    db_path: Path,
    task_id: int,
    mdu_number: str,
    description: str,
    batch_number: Optional[int] = None,
) -> MDU:
    """Create a new MDU."""
    with get_session(db_path) as session:
        mdu = MDU(
            task_id=task_id,
            mdu_number=mdu_number,
            description=description,
            batch_number=batch_number,
        )
        session.add(mdu)
        session.commit()
        session.refresh(mdu)
        return mdu


def get_mdu(db_path: Path, mdu_id: int) -> Optional[MDU]:
    """Get MDU by ID."""
    with get_session(db_path) as session:
        return session.get(MDU, mdu_id)


def get_mdus_by_batch(db_path: Path, project_id: int, batch_number: int) -> list[MDU]:
    """Get all MDUs in a specific batch."""
    with get_session(db_path) as session:
        stmt = (
            select(MDU)
            .join(Task)
            .join(Phase)
            .where(Phase.project_id == project_id)
            .where(MDU.batch_number == batch_number)
            .order_by(MDU.mdu_number)
        )
        return list(session.scalars(stmt).all())


def get_all_mdus(db_path: Path, project_id: int) -> list[MDU]:
    """Get all MDUs for a project."""
    with get_session(db_path) as session:
        stmt = (
            select(MDU)
            .join(Task)
            .join(Phase)
            .where(Phase.project_id == project_id)
            .order_by(MDU.mdu_number)
        )
        return list(session.scalars(stmt).all())


def get_ready_mdus(db_path: Path, project_id: int) -> list[MDU]:
    """Get MDUs whose dependencies are all completed (ready to execute)."""
    with get_session(db_path) as session:
        all_mdus = get_all_mdus(db_path, project_id)
        ready = []
        for mdu in all_mdus:
            if mdu.status != "pending":
                continue
            deps = get_mdu_dependencies(db_path, mdu.id)
            all_deps_done = all(
                _dep_status(session, dep.depends_on_mdu_id) in ("completed", "skipped")
                for dep in deps
            )
            if all_deps_done:
                ready.append(mdu)
        return ready


def _dep_status(session: Session, mdu_id: int) -> str:
    """Get the status of an MDU (helper for dependency check)."""
    mdu = session.get(MDU, mdu_id)
    return mdu.status if mdu else "pending"


def update_mdu(db_path: Path, mdu_id: int, **kwargs) -> None:
    """Update MDU fields."""
    with get_session(db_path) as session:
        session.execute(
            update(MDU).where(MDU.id == mdu_id).values(**kwargs)
        )
        session.commit()


def complete_mdu(db_path: Path, mdu_id: int, code_changes: list[str], review_summary: str) -> None:
    """Mark an MDU as completed."""
    update_mdu(
        db_path, mdu_id,
        status="completed",
        code_changes=code_changes,
        review_summary=review_summary,
        completed_at=datetime.now(timezone.utc),
    )


def skip_mdu(db_path: Path, mdu_id: int, reason: str) -> list[int]:
    """Skip an MDU and mark downstream dependents as blocked. Returns blocked MDU IDs."""
    update_mdu(db_path, mdu_id, status="skipped", skip_reason=reason)
    blocked_ids = _mark_downstream_blocked(db_path, mdu_id)
    return blocked_ids


def _mark_downstream_blocked(db_path: Path, mdu_id: int) -> list[int]:
    """Recursively mark all downstream MDUs as blocked."""
    blocked = []
    with get_session(db_path) as session:
        stmt = select(MDUDependency).where(MDUDependency.depends_on_mdu_id == mdu_id)
        dependents = list(session.scalars(stmt).all())
        for dep in dependents:
            dependent_mdu = session.get(MDU, dep.mdu_id)
            if dependent_mdu and dependent_mdu.status == "pending":
                dependent_mdu.status = "blocked"
                dependent_mdu.skip_reason = f"Blocked by skipped MDU {mdu_id}"
                blocked.append(dep.mdu_id)
                session.commit()
                blocked.extend(_mark_downstream_blocked(db_path, dep.mdu_id))
    return blocked


# ============================================================
# MDU Dependencies
# ============================================================

def add_mdu_dependency(db_path: Path, mdu_id: int, depends_on_mdu_id: int) -> None:
    """Add a dependency between two MDUs."""
    with get_session(db_path) as session:
        dep = MDUDependency(mdu_id=mdu_id, depends_on_mdu_id=depends_on_mdu_id)
        session.add(dep)
        session.commit()


def get_mdu_dependencies(db_path: Path, mdu_id: int) -> list[MDUDependency]:
    """Get all dependencies for an MDU."""
    with get_session(db_path) as session:
        stmt = select(MDUDependency).where(MDUDependency.mdu_id == mdu_id)
        return list(session.scalars(stmt).all())


# ============================================================
# Decision (ADR) CRUD
# ============================================================

def create_decision(db_path: Path, project_id: int, adr_number: int, title: str,
                    content: dict, spike_required: bool = False) -> Decision:
    """Create a new ADR."""
    with get_session(db_path) as session:
        decision = Decision(
            project_id=project_id,
            adr_number=adr_number,
            title=title,
            content=content,
            spike_required=spike_required,
        )
        session.add(decision)
        session.commit()
        session.refresh(decision)
        return decision


def get_decisions(db_path: Path, project_id: int) -> list[Decision]:
    """Get all decisions for a project."""
    with get_session(db_path) as session:
        stmt = select(Decision).where(Decision.project_id == project_id).order_by(Decision.adr_number)
        return list(session.scalars(stmt).all())


def get_spike_candidates(db_path: Path, project_id: int) -> list[Decision]:
    """Get decisions that need spike verification."""
    with get_session(db_path) as session:
        stmt = (
            select(Decision)
            .where(Decision.project_id == project_id)
            .where(Decision.spike_required == True)
            .where(Decision.spike_result == None)
        )
        return list(session.scalars(stmt).all())


def update_decision(db_path: Path, decision_id: int, **kwargs) -> None:
    """Update decision fields."""
    with get_session(db_path) as session:
        session.execute(
            update(Decision).where(Decision.id == decision_id).values(**kwargs)
        )
        session.commit()


# ============================================================
# Backtrack Log
# ============================================================

def create_backtrack_log(
    db_path: Path,
    project_id: int,
    trigger_source: str,
    root_cause_category: str,
    backtrack_target_step: str,
    affected_mdus: Optional[list] = None,
    resolution: Optional[str] = None,
) -> BacktrackLog:
    """Record a backtrack event."""
    with get_session(db_path) as session:
        log = BacktrackLog(
            project_id=project_id,
            trigger_source=trigger_source,
            root_cause_category=root_cause_category,
            backtrack_target_step=backtrack_target_step,
            affected_mdus=affected_mdus,
            resolution=resolution,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log


# ============================================================
# Change Log
# ============================================================

def create_change_log(
    db_path: Path,
    project_id: int,
    change_type: str,
    description: str,
    impact_scope: Optional[str] = None,
) -> ChangeLog:
    """Record a change event."""
    with get_session(db_path) as session:
        log = ChangeLog(
            project_id=project_id,
            change_type=change_type,
            description=description,
            impact_scope=impact_scope,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log


def get_change_logs(db_path: Path, project_id: int) -> list[ChangeLog]:
    """Get all change logs for a project."""
    with get_session(db_path) as session:
        stmt = select(ChangeLog).where(ChangeLog.project_id == project_id).order_by(ChangeLog.created_at)
        return list(session.scalars(stmt).all())


# ============================================================
# Progress summary helpers
# ============================================================

def get_progress_summary(db_path: Path, project_id: int) -> dict:
    """Get a summary of project progress."""
    all_mdus = get_all_mdus(db_path, project_id)
    total = len(all_mdus)
    completed = sum(1 for m in all_mdus if m.status == "completed")
    skipped = sum(1 for m in all_mdus if m.status == "skipped")
    blocked = sum(1 for m in all_mdus if m.status == "blocked")
    in_progress = sum(1 for m in all_mdus if m.status == "in_progress")
    pending = sum(1 for m in all_mdus if m.status == "pending")
    percent = round(completed / total * 100) if total > 0 else 0

    return {
        "total": total,
        "completed": completed,
        "skipped": skipped,
        "blocked": blocked,
        "in_progress": in_progress,
        "pending": pending,
        "percent": percent,
    }
