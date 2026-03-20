"""Bug-Driven Evolution — hard constraint that turns every bug into framework improvement.

Three-layer drill-down:
  Layer 1: Fix the bug
  Layer 2: Root cause analysis — why didn't the framework prevent it?
  Layer 3: Framework evolution — write back defenses to both docs and code
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RootCauseCategory(str, Enum):
    """Categories of framework-level root causes."""
    PROMPT_DEFICIENCY = "prompt_deficiency"        # Agent prompt missing key constraint
    FLOW_OMISSION = "flow_omission"                # Execution protocol missing a check step
    MECHANISM_BLIND_SPOT = "mechanism_blind_spot"   # Circuit breaker/scope lock/backtrack gap
    DATA_MODEL_DEFECT = "data_model_defect"         # State schema missing field or transition
    DEPENDENCY_ANALYSIS_GAP = "dependency_gap"      # MDU dependency analysis incomplete
    ACCEPTANCE_CRITERIA_GAP = "acceptance_gap"      # Phase checkpoint missing check item


EVOLUTION_TARGETS = {
    RootCauseCategory.PROMPT_DEFICIENCY: {
        "doc_section": "Agent prompt definitions",
        "code_target": "src/prompts/",
        "action": "Add missing constraint to the relevant Agent's system prompt",
    },
    RootCauseCategory.FLOW_OMISSION: {
        "doc_section": "完整执行协议",
        "code_target": "src/orchestrator/",
        "action": "Add missing check step to orchestration logic",
    },
    RootCauseCategory.MECHANISM_BLIND_SPOT: {
        "doc_section": "Corresponding mechanism section (回溯/范围锁/熔断)",
        "code_target": "src/mechanisms/",
        "action": "Extend mechanism to cover the uncaught scenario",
    },
    RootCauseCategory.DATA_MODEL_DEFECT: {
        "doc_section": "状态文件规范",
        "code_target": "src/state/",
        "action": "Add missing field/transition to state models and schema",
    },
    RootCauseCategory.DEPENDENCY_ANALYSIS_GAP: {
        "doc_section": "第四阶段：任务拆解",
        "code_target": "src/agents/decomposer.py + src/prompts/decomposer.py",
        "action": "Update dependency analysis logic and prompt",
    },
    RootCauseCategory.ACCEPTANCE_CRITERIA_GAP: {
        "doc_section": "Phase_Checkpoint",
        "code_target": "src/agents/checkpoint.py + src/prompts/checkpoint.py",
        "action": "Add missing check item to phase acceptance",
    },
}


@dataclass
class BugReport:
    """A bug discovered during development, with three-layer analysis."""
    # Layer 1: The bug itself
    description: str
    direct_cause: str
    fix_applied: str
    fixed: bool = False

    # Layer 2: Root cause analysis
    root_cause_category: Optional[RootCauseCategory] = None
    why_framework_missed: str = ""

    # Layer 3: Framework evolution
    doc_changes: list[str] = field(default_factory=list)
    code_changes: list[str] = field(default_factory=list)
    evolution_complete: bool = False
    deferred: bool = False  # [待回写] flag

    # Metadata
    discovered_at: str = ""
    discovered_during: str = ""  # e.g. "mdu_execute", "review", "acceptance"
    evolution_id: Optional[int] = None

    def __post_init__(self):
        if not self.discovered_at:
            self.discovered_at = datetime.now(timezone.utc).isoformat()


@dataclass
class EvolutionRecord:
    """A record of a framework evolution triggered by a bug."""
    id: int
    bug_description: str
    root_cause_category: RootCauseCategory
    doc_changes: list[str]
    code_changes: list[str]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class BugDrivenEvolution:
    """Enforces the three-layer bug drill-down as a hard constraint."""

    def __init__(self):
        self._evolution_log: list[EvolutionRecord] = []
        self._pending_writebacks: list[BugReport] = []
        self._next_id = 1

    @property
    def evolution_log(self) -> list[EvolutionRecord]:
        return self._evolution_log

    @property
    def pending_writebacks(self) -> list[BugReport]:
        return self._pending_writebacks

    def report_bug(
        self,
        description: str,
        direct_cause: str,
        fix_applied: str,
        discovered_during: str,
    ) -> BugReport:
        """Layer 1: Report and fix a bug."""
        report = BugReport(
            description=description,
            direct_cause=direct_cause,
            fix_applied=fix_applied,
            fixed=True,
            discovered_during=discovered_during,
        )
        logger.info(
            f"[BugDrivenEvolution] Bug reported: {description} | "
            f"Cause: {direct_cause} | Fixed: {fix_applied}"
        )
        return report

    def analyze_root_cause(
        self,
        report: BugReport,
        category: RootCauseCategory,
        why_missed: str,
    ) -> BugReport:
        """Layer 2: Analyze why the framework didn't prevent this bug."""
        report.root_cause_category = category
        report.why_framework_missed = why_missed

        target = EVOLUTION_TARGETS.get(category, {})
        logger.info(
            f"[BugDrivenEvolution] Root cause: {category.value} | "
            f"Why missed: {why_missed} | "
            f"Doc target: {target.get('doc_section', 'N/A')} | "
            f"Code target: {target.get('code_target', 'N/A')}"
        )
        return report

    def plan_evolution(self, report: BugReport) -> dict[str, Any]:
        """Generate the evolution plan for Layer 3 (what needs to change)."""
        if report.root_cause_category is None:
            raise ValueError(
                "Cannot plan evolution without root cause analysis. "
                "Layer 2 (analyze_root_cause) must be completed first."
            )

        target = EVOLUTION_TARGETS[report.root_cause_category]
        return {
            "bug": report.description,
            "category": report.root_cause_category.value,
            "doc_update": {
                "target_section": target["doc_section"],
                "action": target["action"],
            },
            "code_update": {
                "target_path": target["code_target"],
                "action": target["action"],
            },
            "generalization_check": (
                "After applying the fix, scan for similar patterns elsewhere "
                "that might have the same vulnerability (举一反三)."
            ),
        }

    def complete_evolution(
        self,
        report: BugReport,
        doc_changes: list[str],
        code_changes: list[str],
    ) -> EvolutionRecord:
        """Layer 3: Record completed framework evolution."""
        report.doc_changes = doc_changes
        report.code_changes = code_changes
        report.evolution_complete = True

        record = EvolutionRecord(
            id=self._next_id,
            bug_description=report.description,
            root_cause_category=report.root_cause_category,
            doc_changes=doc_changes,
            code_changes=code_changes,
        )
        self._next_id += 1
        self._evolution_log.append(record)
        report.evolution_id = record.id

        if report in self._pending_writebacks:
            self._pending_writebacks.remove(report)

        logger.info(
            f"[BugDrivenEvolution] Evolution #{record.id} complete: "
            f"{len(doc_changes)} doc changes, {len(code_changes)} code changes"
        )
        return record

    def defer_writeback(self, report: BugReport) -> BugReport:
        """Mark a bug for deferred writeback (Layer 1 done, Layers 2-3 pending)."""
        report.deferred = True
        self._pending_writebacks.append(report)
        logger.warning(
            f"[BugDrivenEvolution] Deferred writeback for: {report.description}. "
            f"MUST be completed before current phase ends."
        )
        return report

    def check_pending(self) -> list[BugReport]:
        """Check for pending writebacks — called at phase checkpoints."""
        if self._pending_writebacks:
            logger.warning(
                f"[BugDrivenEvolution] {len(self._pending_writebacks)} pending writebacks! "
                f"These MUST be completed before proceeding."
            )
        return self._pending_writebacks

    def enforce_at_phase_boundary(self) -> bool:
        """Hard enforcement: block phase transition if writebacks are pending."""
        pending = self.check_pending()
        if pending:
            descriptions = [p.description for p in pending]
            raise RuntimeError(
                f"[BugDrivenEvolution] BLOCKED: Cannot proceed to next phase. "
                f"{len(pending)} pending bug evolution writebacks: {descriptions}"
            )
        return True
