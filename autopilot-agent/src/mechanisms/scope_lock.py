"""Scope lock — prevents MDU execution from expanding beyond spec."""

from __future__ import annotations

SCOPE_LOCK_INJECTION = """
SCOPE LOCK — MANDATORY RULES (injected by system, non-negotiable):
1. Implement ONLY what is specified in the MDU description
2. Do NOT add features, utilities, or "nice-to-haves" beyond the spec
3. Do NOT refactor or modify code outside the target files listed in the MDU
4. Do NOT use workarounds to bypass upstream problems — if you detect an
   upstream issue (wrong interface, missing dependency, architectural mismatch),
   STOP and report it instead of coding around it
5. If the MDU spec is ambiguous, implement the simplest interpretation and
   note the ambiguity in CONCERNS
6. Maximum output: {max_lines} lines of code per MDU
7. Do NOT import libraries not already in pyproject.toml without flagging it

ANTI-WORKAROUND RULE:
If you find yourself writing code that "works around" a problem rather than
solving it directly, this is a signal that the problem is upstream. Stop
coding and report the upstream issue.
"""


def build_scope_lock(mdu_spec: dict, max_lines: int = 200) -> str:
    """Build scope lock text to inject into the coder's system prompt."""
    return SCOPE_LOCK_INJECTION.format(max_lines=max_lines)


def check_scope_violation(code_output: str, mdu_spec: dict) -> list[str]:
    """Static check for obvious scope violations in generated code.

    Returns list of violation descriptions (empty if clean).
    """
    violations = []
    target_files = mdu_spec.get("file_path", "")
    if isinstance(target_files, str):
        target_files = [target_files]

    lines = code_output.split("\n")
    file_sections = []
    for line in lines:
        if line.startswith("FILE: "):
            file_sections.append(line[6:].strip())

    for f in file_sections:
        if target_files and f not in target_files:
            is_related = any(
                t.rsplit("/", 1)[0] == f.rsplit("/", 1)[0]
                for t in target_files if "/" in t and "/" in f
            )
            if not is_related:
                violations.append(
                    f"File '{f}' modified but not in MDU target files: {target_files}"
                )

    code_lines = sum(
        1 for line in lines
        if line.strip() and not line.startswith("FILE:") and not line.startswith("```")
        and not line.startswith("SUMMARY:") and not line.startswith("CONCERNS:")
    )
    if code_lines > 300:
        violations.append(
            f"Code output is {code_lines} lines, exceeding reasonable MDU size"
        )

    workaround_signals = ["workaround", "hack", "temporary fix", "TODO: fix upstream"]
    for signal in workaround_signals:
        if signal.lower() in code_output.lower():
            violations.append(
                f"Potential workaround detected: found '{signal}' in code output"
            )

    return violations
