"""Backtrack protocol — 5 root cause categories → 5 backtrack targets."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class RootCause(str, Enum):
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    TECH_SELECTION = "tech_selection"
    DECOMPOSITION = "decomposition"
    IMPLEMENTATION = "implementation"


BACKTRACK_TARGETS = {
    RootCause.REQUIREMENT: "step_3",
    RootCause.ARCHITECTURE: "step_4",
    RootCause.TECH_SELECTION: "step_6",
    RootCause.DECOMPOSITION: "step_8",
    RootCause.IMPLEMENTATION: None,  # no backtrack, just retry current MDU
}


@dataclass
class BacktrackRequest:
    """A request to backtrack to an earlier step."""
    root_cause: RootCause
    target_step: Optional[str]
    reason: str
    trigger_source: str  # e.g. "mdu_execute_step_e", "review_deadlock", "user_command"
    affected_mdu_ids: list[int] = field(default_factory=list)


def classify_root_cause(analysis: str) -> RootCause:
    """Classify the root cause from an analysis string.

    Uses keyword matching as a first pass; the orchestrator can refine
    with LLM analysis if needed.
    """
    lower = analysis.lower()

    if any(kw in lower for kw in ["requirement", "需求", "spec is wrong", "need clarification"]):
        return RootCause.REQUIREMENT
    if any(kw in lower for kw in ["architecture", "架构", "module design", "system design"]):
        return RootCause.ARCHITECTURE
    if any(kw in lower for kw in ["tech selection", "技术选型", "library", "framework choice", "dependency"]):
        return RootCause.TECH_SELECTION
    if any(kw in lower for kw in ["decomposition", "拆解", "mdu too large", "task split"]):
        return RootCause.DECOMPOSITION

    return RootCause.IMPLEMENTATION


def create_backtrack_request(
    reason: str,
    trigger_source: str,
    affected_mdu_ids: list[int] | None = None,
    root_cause: RootCause | None = None,
) -> BacktrackRequest:
    """Create a backtrack request with automatic root cause classification."""
    if root_cause is None:
        root_cause = classify_root_cause(reason)

    target = BACKTRACK_TARGETS[root_cause]

    if target is None:
        logger.info(
            f"[Backtrack] Implementation issue — no backtrack needed, retry current MDU. "
            f"Reason: {reason}"
        )
    else:
        logger.info(
            f"[Backtrack] Root cause: {root_cause.value} → target: {target}. "
            f"Reason: {reason}"
        )

    return BacktrackRequest(
        root_cause=root_cause,
        target_step=target,
        reason=reason,
        trigger_source=trigger_source,
        affected_mdu_ids=affected_mdu_ids or [],
    )


def get_invalidated_mdus(
    backtrack_target: str,
    all_mdu_ids: list[int],
    completed_mdu_ids: list[int],
) -> list[int]:
    """Determine which completed MDUs need to be invalidated by a backtrack.

    For now, a conservative approach: if backtracking to requirement or architecture,
    all completed MDUs are potentially invalidated. For decomposition backtracks,
    only MDUs after the affected task are invalidated.
    """
    if backtrack_target in ("step_3", "step_4"):
        return completed_mdu_ids
    if backtrack_target == "step_6":
        return completed_mdu_ids
    if backtrack_target == "step_8":
        return completed_mdu_ids

    return []
