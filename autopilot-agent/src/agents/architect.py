"""ArchitectAgent — handles Steps 4-5 (architecture design + ADR recording)."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent
from src.prompts.architect import DESIGN_ARCHITECTURE, RECORD_DECISIONS
from src.state.schema import AutopilotState, SpikeCandidate

logger = logging.getLogger(__name__)


async def design_architecture(state: AutopilotState, agent: BaseAgent) -> dict[str, Any]:
    """Step 4: Generate architecture plan based on locked requirement."""
    logger.info("[ArchitectAgent] Step 4: Designing architecture")

    prompt = DESIGN_ARCHITECTURE.format(
        locked_requirement=state["locked_requirement"],
    )
    plan = await agent.invoke_llm(prompt)

    return {
        "architecture_plan": plan,
        "current_step": "step_4",
        "waiting_for_human": True,
        "human_prompt": (
            "Architecture plan generated. Please review and confirm or adjust:\n\n"
            + plan
        ),
    }


async def record_decisions(state: AutopilotState, agent: BaseAgent) -> dict[str, Any]:
    """Step 5: Extract and record ADRs from confirmed architecture plan."""
    logger.info("[ArchitectAgent] Step 5: Recording architecture decisions")

    arch_plan = state["architecture_plan"]
    if state.get("human_response"):
        arch_plan += f"\n\nUser adjustments:\n{state['human_response']}"

    prompt = RECORD_DECISIONS.format(architecture_plan=arch_plan)
    decisions_raw = await agent.invoke_llm_json(prompt)

    if not isinstance(decisions_raw, list):
        decisions_raw = [decisions_raw]

    spike_candidates: list[SpikeCandidate] = []
    for d in decisions_raw:
        if d.get("spike_required", False):
            spike_candidates.append(SpikeCandidate(
                adr_id=0,
                adr_number=d["adr_number"],
                title=d["title"],
                verification_goal=d.get("content", {}).get("decision", ""),
                approach="",
                pass_criteria="",
            ))

    logger.info(
        f"[ArchitectAgent] Recorded {len(decisions_raw)} ADRs, "
        f"{len(spike_candidates)} need spike verification"
    )

    return {
        "decisions": decisions_raw,
        "spike_candidates": spike_candidates,
        "current_phase": "spike",
        "current_step": "step_6",
        "waiting_for_human": False,
    }
