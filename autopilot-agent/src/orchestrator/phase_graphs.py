"""Phase subgraph nodes — each phase is a single node in the main graph.

Each node function receives the full AutopilotState, delegates to the
appropriate agent functions, and returns state updates.
"""

from __future__ import annotations

import logging
from typing import Any

from src.state.schema import AutopilotState

logger = logging.getLogger(__name__)


# ============================================================
# Phase 1: Requirement (Steps 1-3)
# ============================================================

async def requirement_phase_node(state: AutopilotState) -> dict[str, Any]:
    """Requirement understanding and locking phase."""
    from src.agents.base import BaseAgent, create_llm
    from src.config.settings import Settings
    from src.agents.requirement import (
        understand_requirement,
        lock_requirement,
        finalize_requirement,
    )

    step = state.get("current_step", "step_1")
    logger.info(f"[Phase:Requirement] Entering at step={step}")

    settings = Settings.from_env()
    llm = create_llm(settings.llm)
    agent = BaseAgent("RequirementAgent", llm, settings.concurrency)

    if step in ("step_1", "step_2"):
        result = await understand_requirement(state, agent)
        lock_result = await lock_requirement({**state, **result}, agent)
        return {**result, **lock_result}

    if step == "step_3":
        return await finalize_requirement(state, agent)

    return {"current_phase": "architecture", "current_step": "step_4"}


# ============================================================
# Phase 2: Architecture (Steps 4-5)
# ============================================================

async def architecture_phase_node(state: AutopilotState) -> dict[str, Any]:
    """Architecture design and decision recording phase."""
    from src.agents.base import BaseAgent, create_llm
    from src.config.settings import Settings
    from src.agents.architect import design_architecture, record_decisions

    step = state.get("current_step", "step_4")
    logger.info(f"[Phase:Architecture] Entering at step={step}")

    settings = Settings.from_env()
    llm = create_llm(settings.llm)
    agent = BaseAgent("ArchitectAgent", llm, settings.concurrency)

    if step == "step_4":
        return await design_architecture(state, agent)

    if step == "step_5":
        return await record_decisions(state, agent)

    return {"current_phase": "spike", "current_step": "step_6"}


# ============================================================
# Phase 3: Spike (Step 6)
# ============================================================

async def spike_phase_node(state: AutopilotState) -> dict[str, Any]:
    """Technical spike verification phase."""
    from src.agents.base import BaseAgent, create_llm
    from src.config.settings import Settings
    from src.agents.spike import (
        check_spike_needed,
        evaluate_spike,
        analyze_spike_result,
        handle_spike_failure,
    )

    step = state.get("current_step", "step_6")
    logger.info(f"[Phase:Spike] Entering at step={step}")

    settings = Settings.from_env()
    llm = create_llm(settings.llm)
    agent = BaseAgent("SpikeAgent", llm, settings.concurrency)

    if step == "step_6":
        check = await check_spike_needed(state)
        if check.get("current_phase") == "decomposition":
            return check
        return await evaluate_spike(state, agent)

    if step == "step_6_spike":
        result = await analyze_spike_result(state, agent)
        if result.get("spike_failed"):
            return result
        return {
            **result,
            "current_phase": "decomposition",
            "current_step": "step_7",
        }

    if step == "step_6_failure":
        return await handle_spike_failure(state)

    return {"current_phase": "decomposition", "current_step": "step_7"}


# ============================================================
# Phase 4: Decomposition (Steps 7-9) with circuit breaker
# ============================================================

async def decomposition_phase_node(state: AutopilotState) -> dict[str, Any]:
    """Task decomposition with circuit breaker integration."""
    from src.agents.base import BaseAgent, create_llm
    from src.config.settings import Settings
    from src.agents.decomposer import (
        decompose_tasks,
        refine_to_mdu,
        analyze_dependencies,
    )

    step = state.get("current_step", "step_7")
    logger.info(f"[Phase:Decomposition] Entering at step={step}")

    settings = Settings.from_env()
    llm = create_llm(settings.llm)
    agent = BaseAgent("DecomposerAgent", llm, settings.concurrency)
    cb = settings.circuit_breaker

    if step == "step_7":
        result = await decompose_tasks(state, agent)
        refine_result = await refine_to_mdu(
            {**state, **result}, agent,
            max_depth=cb.max_depth,
            max_mdu_count=cb.max_mdu_count,
            max_sub_items=cb.max_sub_items,
        )
        dep_result = await analyze_dependencies(
            {**state, **result, **refine_result}, agent,
            max_parallel=settings.concurrency.max_parallel_mdus,
        )
        return {**result, **refine_result, **dep_result}

    return {"current_phase": "execution", "current_step": "mdu_execute"}


# ============================================================
# Phase 5: Execution loop
# ============================================================

async def execution_phase_node(state: AutopilotState) -> dict[str, Any]:
    """MDU execution loop — delegates to parallel executor."""
    from src.orchestrator.parallel import execute_batch

    step = state.get("current_step", "mdu_execute")
    logger.info(f"[Phase:Execution] Entering at step={step}, batch={state.get('current_batch', 0)}")

    execution_plan = state.get("execution_plan", {})
    batches = execution_plan.get("batches", [])
    current_batch = state.get("current_batch", 1)

    if current_batch > len(batches):
        logger.info("[Phase:Execution] All batches complete")
        return {
            "current_phase": "wrapup",
            "current_step": "wrapup",
        }

    result = await execute_batch(state, current_batch)

    new_completed = state.get("completed_mdu_count", 0) + len(
        [r for r in result.get("mdu_results", []) if r.get("status") == "completed"]
    )

    if result.get("needs_backtrack"):
        return result

    return {
        **result,
        "current_batch": current_batch + 1,
        "completed_mdu_count": new_completed,
    }


# ============================================================
# Phase 6: Wrapup
# ============================================================

async def wrapup_phase_node(state: AutopilotState) -> dict[str, Any]:
    """Global wrapup — generate delivery summary."""
    from src.agents.base import BaseAgent, create_llm
    from src.agents.checkpoint import enforce_evolution_gate
    from src.config.settings import Settings
    from src.mechanisms.bug_driven_evolution import BugDrivenEvolution

    logger.info("[Phase:Wrapup] Generating delivery summary")

    evolution = BugDrivenEvolution()
    gate = enforce_evolution_gate(evolution)
    if gate.get("waiting_for_human"):
        return gate

    settings = Settings.from_env()
    llm = create_llm(settings.llm)
    agent = BaseAgent("WrapupAgent", llm, settings.concurrency)

    total = state.get("total_mdu_count", 0)
    completed = state.get("completed_mdu_count", 0)

    summary_prompt = (
        f"Generate a project delivery summary.\n\n"
        f"Total MDUs: {total}\n"
        f"Completed: {completed}\n"
        f"Architecture decisions: {len(state.get('decisions', []))}\n"
        f"Requirement: {state.get('locked_requirement', '')[:300]}\n\n"
        f"Output: A concise delivery summary covering what was built, "
        f"key decisions made, and any known limitations or follow-up items."
    )
    summary = await agent.invoke_llm(summary_prompt)

    return {
        "current_phase": "wrapup",
        "current_step": "done",
        "messages": [{"role": "assistant", "content": summary}],
    }
