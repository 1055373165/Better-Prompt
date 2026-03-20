"""SpikeAgent — handles Step 6 (technical spike verification)."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent
from src.prompts.spike import EVALUATE_SPIKE, SPIKE_RESULT_ANALYSIS
from src.state.schema import AutopilotState

logger = logging.getLogger(__name__)


async def check_spike_needed(state: AutopilotState) -> dict[str, Any]:
    """Check if any ADRs need spike verification."""
    candidates = state.get("spike_candidates", [])
    if not candidates:
        logger.info("[SpikeAgent] No spike candidates — skipping Phase 3")
        return {
            "current_phase": "decomposition",
            "current_step": "step_7",
            "validated_decisions": state.get("decisions", []),
            "spike_failed": False,
        }
    logger.info(f"[SpikeAgent] {len(candidates)} spike candidates to verify")
    return {}


async def evaluate_spike(state: AutopilotState, agent: BaseAgent, candidate_index: int = 0) -> dict[str, Any]:
    """Evaluate a single spike candidate — design verification approach."""
    candidates = state.get("spike_candidates", [])
    if candidate_index >= len(candidates):
        logger.info("[SpikeAgent] All spikes evaluated")
        return {
            "current_phase": "decomposition",
            "current_step": "step_7",
            "validated_decisions": state.get("decisions", []),
            "spike_failed": False,
        }

    candidate = candidates[candidate_index]
    logger.info(f"[SpikeAgent] Evaluating spike for ADR-{candidate.get('adr_number', '?')}: {candidate.get('title', '?')}")

    prompt = EVALUATE_SPIKE.format(adr_content=str(candidate))
    evaluation = await agent.invoke_llm_json(prompt)

    return {
        "current_step": "step_6_spike",
        "waiting_for_human": True,
        "human_prompt": (
            f"Spike verification plan for ADR-{candidate.get('adr_number', '?')}:\n\n"
            f"Goal: {evaluation.get('verification_goal', 'N/A')}\n"
            f"Approach: {evaluation.get('approach', 'N/A')}\n"
            f"Pass criteria: {evaluation.get('pass_criteria', 'N/A')}\n\n"
            "Please execute this verification locally and provide the results, "
            "or type 'skip' to skip this spike."
        ),
    }


async def analyze_spike_result(state: AutopilotState, agent: BaseAgent) -> dict[str, Any]:
    """Analyze spike execution results provided by user."""
    human_response = state.get("human_response", "")

    if human_response.strip().lower() == "skip":
        logger.info("[SpikeAgent] User skipped spike verification")
        return {
            "waiting_for_human": False,
            "spike_failed": False,
        }

    prompt = SPIKE_RESULT_ANALYSIS.format(
        verification_goal=state.get("human_prompt", ""),
        pass_criteria="",
        execution_output=human_response,
    )
    analysis = await agent.invoke_llm_json(prompt)

    if analysis.get("result") == "failed":
        logger.warning("[SpikeAgent] Spike FAILED — may need architecture backtrack")
        return {
            "waiting_for_human": True,
            "spike_failed": True,
            "human_prompt": (
                f"⚠️ Spike verification FAILED.\n\n"
                f"Analysis: {analysis.get('analysis', 'N/A')}\n"
                f"Alternative proposal: {analysis.get('alternative_proposal', 'N/A')}\n\n"
                "Options:\n"
                "1. Accept the alternative proposal\n"
                "2. Backtrack to architecture design (Step 4)\n"
                "3. Skip and proceed with risk\n\n"
                "Please choose (1/2/3):"
            ),
        }

    logger.info("[SpikeAgent] Spike PASSED")
    return {
        "waiting_for_human": False,
        "spike_failed": False,
    }


async def handle_spike_failure(state: AutopilotState) -> dict[str, Any]:
    """Handle user's decision after a spike failure."""
    choice = state.get("human_response", "").strip()

    if choice == "2":
        logger.info("[SpikeAgent] User chose to backtrack to architecture")
        return {
            "needs_backtrack": True,
            "backtrack_target": "step_4",
            "backtrack_reason": "Spike verification failed",
            "backtrack_root_cause": "tech_selection",
            "waiting_for_human": False,
        }
    elif choice == "3":
        logger.warning("[SpikeAgent] User chose to proceed with risk")

    return {
        "current_phase": "decomposition",
        "current_step": "step_7",
        "validated_decisions": state.get("decisions", []),
        "spike_failed": False,
        "waiting_for_human": False,
    }
