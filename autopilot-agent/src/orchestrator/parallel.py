"""Parallel MDU execution — fan-out/fan-in with concurrency limit."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.state.schema import AutopilotState, MDUResult

logger = logging.getLogger(__name__)


async def execute_batch(state: AutopilotState, batch_number: int) -> dict[str, Any]:
    """Execute a batch of MDUs in parallel (fan-out → fan-in).

    Respects max_parallel_mdus concurrency limit via semaphore.
    """
    from src.agents.base import BaseAgent, create_llm
    from src.agents.coder import execute_mdu
    from src.agents.reviewer import review_loop
    from src.agents.checkpoint import calculate_heartbeat
    from src.config.settings import Settings
    from src.mechanisms.scope_lock import check_scope_violation
    from src.mechanisms.heartbeat import Heartbeat

    settings = Settings.from_env()
    max_parallel = settings.concurrency.max_parallel_mdus
    max_review_rounds = settings.review.max_review_rounds

    execution_plan = state.get("execution_plan", {})
    batches = execution_plan.get("batches", [])

    if batch_number > len(batches):
        return {"current_phase": "wrapup", "current_step": "wrapup"}

    batch_info = batches[batch_number - 1]
    mdu_numbers = batch_info.get("mdu_numbers", [])
    mdus = execution_plan.get("mdus", [])

    batch_mdus = [m for m in mdus if m.get("mdu_number") in mdu_numbers]
    if not batch_mdus:
        logger.warning(f"[Parallel] Batch {batch_number}: no MDUs found")
        return {"mdu_results": []}

    logger.info(
        f"[Parallel] Batch {batch_number}: executing {len(batch_mdus)} MDUs "
        f"(max parallel: {max_parallel})"
    )

    semaphore = asyncio.Semaphore(max_parallel)
    results: list[MDUResult] = []
    needs_backtrack = False
    backtrack_info: dict[str, Any] = {}

    async def run_single_mdu(mdu_spec: dict) -> MDUResult:
        """Execute a single MDU with semaphore-controlled concurrency."""
        nonlocal needs_backtrack, backtrack_info

        async with semaphore:
            mdu_num = mdu_spec.get("mdu_number", "?")
            logger.info(f"[Parallel] Starting MDU {mdu_num}")

            llm = create_llm(settings.llm)
            coder = BaseAgent(f"Coder-{mdu_num}", llm, settings.concurrency)
            reviewer = BaseAgent(f"Reviewer-{mdu_num}", llm, settings.concurrency)

            try:
                mdu_result = await execute_mdu(state, coder, mdu_spec)

                if mdu_result.get("status") == "failed":
                    error = mdu_result.get("error", "")
                    if "upstream" in error.lower():
                        needs_backtrack = True
                        backtrack_info = {
                            "needs_backtrack": True,
                            "backtrack_reason": error,
                            "backtrack_root_cause": "implementation",
                        }
                    return mdu_result

                scope_violations = check_scope_violation(
                    str(mdu_result.get("code_changes", [])),
                    mdu_spec,
                )
                if scope_violations:
                    logger.warning(
                        f"[Parallel] MDU {mdu_num} scope violations: {scope_violations}"
                    )

                review_result = await review_loop(
                    coder_agent=coder,
                    reviewer_agent=reviewer,
                    mdu_spec=mdu_spec,
                    initial_code=str(mdu_result.get("code_changes", [])),
                    max_rounds=max_review_rounds,
                )

                if review_result["status"] == "upstream_issue":
                    needs_backtrack = True
                    upstream_detail = review_result.get("review", {}).get(
                        "upstream_issue_detail", "Unknown upstream issue"
                    )
                    backtrack_info = {
                        "needs_backtrack": True,
                        "backtrack_reason": upstream_detail,
                        "backtrack_root_cause": "implementation",
                    }
                    mdu_result["status"] = "failed"
                    mdu_result["error"] = upstream_detail
                elif review_result["status"] == "deadlock":
                    logger.warning(f"[Parallel] MDU {mdu_num} review deadlock")
                    mdu_result["status"] = "failed"
                    mdu_result["error"] = "Review deadlock after max rounds"
                else:
                    mdu_result["status"] = "completed"
                    mdu_result["review_summary"] = str(review_result.get("review", {}))
                    mdu_result["review_count"] = review_result.get("rounds_used", 0)

                return mdu_result

            except Exception as e:
                logger.error(f"[Parallel] MDU {mdu_num} execution error: {e}")
                return MDUResult(
                    mdu_id=mdu_spec.get("id", 0),
                    mdu_number=mdu_num,
                    status="failed",
                    code_changes=[],
                    review_summary="",
                    review_count=0,
                    error=str(e),
                )

    tasks = [run_single_mdu(mdu) for mdu in batch_mdus]
    results = await asyncio.gather(*tasks)

    completed = [r for r in results if r.get("status") == "completed"]
    failed = [r for r in results if r.get("status") == "failed"]

    logger.info(
        f"[Parallel] Batch {batch_number} done: "
        f"{len(completed)} completed, {len(failed)} failed"
    )

    output: dict[str, Any] = {"mdu_results": list(results)}

    if needs_backtrack:
        output.update(backtrack_info)

    heartbeat = Heartbeat(settings.heartbeat)
    total = state.get("total_mdu_count", 0)
    prev_completed = state.get("completed_mdu_count", 0)
    new_completed = prev_completed + len(completed)
    hb_msg = heartbeat.check(new_completed, total, state.get("current_phase", ""))
    if hb_msg:
        logger.info(f"[Parallel] {hb_msg}")
        output["heartbeat_percent"] = round(new_completed / max(total, 1) * 100)

    return output
