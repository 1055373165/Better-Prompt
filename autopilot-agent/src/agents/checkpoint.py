"""CheckpointAgent — phase acceptance validation + progress updates."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent
from src.mechanisms.bug_driven_evolution import BugDrivenEvolution
from src.prompts.checkpoint import PHASE_CHECKPOINT, PROGRESS_UPDATE
from src.state.schema import AutopilotState

logger = logging.getLogger(__name__)


async def phase_checkpoint(
    state: AutopilotState,
    agent: BaseAgent,
    phase_name: str,
    expected_deliverables: str,
    actual_outputs: str,
) -> dict[str, Any]:
    """Run phase acceptance check — split into AI-verifiable and user-must-verify."""
    logger.info(f"[CheckpointAgent] Running phase checkpoint for: {phase_name}")

    prompt = PHASE_CHECKPOINT.format(
        phase_name=phase_name,
        expected_deliverables=expected_deliverables,
        actual_outputs=actual_outputs,
    )
    result = await agent.invoke_llm_json(prompt)

    ai_passed = result.get("ai_overall") == "pass"
    blocking = result.get("blocking_issues", [])
    user_checks = result.get("user_verification_needed", [])

    if not ai_passed:
        logger.warning(f"[CheckpointAgent] AI checks FAILED for {phase_name}")
        return {
            "waiting_for_human": True,
            "human_prompt": (
                f"⚠️ Phase '{phase_name}' AI checks FAILED.\n\n"
                f"Blocking issues:\n"
                + "\n".join(f"  - {issue}" for issue in blocking)
                + "\n\nThese must be resolved before proceeding."
            ),
        }

    if user_checks:
        logger.info(f"[CheckpointAgent] AI checks passed, {len(user_checks)} user verifications needed")
        return {
            "waiting_for_human": True,
            "human_prompt": (
                f"✅ Phase '{phase_name}' AI checks passed.\n\n"
                f"User verification needed:\n"
                + "\n".join(f"  {i+1}. {check}" for i, check in enumerate(user_checks))
                + "\n\nPlease verify locally and confirm (yes/no):"
            ),
        }

    logger.info(f"[CheckpointAgent] Phase '{phase_name}' fully passed")
    return {"waiting_for_human": False}


async def progress_update(
    state: AutopilotState,
    agent: BaseAgent,
    total_mdus: int,
    completed_mdus: int,
    skipped_mdus: int = 0,
    blocked_mdus: int = 0,
    current_batch: int = 0,
    total_batches: int = 0,
) -> str:
    """Generate a concise progress update for the user."""
    prompt = PROGRESS_UPDATE.format(
        total_mdus=total_mdus,
        completed_mdus=completed_mdus,
        skipped_mdus=skipped_mdus,
        blocked_mdus=blocked_mdus,
        current_batch=current_batch,
        total_batches=total_batches,
        current_phase=state.get("current_phase", "unknown"),
    )
    return await agent.invoke_llm(prompt)


def calculate_heartbeat(completed: int, total: int, last_reported: int, interval: int = 10) -> int | None:
    """Check if a heartbeat should fire. Returns new percentage or None."""
    if total == 0:
        return None
    current_pct = round(completed / total * 100)
    if current_pct >= last_reported + interval:
        return current_pct
    return None


def enforce_evolution_gate(evolution: BugDrivenEvolution) -> dict[str, Any]:
    """Hard gate: block phase transition if bug evolution writebacks are pending.

    Called at every phase boundary. Returns blocking info if pending, empty dict if clear.
    """
    pending = evolution.check_pending()
    if pending:
        descriptions = [p.description for p in pending]
        logger.warning(
            f"[CheckpointAgent] EVOLUTION GATE BLOCKED: "
            f"{len(pending)} pending writebacks"
        )
        return {
            "waiting_for_human": True,
            "human_prompt": (
                f"⛔ Bug-Driven Evolution gate BLOCKED phase transition.\n\n"
                f"{len(pending)} bugs were fixed but their framework evolution "
                f"writebacks are still pending:\n"
                + "\n".join(f"  - {d}" for d in descriptions)
                + "\n\nYou must complete the three-layer drill-down for each "
                f"before proceeding. This is a hard constraint."
            ),
        }
    return {}
