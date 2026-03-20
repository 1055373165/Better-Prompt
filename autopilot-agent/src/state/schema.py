"""Pydantic state schema for LangGraph + typed data transfer between agents."""

from __future__ import annotations

from typing import Annotated, Any, Optional

from operator import add
from typing_extensions import TypedDict


class MDUResult(TypedDict, total=False):
    """Result of a single MDU execution."""
    mdu_id: int
    mdu_number: str
    status: str  # completed | failed | skipped
    code_changes: list[str]
    review_summary: str
    review_count: int
    error: Optional[str]


class SpikeCandidate(TypedDict, total=False):
    """A decision requiring spike verification."""
    adr_id: int
    adr_number: int
    title: str
    verification_goal: str
    approach: str
    pass_criteria: str


class AutopilotState(TypedDict, total=False):
    """Root state flowing through the LangGraph orchestration.

    This is the single source of truth passed between all agent nodes.
    Fields use LangGraph reducers where aggregation is needed (e.g. mdu_results).
    """

    # --- Project identity ---
    project_id: int
    project_dir: str

    # --- Phase tracking ---
    current_phase: str   # requirement | architecture | spike | decomposition | execution | wrapup
    current_step: str    # e.g. "step_1", "step_4", "mdu_execute"

    # --- Phase 1: Requirement ---
    raw_requirement: str
    ai_understanding: str
    locked_requirement: str

    # --- Phase 2: Architecture ---
    architecture_plan: str
    decisions: list[dict[str, Any]]
    spike_candidates: list[SpikeCandidate]

    # --- Phase 3: Spike ---
    validated_decisions: list[dict[str, Any]]
    spike_failed: bool

    # --- Phase 4: Decomposition ---
    task_tree: dict[str, Any]
    execution_plan: dict[str, Any]  # MDU DAG with dependency info
    total_mdu_count: int
    max_depth: int

    # --- Phase 5: Execution ---
    current_batch: int
    current_mdu_batch: list[int]  # MDU IDs in current parallel batch
    mdu_results: Annotated[list[MDUResult], add]  # fan-in reducer
    completed_mdu_count: int
    heartbeat_percent: int

    # --- Cross-cutting: Backtrack ---
    needs_backtrack: bool
    backtrack_target: str  # step to backtrack to
    backtrack_reason: str
    backtrack_root_cause: str  # requirement | architecture | tech_selection | decomposition | implementation

    # --- Cross-cutting: Change request ---
    change_request: Optional[str]
    change_impact: Optional[dict[str, Any]]

    # --- Human interaction ---
    waiting_for_human: bool
    human_prompt: str
    human_response: str

    # --- Messages (LangGraph convention) ---
    messages: list[Any]

    # --- Error handling ---
    error: Optional[str]
