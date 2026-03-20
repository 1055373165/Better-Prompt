"""Main LangGraph orchestration — 6-phase serial DAG with conditional branches."""

from __future__ import annotations

import logging
from typing import Any, Literal

from langgraph.graph import StateGraph, START, END

from src.state.schema import AutopilotState

logger = logging.getLogger(__name__)

# Phase identifiers
PHASE_REQUIREMENT = "requirement_phase"
PHASE_ARCHITECTURE = "architecture_phase"
PHASE_SPIKE = "spike_phase"
PHASE_DECOMPOSITION = "decomposition_phase"
PHASE_EXECUTION = "execution_phase"
PHASE_WRAPUP = "wrapup_phase"

# Special nodes
HUMAN_GATE = "human_gate"
BACKTRACK_ROUTER = "backtrack_router"


def route_after_human(state: AutopilotState) -> str:
    """Route after human response — check for backtrack or continue."""
    if state.get("needs_backtrack"):
        return BACKTRACK_ROUTER
    phase = state.get("current_phase", "requirement")
    phase_map = {
        "requirement": PHASE_REQUIREMENT,
        "architecture": PHASE_ARCHITECTURE,
        "spike": PHASE_SPIKE,
        "decomposition": PHASE_DECOMPOSITION,
        "execution": PHASE_EXECUTION,
        "wrapup": PHASE_WRAPUP,
    }
    return phase_map.get(phase, PHASE_REQUIREMENT)


def route_phase_transition(state: AutopilotState) -> str:
    """Route to next phase based on current_phase."""
    if state.get("waiting_for_human"):
        return HUMAN_GATE
    if state.get("needs_backtrack"):
        return BACKTRACK_ROUTER

    phase = state.get("current_phase", "requirement")
    transitions = {
        "requirement": PHASE_REQUIREMENT,
        "architecture": PHASE_ARCHITECTURE,
        "spike": PHASE_SPIKE,
        "decomposition": PHASE_DECOMPOSITION,
        "execution": PHASE_EXECUTION,
        "wrapup": PHASE_WRAPUP,
    }
    return transitions.get(phase, END)


def human_gate_node(state: AutopilotState) -> dict[str, Any]:
    """Human-in-the-loop gate — pauses execution for human input."""
    logger.info(
        f"[Orchestrator] Human gate: waiting for input. "
        f"Prompt: {state.get('human_prompt', '')[:80]}..."
    )
    return {}


def backtrack_router_node(state: AutopilotState) -> dict[str, Any]:
    """Route backtrack to the correct phase."""
    target = state.get("backtrack_target", "")
    logger.info(f"[Orchestrator] Backtrack router: target={target}")

    target_phase_map = {
        "step_3": "requirement",
        "step_4": "architecture",
        "step_6": "spike",
        "step_8": "decomposition",
    }
    new_phase = target_phase_map.get(target, "execution")

    return {
        "current_phase": new_phase,
        "current_step": target,
        "needs_backtrack": False,
        "backtrack_target": "",
    }


def route_after_backtrack(state: AutopilotState) -> str:
    """After backtrack routing, go to the target phase."""
    phase = state.get("current_phase", "requirement")
    phase_map = {
        "requirement": PHASE_REQUIREMENT,
        "architecture": PHASE_ARCHITECTURE,
        "spike": PHASE_SPIKE,
        "decomposition": PHASE_DECOMPOSITION,
        "execution": PHASE_EXECUTION,
    }
    return phase_map.get(phase, PHASE_REQUIREMENT)


def build_main_graph() -> StateGraph:
    """Build the top-level orchestration graph.

    Structure:
        START → requirement_phase → architecture_phase → spike_phase
              → decomposition_phase → execution_phase → wrapup_phase → END

    With conditional edges for:
        - human_gate (pauses for human input)
        - backtrack_router (jumps back to earlier phases)
    """
    builder = StateGraph(AutopilotState)

    # Import phase subgraphs (lazy to avoid circular imports)
    from src.orchestrator.phase_graphs import (
        requirement_phase_node,
        architecture_phase_node,
        spike_phase_node,
        decomposition_phase_node,
        execution_phase_node,
        wrapup_phase_node,
    )

    # Add phase nodes
    builder.add_node(PHASE_REQUIREMENT, requirement_phase_node)
    builder.add_node(PHASE_ARCHITECTURE, architecture_phase_node)
    builder.add_node(PHASE_SPIKE, spike_phase_node)
    builder.add_node(PHASE_DECOMPOSITION, decomposition_phase_node)
    builder.add_node(PHASE_EXECUTION, execution_phase_node)
    builder.add_node(PHASE_WRAPUP, wrapup_phase_node)

    # Add special nodes
    builder.add_node(HUMAN_GATE, human_gate_node)
    builder.add_node(BACKTRACK_ROUTER, backtrack_router_node)

    # START → requirement
    builder.add_edge(START, PHASE_REQUIREMENT)

    # Each phase routes through the transition router
    for phase_node in [
        PHASE_REQUIREMENT, PHASE_ARCHITECTURE, PHASE_SPIKE,
        PHASE_DECOMPOSITION, PHASE_EXECUTION,
    ]:
        builder.add_conditional_edges(
            phase_node,
            route_phase_transition,
            {
                HUMAN_GATE: HUMAN_GATE,
                BACKTRACK_ROUTER: BACKTRACK_ROUTER,
                PHASE_REQUIREMENT: PHASE_REQUIREMENT,
                PHASE_ARCHITECTURE: PHASE_ARCHITECTURE,
                PHASE_SPIKE: PHASE_SPIKE,
                PHASE_DECOMPOSITION: PHASE_DECOMPOSITION,
                PHASE_EXECUTION: PHASE_EXECUTION,
                PHASE_WRAPUP: PHASE_WRAPUP,
                END: END,
            },
        )

    # Human gate → route back to appropriate phase
    builder.add_conditional_edges(
        HUMAN_GATE,
        route_after_human,
        {
            BACKTRACK_ROUTER: BACKTRACK_ROUTER,
            PHASE_REQUIREMENT: PHASE_REQUIREMENT,
            PHASE_ARCHITECTURE: PHASE_ARCHITECTURE,
            PHASE_SPIKE: PHASE_SPIKE,
            PHASE_DECOMPOSITION: PHASE_DECOMPOSITION,
            PHASE_EXECUTION: PHASE_EXECUTION,
            PHASE_WRAPUP: PHASE_WRAPUP,
        },
    )

    # Backtrack router → target phase
    builder.add_conditional_edges(
        BACKTRACK_ROUTER,
        route_after_backtrack,
        {
            PHASE_REQUIREMENT: PHASE_REQUIREMENT,
            PHASE_ARCHITECTURE: PHASE_ARCHITECTURE,
            PHASE_SPIKE: PHASE_SPIKE,
            PHASE_DECOMPOSITION: PHASE_DECOMPOSITION,
            PHASE_EXECUTION: PHASE_EXECUTION,
        },
    )

    # Wrapup → END
    builder.add_edge(PHASE_WRAPUP, END)

    return builder
