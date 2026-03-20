"""ReviewerAgent — handles code review with max round limit and upstream detection."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent
from src.prompts.reviewer import REVIEW_CODE
from src.state.schema import MDUResult

logger = logging.getLogger(__name__)


async def review_mdu(
    agent: BaseAgent,
    mdu_number: str,
    mdu_description: str,
    mdu_spec: str,
    code_changes: str,
    review_round: int = 1,
    max_review_rounds: int = 3,
) -> dict[str, Any]:
    """Review code for a single MDU.

    Returns review result with pass/minor/fail status and fix instructions.
    If upstream_issue_detected, signals that the problem is not local.
    """
    logger.info(
        f"[ReviewerAgent] Reviewing MDU {mdu_number} "
        f"(round {review_round}/{max_review_rounds})"
    )

    prompt = REVIEW_CODE.format(
        mdu_number=mdu_number,
        mdu_description=mdu_description,
        mdu_spec=mdu_spec,
        code_changes=code_changes,
        review_round=review_round,
        max_review_rounds=max_review_rounds,
    )
    review = await agent.invoke_llm_json(prompt)

    overall = review.get("overall", "fail")
    upstream = review.get("upstream_issue_detected", False)

    if upstream:
        logger.warning(
            f"[ReviewerAgent] MDU {mdu_number}: UPSTREAM ISSUE detected — "
            f"{review.get('upstream_issue_detail', 'unknown')}"
        )

    logger.info(f"[ReviewerAgent] MDU {mdu_number} review result: {overall}")
    return review


async def review_loop(
    coder_agent: BaseAgent,
    reviewer_agent: BaseAgent,
    mdu_spec: dict,
    initial_code: str,
    max_rounds: int = 3,
) -> dict[str, Any]:
    """Execute the review loop: review → fix → re-review, up to max_rounds.

    Returns final review result and the last code version.
    """
    mdu_number = mdu_spec.get("mdu_number", "?")
    mdu_description = mdu_spec.get("description", "")
    current_code = initial_code

    for round_num in range(1, max_rounds + 1):
        review = await review_mdu(
            agent=reviewer_agent,
            mdu_number=mdu_number,
            mdu_description=mdu_description,
            mdu_spec=str(mdu_spec),
            code_changes=current_code,
            review_round=round_num,
            max_review_rounds=max_rounds,
        )

        if review.get("upstream_issue_detected"):
            return {
                "status": "upstream_issue",
                "review": review,
                "code": current_code,
                "rounds_used": round_num,
            }

        if review.get("overall") in ("pass", "minor"):
            return {
                "status": "passed",
                "review": review,
                "code": current_code,
                "rounds_used": round_num,
            }

        if round_num < max_rounds:
            fix_instructions = review.get("fix_instructions", [])
            logger.info(
                f"[ReviewerAgent] MDU {mdu_number} round {round_num} failed, "
                f"sending {len(fix_instructions)} fix instructions to coder"
            )
            fix_prompt = (
                f"The code review found issues. Please fix the following:\n\n"
                + "\n".join(f"- {instr}" for instr in fix_instructions)
                + f"\n\nCurrent code:\n{current_code}"
            )
            current_code = await coder_agent.invoke_llm(fix_prompt)

    logger.warning(
        f"[ReviewerAgent] MDU {mdu_number} review DEADLOCK after {max_rounds} rounds"
    )
    return {
        "status": "deadlock",
        "review": review,
        "code": current_code,
        "rounds_used": max_rounds,
    }
