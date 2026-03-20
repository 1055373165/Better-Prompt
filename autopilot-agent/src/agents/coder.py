"""CoderAgent — handles MDU coding (prompt compilation + code implementation)."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent
from src.prompts.coder import COMPILE_MDU_PROMPT, IMPLEMENT_CODE
from src.state.schema import AutopilotState, MDUResult

logger = logging.getLogger(__name__)


async def compile_mdu_prompt(
    state: AutopilotState,
    agent: BaseAgent,
    mdu_spec: dict,
) -> str:
    """Compile an optimized coding prompt for a specific MDU."""
    logger.info(f"[CoderAgent] Compiling prompt for MDU {mdu_spec.get('mdu_number', '?')}")

    prompt = COMPILE_MDU_PROMPT.format(
        mdu_spec=str(mdu_spec),
        architecture_summary=state.get("architecture_plan", "")[:500],
        tech_stack="Python, LangGraph, SQLAlchemy, SQLite, Typer",
        existing_files=str(mdu_spec.get("dependencies", [])),
    )
    compiled = await agent.invoke_llm(prompt)
    return compiled


async def implement_mdu(
    state: AutopilotState,
    agent: BaseAgent,
    mdu_spec: dict,
    compiled_prompt: str,
) -> MDUResult:
    """Implement code for a single MDU using the compiled prompt."""
    mdu_number = mdu_spec.get("mdu_number", "?")
    logger.info(f"[CoderAgent] Implementing MDU {mdu_number}")

    prompt = IMPLEMENT_CODE.format(compiled_prompt=compiled_prompt)
    code_output = await agent.invoke_llm(prompt)

    file_changes = _extract_file_changes(code_output)
    summary, concerns = _extract_summary(code_output)

    result = MDUResult(
        mdu_id=mdu_spec.get("id", 0),
        mdu_number=mdu_number,
        status="completed" if not concerns or concerns.lower() == "none" else "completed",
        code_changes=[f["path"] for f in file_changes],
        review_summary=summary,
        review_count=0,
    )

    if concerns and concerns.lower() != "none":
        logger.warning(f"[CoderAgent] MDU {mdu_number} concerns: {concerns}")
        if "upstream" in concerns.lower():
            result["status"] = "failed"
            result["error"] = f"Upstream issue detected: {concerns}"

    return result


async def execute_mdu(
    state: AutopilotState,
    agent: BaseAgent,
    mdu_spec: dict,
) -> MDUResult:
    """Full MDU execution: compile prompt → implement code."""
    compiled_prompt = await compile_mdu_prompt(state, agent, mdu_spec)
    result = await implement_mdu(state, agent, mdu_spec, compiled_prompt)
    return result


def _extract_file_changes(code_output: str) -> list[dict[str, str]]:
    """Extract file paths and content from coder output."""
    files = []
    lines = code_output.split("\n")
    current_file = None
    current_content = []
    in_code_block = False

    for line in lines:
        if line.startswith("FILE: "):
            if current_file and current_content:
                files.append({
                    "path": current_file,
                    "content": "\n".join(current_content),
                })
            current_file = line[6:].strip()
            current_content = []
            in_code_block = False
        elif current_file:
            if line.strip().startswith("```") and not in_code_block:
                in_code_block = True
                continue
            elif line.strip() == "```" and in_code_block:
                in_code_block = False
                continue
            elif in_code_block:
                current_content.append(line)

    if current_file and current_content:
        files.append({
            "path": current_file,
            "content": "\n".join(current_content),
        })

    return files


def _extract_summary(code_output: str) -> tuple[str, str]:
    """Extract SUMMARY and CONCERNS from coder output."""
    summary = ""
    concerns = ""
    for line in code_output.split("\n"):
        if line.startswith("SUMMARY:"):
            summary = line[8:].strip()
        elif line.startswith("CONCERNS:"):
            concerns = line[9:].strip()
    return summary, concerns
