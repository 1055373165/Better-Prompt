"""Change request protocol — formal entry point for requirement changes."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChangeRequest:
    """A formal requirement change request."""
    description: str
    requested_by: str = "user"
    impact_analysis: Optional[dict[str, Any]] = None
    approved: bool = False
    affected_phases: list[str] = field(default_factory=list)
    affected_mdu_ids: list[int] = field(default_factory=list)
    new_mdus_needed: int = 0


def create_change_request(description: str) -> ChangeRequest:
    """Create a new change request (unapproved)."""
    logger.info(f"[ChangeRequest] New request: {description[:100]}...")
    return ChangeRequest(description=description)


def analyze_impact(
    change: ChangeRequest,
    locked_requirement: str,
    total_mdus: int,
    completed_mdus: int,
) -> ChangeRequest:
    """Analyze the impact of a change request.

    This produces a static analysis. The orchestrator will use LLM
    to refine the analysis and present it to the user.
    """
    change.impact_analysis = {
        "original_requirement_excerpt": locked_requirement[:200],
        "change_description": change.description,
        "total_mdus": total_mdus,
        "completed_mdus": completed_mdus,
        "risk_level": _estimate_risk(change.description, completed_mdus, total_mdus),
        "recommendation": "",
    }

    if completed_mdus / max(total_mdus, 1) > 0.7:
        change.impact_analysis["recommendation"] = (
            "⚠️ Project is >70% complete. Change request may invalidate "
            "significant completed work. Consider deferring to a follow-up iteration."
        )
    elif completed_mdus / max(total_mdus, 1) > 0.3:
        change.impact_analysis["recommendation"] = (
            "Change request at mid-project. Impact assessment critical — "
            "some completed MDUs may need rework."
        )
    else:
        change.impact_analysis["recommendation"] = (
            "Early-stage change. Impact should be manageable."
        )

    logger.info(
        f"[ChangeRequest] Impact analyzed: risk={change.impact_analysis['risk_level']}"
    )
    return change


def approve_change(change: ChangeRequest) -> ChangeRequest:
    """Mark a change request as approved."""
    change.approved = True
    logger.info(f"[ChangeRequest] APPROVED: {change.description[:100]}...")
    return change


def reject_change(change: ChangeRequest) -> ChangeRequest:
    """Mark a change request as rejected."""
    change.approved = False
    logger.info(f"[ChangeRequest] REJECTED: {change.description[:100]}...")
    return change


def _estimate_risk(description: str, completed: int, total: int) -> str:
    """Estimate risk level of a change request."""
    lower = description.lower()

    high_risk_keywords = [
        "architecture", "database", "framework", "rewrite",
        "replace", "migrate", "全部", "重写",
    ]
    if any(kw in lower for kw in high_risk_keywords):
        return "high"

    if completed / max(total, 1) > 0.5:
        return "medium"

    return "low"
