"""RequirementAgent — handles Steps 1-3 (requirement understanding + locking)."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent
from src.prompts.requirement import UNDERSTAND_REQUIREMENT, LOCK_REQUIREMENT
from src.state.schema import AutopilotState

logger = logging.getLogger(__name__)


async def receive_requirement(state: AutopilotState) -> dict[str, Any]:
    """Step 1: Receive raw requirement — passthrough, no LLM needed."""
    logger.info("[RequirementAgent] Step 1: Receiving raw requirement")
    return {
        "current_phase": "requirement",
        "current_step": "step_1",
    }


async def understand_requirement(state: AutopilotState, agent: BaseAgent) -> dict[str, Any]:
    """Step 2: AI directly expands requirement understanding."""
    logger.info("[RequirementAgent] Step 2: Understanding requirement")

    prompt = UNDERSTAND_REQUIREMENT.format(
        raw_requirement=state["raw_requirement"],
    )
    understanding = await agent.invoke_llm(prompt)

    logger.info(f"[RequirementAgent] Understanding generated ({len(understanding)} chars)")
    return {
        "ai_understanding": understanding,
        "current_step": "step_2",
    }


async def lock_requirement(state: AutopilotState, agent: BaseAgent) -> dict[str, Any]:
    """Step 3: Interactive requirement locking with user.

    This node generates clarifying questions. The orchestrator handles the
    human-in-the-loop interaction and feeds answers back.
    """
    logger.info("[RequirementAgent] Step 3: Locking requirement")

    prompt = LOCK_REQUIREMENT.format(
        raw_requirement=state["raw_requirement"],
        ai_understanding=state["ai_understanding"],
    )
    lock_output = await agent.invoke_llm(prompt)

    return {
        "current_step": "step_3",
        "waiting_for_human": True,
        "human_prompt": lock_output,
    }


async def finalize_requirement(state: AutopilotState, agent: BaseAgent) -> dict[str, Any]:
    """Step 3 (continued): After user answers, generate locked requirement summary."""
    logger.info("[RequirementAgent] Step 3: Finalizing locked requirement")

    prompt = (
        "Based on the user's answers below, generate the final locked requirement summary.\n\n"
        f"Original questions and context:\n{state.get('human_prompt', '')}\n\n"
        f"User's answers:\n{state.get('human_response', '')}\n\n"
        "Output a concise, structured requirement summary that will serve as the "
        "SOLE requirement baseline for all subsequent development steps."
    )
    locked = await agent.invoke_llm(prompt)

    return {
        "locked_requirement": locked,
        "current_phase": "architecture",
        "current_step": "step_4",
        "waiting_for_human": False,
    }
