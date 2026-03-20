"""Unit tests for mechanisms — circuit breaker, scope lock, backtrack, heartbeat, bug evolution."""

import pytest

from src.mechanisms.circuit_breaker import CircuitBreaker, CircuitBreakerState
from src.mechanisms.scope_lock import build_scope_lock, check_scope_violation
from src.mechanisms.backtrack import (
    RootCause,
    classify_root_cause,
    create_backtrack_request,
    BACKTRACK_TARGETS,
)
from src.mechanisms.heartbeat import Heartbeat, HeartbeatState
from src.mechanisms.bug_driven_evolution import (
    BugDrivenEvolution,
    BugReport,
    RootCauseCategory,
)
from src.mechanisms.change_request import (
    create_change_request,
    analyze_impact,
    approve_change,
)
from src.config.settings import CircuitBreakerConfig, HeartbeatConfig


class TestCircuitBreaker:
    def test_depth_limit(self):
        cb = CircuitBreaker(CircuitBreakerConfig(max_depth=3))
        assert cb.check_depth(2) is True
        assert cb.check_depth(4) is False
        assert cb.state.tripped is True

    def test_mdu_count_limit(self):
        cb = CircuitBreaker(CircuitBreakerConfig(max_mdu_count=10))
        assert cb.check_mdu_count(5) is True
        assert cb.check_mdu_count(10) is False
        assert cb.state.tripped is True

    def test_sub_items_limit(self):
        cb = CircuitBreaker(CircuitBreakerConfig(max_sub_items=5))
        assert cb.check_sub_items(3, "task-a") is True
        assert cb.check_sub_items(6, "task-b") is False

    def test_check_all(self):
        cb = CircuitBreaker(CircuitBreakerConfig(max_depth=4, max_mdu_count=60, max_sub_items=8))
        assert cb.check_all(2, 30, 5, "task") is True
        assert cb.check_all(5, 30, 5, "task") is False

    def test_reset(self):
        cb = CircuitBreaker()
        cb.check_depth(999)
        assert cb.state.tripped is True
        cb.reset()
        assert cb.state.tripped is False


class TestScopeLock:
    def test_build_scope_lock_contains_rules(self):
        lock = build_scope_lock({"mdu_number": "1.1"}, max_lines=200)
        assert "SCOPE LOCK" in lock
        assert "200" in lock
        assert "ANTI-WORKAROUND" in lock

    def test_check_scope_violation_clean(self):
        mdu_spec = {"file_path": "src/foo.py"}
        code = "FILE: src/foo.py\n```python\nprint('hello')\n```\nSUMMARY: done\nCONCERNS: none"
        violations = check_scope_violation(code, mdu_spec)
        assert len(violations) == 0

    def test_check_scope_violation_workaround(self):
        mdu_spec = {"file_path": "src/foo.py"}
        code = "FILE: src/foo.py\n# This is a workaround for the upstream bug\nSUMMARY: done"
        violations = check_scope_violation(code, mdu_spec)
        assert any("workaround" in v.lower() for v in violations)


class TestBacktrack:
    def test_classify_root_cause(self):
        assert classify_root_cause("The requirement is wrong") == RootCause.REQUIREMENT
        assert classify_root_cause("Architecture needs rework") == RootCause.ARCHITECTURE
        assert classify_root_cause("Library choice is bad") == RootCause.TECH_SELECTION
        assert classify_root_cause("MDU too large, need re-split") == RootCause.DECOMPOSITION
        assert classify_root_cause("Just a typo in code") == RootCause.IMPLEMENTATION

    def test_create_backtrack_request(self):
        req = create_backtrack_request(
            reason="Architecture doesn't support this pattern",
            trigger_source="review_deadlock",
        )
        assert req.root_cause == RootCause.ARCHITECTURE
        assert req.target_step == "step_4"

    def test_implementation_no_backtrack(self):
        req = create_backtrack_request(
            reason="Simple bug in implementation",
            trigger_source="mdu_execute",
        )
        assert req.root_cause == RootCause.IMPLEMENTATION
        assert req.target_step is None

    def test_all_targets_mapped(self):
        for cause in RootCause:
            assert cause in BACKTRACK_TARGETS


class TestHeartbeat:
    def test_fires_at_interval(self):
        hb = Heartbeat(HeartbeatConfig(percent_interval=10))
        assert hb.check(0, 100) is None
        assert hb.check(10, 100) is not None
        assert hb.check(15, 100) is None  # not yet 20%
        assert hb.check(20, 100) is not None

    def test_fires_on_phase_change(self):
        hb = Heartbeat(HeartbeatConfig(percent_interval=10))
        msg = hb.check(5, 100, "requirement")
        assert msg is not None  # first phase report
        msg = hb.check(5, 100, "architecture")
        assert msg is not None  # phase changed

    def test_force_report(self):
        hb = Heartbeat()
        msg = hb.force_report(25, 100, "execution")
        assert "25%" in msg or "25/100" in msg

    def test_zero_total(self):
        hb = Heartbeat()
        assert hb.check(0, 0) is None


class TestBugDrivenEvolution:
    def test_full_lifecycle(self):
        evo = BugDrivenEvolution()

        report = evo.report_bug(
            description="Import order causes circular dependency",
            direct_cause="Module A imports B which imports A",
            fix_applied="Moved import to function level",
            discovered_during="mdu_execute",
        )
        assert report.fixed is True

        report = evo.analyze_root_cause(
            report,
            category=RootCauseCategory.FLOW_OMISSION,
            why_missed="No circular dependency check in decomposition phase",
        )
        assert report.root_cause_category == RootCauseCategory.FLOW_OMISSION

        plan = evo.plan_evolution(report)
        assert "doc_update" in plan
        assert "code_update" in plan

        record = evo.complete_evolution(
            report,
            doc_changes=["Added circular dependency check to decomposition protocol"],
            code_changes=["Updated decomposer prompt to check for circular deps"],
        )
        assert record.id == 1
        assert len(evo.evolution_log) == 1

    def test_deferred_writeback(self):
        evo = BugDrivenEvolution()
        report = evo.report_bug("Bug X", "cause", "fix", "review")
        evo.defer_writeback(report)

        assert len(evo.pending_writebacks) == 1

        with pytest.raises(RuntimeError, match="BLOCKED"):
            evo.enforce_at_phase_boundary()

    def test_no_pending_allows_proceed(self):
        evo = BugDrivenEvolution()
        assert evo.enforce_at_phase_boundary() is True

    def test_plan_without_analysis_raises(self):
        evo = BugDrivenEvolution()
        report = evo.report_bug("Bug", "cause", "fix", "test")
        with pytest.raises(ValueError, match="root cause analysis"):
            evo.plan_evolution(report)


class TestChangeRequest:
    def test_create_and_analyze(self):
        cr = create_change_request("Add authentication support")
        assert cr.approved is False

        cr = analyze_impact(cr, "Build a web app", total_mdus=20, completed_mdus=5)
        assert cr.impact_analysis is not None
        assert cr.impact_analysis["risk_level"] in ("low", "medium", "high")

    def test_high_completion_warning(self):
        cr = create_change_request("Rewrite database layer")
        cr = analyze_impact(cr, "Build a web app", total_mdus=20, completed_mdus=15)
        assert "70%" in cr.impact_analysis["recommendation"]

    def test_approve_reject(self):
        cr = create_change_request("Minor tweak")
        cr = approve_change(cr)
        assert cr.approved is True
