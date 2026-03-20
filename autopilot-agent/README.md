# autopilot-agent

Multi-Agent system for automated full-cycle software development, built on LangGraph + SQLAlchemy + Typer.

Upgrades the [dev-autopilot-skill v2](../dev-autopilot-skill.md) from a linear prompt protocol into a true Agent system with parallel execution, persistent state, and human-in-the-loop control.

## Architecture

```
CLI (Typer)
  │
  ▼
Orchestrator (LangGraph StateGraph)
  │
  ├── Phase 1: RequirementAgent (Steps 1-3)
  ├── Phase 2: ArchitectAgent (Steps 4-5)
  ├── Phase 3: SpikeAgent (Step 6)
  ├── Phase 4: DecomposerAgent (Steps 7-9)
  ├── Phase 5: CoderAgent + ReviewerAgent (fan-out parallel)
  └── Phase 6: WrapupAgent
  │
  ├── Mechanisms: CircuitBreaker, ScopeLock, Backtrack, ChangeRequest, Heartbeat, BugDrivenEvolution
  └── State: SQLite + SQLAlchemy (WAL mode, concurrent-safe)
```

## Key Features

- **True parallel MDU execution** via LangGraph fan-out/fan-in (configurable 1-5 concurrent)
- **SQLite persistent state** with WAL mode for concurrent agent writes
- **LangGraph checkpointing** for session resume after interruption
- **Circuit breaker** prevents infinite task decomposition (depth ≤4, MDU ≤60)
- **Scope lock** prevents AI from over-expanding during coding
- **Backtrack protocol** with 5 root cause categories → 5 backtrack targets
- **Change request protocol** with impact analysis
- **Bug-driven evolution** (hard constraint) — every bug triggers three-layer drill-down: fix → root cause analysis → framework evolution writeback
- **Progress heartbeat** every 10% completion or phase change

## Installation

```bash
# Requires Python 3.11+
cd autopilot-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Set environment variables:

```bash
export OPENAI_API_KEY="sk-..."          # or ANTHROPIC_API_KEY
export AUTOPILOT_MODEL="gpt-4o"         # default
export AUTOPILOT_LLM_PROVIDER="openai"  # openai | anthropic | ollama
export AUTOPILOT_MAX_PARALLEL="3"       # 1-5
```

## Usage

```bash
# Start a new project
autopilot start "Build a REST API for user management" --dir ./my-project

# Resume interrupted session
autopilot resume --dir ./my-project

# Check progress
autopilot status --dir ./my-project

# View architecture decisions
autopilot decisions --dir ./my-project

# Control commands
autopilot backtrack "Architecture doesn't support websockets"
autopilot skip --reason "Not needed for MVP"
autopilot pause
autopilot change-request "Add OAuth2 authentication"
```

## Project Structure

```
src/
├── cli/main.py              # Typer CLI entry point
├── config/settings.py       # Pydantic settings (LLM, concurrency, limits)
├── state/
│   ├── database.py          # SQLite + SQLAlchemy connection, WAL config
│   ├── models.py            # 8-table ORM (projects, decisions, phases, tasks, mdus, ...)
│   ├── schema.py            # LangGraph AutopilotState TypedDict
│   └── queries.py           # All CRUD operations
├── agents/
│   ├── base.py              # BaseAgent with LLM retry + JSON parsing
│   ├── requirement.py       # Steps 1-3
│   ├── architect.py         # Steps 4-5
│   ├── spike.py             # Step 6
│   ├── decomposer.py        # Steps 7-9
│   ├── coder.py             # MDU coding
│   ├── reviewer.py          # Code review with max rounds
│   └── checkpoint.py        # Phase acceptance + evolution gate
├── prompts/                 # System prompts for each agent
├── mechanisms/
│   ├── circuit_breaker.py   # Decomposition limits
│   ├── scope_lock.py        # MDU execution boundaries
│   ├── backtrack.py         # 5-category root cause → backtrack targets
│   ├── change_request.py    # Formal requirement changes
│   ├── heartbeat.py         # Progress reporting
│   └── bug_driven_evolution.py  # Three-layer bug drill-down (HARD CONSTRAINT)
├── orchestrator/
│   ├── main_graph.py        # LangGraph DAG with conditional edges
│   ├── phase_graphs.py      # Phase subgraph nodes
│   └── parallel.py          # Fan-out/fan-in MDU execution
└── tools/
    ├── file_manager.py      # File I/O
    └── code_writer.py       # Code + PROGRESS.md/DECISIONS.md sync
```

## Testing

```bash
source .venv/bin/activate
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## ADRs

| ADR | Decision | Status |
|-----|----------|--------|
| 001 | LangGraph as Agent framework | Verified (spike passed) |
| 002 | LangChain Core for LLM abstraction | Decided |
| 003 | SQLite + SQLAlchemy 2.0 for state | Verified (spike passed) |
| 004 | Typer for CLI | Decided |
| 005 | asyncio + fan-out, default 3 parallel | Verified (spike passed) |
| 006 | uv + pyproject.toml for packaging | Decided |
| 007 | 8-table data model | Decided |
