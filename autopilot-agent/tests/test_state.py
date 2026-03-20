"""Unit tests for state layer — DB init, ORM models, CRUD, concurrent writes."""

import os
import tempfile
import threading
from pathlib import Path

import pytest

from src.state.database import get_engine, init_db, reset_connection, get_session
from src.state.models import Base, Project, Phase, Task, MDU, Decision
from src.state.queries import (
    create_project,
    get_project,
    update_project,
    create_phase,
    get_phases,
    create_task,
    create_mdu,
    get_all_mdus,
    complete_mdu,
    skip_mdu,
    add_mdu_dependency,
    create_decision,
    get_decisions,
    get_spike_candidates,
    create_change_log,
    get_change_logs,
    get_progress_summary,
)


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database for each test."""
    reset_connection()
    path = tmp_path / "test.db"
    init_db(path)
    yield path
    reset_connection()


class TestDatabaseInit:
    def test_creates_all_tables(self, db_path):
        engine = get_engine(db_path)
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected = [
            "projects", "decisions", "phases", "tasks",
            "mdus", "mdu_dependencies", "backtrack_log", "change_log",
        ]
        for t in expected:
            assert t in tables, f"Table '{t}' not found"

    def test_wal_mode_enabled(self, db_path):
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"


class TestProjectCRUD:
    def test_create_and_get(self, db_path):
        project = create_project(db_path, "test-project", "Build something")
        assert project.id is not None
        assert project.name == "test-project"

        fetched = get_project(db_path, project.id)
        assert fetched is not None
        assert fetched.goal == "Build something"

    def test_update(self, db_path):
        project = create_project(db_path, "test", "goal")
        update_project(db_path, project.id, status="completed")
        fetched = get_project(db_path, project.id)
        assert fetched.status == "completed"


class TestPhaseCRUD:
    def test_create_and_list(self, db_path):
        project = create_project(db_path, "test", "goal")
        create_phase(db_path, project.id, 1, "Requirement")
        create_phase(db_path, project.id, 2, "Architecture")
        phases = get_phases(db_path, project.id)
        assert len(phases) == 2
        assert phases[0].name == "Requirement"


class TestMDULifecycle:
    def test_create_complete_skip(self, db_path):
        project = create_project(db_path, "test", "goal")
        phase = create_phase(db_path, project.id, 1, "Execution")
        task = create_task(db_path, phase.id, "T1", "Task 1")

        mdu1 = create_mdu(db_path, task.id, "1.1", "First MDU", batch_number=1)
        mdu2 = create_mdu(db_path, task.id, "1.2", "Second MDU", batch_number=1)
        mdu3 = create_mdu(db_path, task.id, "1.3", "Third MDU", batch_number=2)

        add_mdu_dependency(db_path, mdu3.id, mdu2.id)

        complete_mdu(db_path, mdu1.id, ["file1.py"], "Looks good")
        blocked = skip_mdu(db_path, mdu2.id, "Not needed")

        all_mdus = get_all_mdus(db_path, project.id)
        statuses = {m.mdu_number: m.status for m in all_mdus}
        assert statuses["1.1"] == "completed"
        assert statuses["1.2"] == "skipped"
        assert statuses["1.3"] == "blocked"

    def test_progress_summary(self, db_path):
        project = create_project(db_path, "test", "goal")
        phase = create_phase(db_path, project.id, 1, "Exec")
        task = create_task(db_path, phase.id, "T1", "Task")

        for i in range(5):
            mdu = create_mdu(db_path, task.id, f"1.{i}", f"MDU {i}")
            if i < 3:
                complete_mdu(db_path, mdu.id, [], "ok")

        summary = get_progress_summary(db_path, project.id)
        assert summary["total"] == 5
        assert summary["completed"] == 3
        assert summary["percent"] == 60


class TestDecisionCRUD:
    def test_create_and_spike_candidates(self, db_path):
        project = create_project(db_path, "test", "goal")
        create_decision(
            db_path, project.id, 1, "Use LangGraph",
            {"background": "Need DAG"}, spike_required=True,
        )
        create_decision(
            db_path, project.id, 2, "Use Typer",
            {"background": "Need CLI"}, spike_required=False,
        )

        all_decisions = get_decisions(db_path, project.id)
        assert len(all_decisions) == 2

        spikes = get_spike_candidates(db_path, project.id)
        assert len(spikes) == 1
        assert spikes[0].title == "Use LangGraph"


class TestConcurrentWrites:
    def test_parallel_mdu_creation(self, db_path):
        project = create_project(db_path, "test", "goal")
        phase = create_phase(db_path, project.id, 1, "Exec")
        task = create_task(db_path, phase.id, "T1", "Task")

        errors = []
        def writer(worker_id, count):
            try:
                for i in range(count):
                    reset_connection()
                    create_mdu(db_path, task.id, f"w{worker_id}.{i}", f"MDU from worker {worker_id}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=writer, args=(w, 5)) for w in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent write errors: {errors}"
        reset_connection()
        all_mdus = get_all_mdus(db_path, project.id)
        assert len(all_mdus) == 15


class TestChangeLog:
    def test_create_and_list(self, db_path):
        project = create_project(db_path, "test", "goal")
        create_change_log(db_path, project.id, "init", "Project started", "global")
        create_change_log(db_path, project.id, "backtrack", "Backtracked to step 4", "architecture")

        logs = get_change_logs(db_path, project.id)
        assert len(logs) == 2
        assert logs[0].change_type == "init"
        assert logs[1].change_type == "backtrack"
