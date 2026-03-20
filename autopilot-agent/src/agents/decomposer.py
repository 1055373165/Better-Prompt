"""DecomposerAgent — handles Steps 7-9 (task decomposition + dependency analysis)."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent
from src.prompts.decomposer import DECOMPOSE_TASKS, REFINE_TO_MDU, ANALYZE_DEPENDENCIES
from src.state.schema import AutopilotState

logger = logging.getLogger(__name__)


async def decompose_tasks(state: AutopilotState, agent: BaseAgent) -> dict[str, Any]:
    """Step 7: Break project into top-level tasks."""
    logger.info("[DecomposerAgent] Step 7: Decomposing into top-level tasks")

    prompt = DECOMPOSE_TASKS.format(
        locked_requirement=state["locked_requirement"],
        architecture_plan=state["architecture_plan"],
    )
    tasks = await agent.invoke_llm_json(prompt)

    if not isinstance(tasks, list):
        tasks = [tasks]

    logger.info(f"[DecomposerAgent] Generated {len(tasks)} top-level tasks")
    return {
        "task_tree": {"tasks": tasks},
        "current_step": "step_7",
    }


async def refine_to_mdu(
    state: AutopilotState,
    agent: BaseAgent,
    max_depth: int = 4,
    max_mdu_count: int = 60,
    max_sub_items: int = 8,
) -> dict[str, Any]:
    """Step 8: Recursively refine tasks to MDUs with circuit breaker."""
    logger.info("[DecomposerAgent] Step 8: Refining tasks to MDUs")

    tasks = state.get("task_tree", {}).get("tasks", [])
    all_mdus = []
    current_depth = 1

    for task in tasks:
        if len(all_mdus) >= max_mdu_count:
            logger.warning(
                f"[DecomposerAgent] CIRCUIT BREAKER: MDU count limit reached "
                f"({len(all_mdus)}/{max_mdu_count})"
            )
            break

        prompt = REFINE_TO_MDU.format(
            task=str(task),
            current_depth=current_depth,
            max_depth=max_depth,
            current_mdu_count=len(all_mdus),
            max_mdu_count=max_mdu_count,
            max_sub_items=max_sub_items,
        )
        mdus = await agent.invoke_llm_json(prompt)

        if not isinstance(mdus, list):
            mdus = [mdus]

        if len(mdus) > max_sub_items:
            logger.warning(
                f"[DecomposerAgent] CIRCUIT BREAKER: Task '{task.get('name', '?')}' "
                f"produced {len(mdus)} sub-items (max {max_sub_items}), truncating"
            )
            mdus = mdus[:max_sub_items]

        all_mdus.extend(mdus)

    logger.info(f"[DecomposerAgent] Total MDUs after refinement: {len(all_mdus)}")

    return {
        "execution_plan": {"mdus": all_mdus},
        "total_mdu_count": len(all_mdus),
        "max_depth": current_depth,
        "current_step": "step_8",
    }


async def analyze_dependencies(
    state: AutopilotState,
    agent: BaseAgent,
    max_parallel: int = 3,
) -> dict[str, Any]:
    """Step 9: Analyze dependencies and create execution batches."""
    logger.info("[DecomposerAgent] Step 9: Analyzing dependencies")

    mdus = state.get("execution_plan", {}).get("mdus", [])

    prompt = ANALYZE_DEPENDENCIES.format(
        mdu_list=str(mdus),
        max_parallel=max_parallel,
    )
    dep_analysis = await agent.invoke_llm_json(prompt)

    execution_plan = state.get("execution_plan", {})
    execution_plan["dependency_graph"] = dep_analysis.get("dependency_graph", {})
    execution_plan["batches"] = dep_analysis.get("batches", [])
    execution_plan["critical_path"] = dep_analysis.get("critical_path", [])
    execution_plan["total_batches"] = dep_analysis.get("total_batches", 0)

    logger.info(
        f"[DecomposerAgent] Dependency analysis complete: "
        f"{dep_analysis.get('total_batches', 0)} batches"
    )

    return {
        "execution_plan": execution_plan,
        "current_phase": "execution",
        "current_step": "mdu_execute",
        "current_batch": 1,
        "waiting_for_human": True,
        "human_prompt": (
            f"Execution plan ready:\n"
            f"- Total MDUs: {state.get('total_mdu_count', len(mdus))}\n"
            f"- Total batches: {dep_analysis.get('total_batches', 0)}\n"
            f"- Critical path: {' → '.join(dep_analysis.get('critical_path', []))}\n\n"
            "Confirm to start development execution."
        ),
    }
