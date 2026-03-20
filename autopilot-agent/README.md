# autopilot-agent

> Multi-Agent system for automated full-cycle software development.
> 用户输入一句需求，系统自动驱动 Agent 按流程执行：需求锁定 → 架构设计 → 技术验证 → 任务拆解 → 逐单元编码 → 审查 → 验收 → 进度更新。

Built on **LangGraph** (orchestration) + **SQLAlchemy** (persistence) + **Typer** (CLI).

Upgrades the [dev-autopilot-skill v2](../dev-autopilot-skill.md) from a linear prompt protocol into a true Agent system with parallel execution, persistent state, and human-in-the-loop control.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Features](#core-features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Development Lifecycle](#development-lifecycle)
- [Engineering Mechanisms](#engineering-mechanisms)
- [Data Model](#data-model)
- [State Files](#state-files)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Architecture Decisions (ADRs)](#architecture-decisions-adrs)
- [Contributing](#contributing)

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                        CLI (Typer)                          │
│   start · resume · status · decisions · backtrack · skip    │
│   pause · change-request                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator (LangGraph StateGraph)            │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │  Phase 1  │──▶│  Phase 2  │──▶│  Phase 3  │              │
│  │Requirement│   │Architecture│  │  Spike   │              │
│  │Steps 1-3  │   │Steps 4-5  │   │ Step 6   │              │
│  └──────────┘   └──────────┘   └────┬─────┘              │
│                                       │                     │
│  ┌──────────┐   ┌──────────────────┐  │                     │
│  │  Phase 6  │◀──│    Phase 5       │◀─┘                    │
│  │  Wrapup   │   │   Execution     │                        │
│  └──────────┘   │ fan-out/fan-in  │   ┌──────────┐        │
│                  │ Coder+Reviewer  │◀──│  Phase 4  │        │
│                  └──────────────────┘   │Decompose │        │
│                                         │Steps 7-9 │        │
│  Special Nodes:                         └──────────┘        │
│  ├── human_gate (pause for user input)                      │
│  └── backtrack_router (jump to earlier phase)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Mechanisms   │ │    State     │ │    Tools     │
│              │ │              │ │              │
│CircuitBreaker│ │ SQLite + WAL │ │ FileManager  │
│ ScopeLock    │ │ 8-table ORM  │ │ CodeWriter   │
│ Backtrack    │ │ LangGraph    │ └──────────────┘
│ChangeRequest │ │ Checkpoint   │
│ Heartbeat    │ └──────────────┘
│ BugEvolution │
└──────────────┘
```

### Agent Collaboration Flow

```text
User Requirement
       │
       ▼
RequirementAgent ──┐
  (Steps 1-3)      │ locked_requirement
       │           │
       ▼           │
ArchitectAgent  ◀──┘
  (Steps 4-5)
       │  decisions[] + spike_candidates[]
       ▼
SpikeAgent
  (Step 6)  ── spike_failed? ──▶ BacktrackRouter ──▶ ArchitectAgent
       │
       ▼
DecomposerAgent
  (Steps 7-9) + CircuitBreaker
       │  execution_plan { mdus[], batches[] }
       ▼
┌──────────────────────────────────────┐
│        Parallel Executor             │
│  ┌─────────┐  ┌─────────┐  ┌─────┐ │
│  │ Coder-1 │  │ Coder-2 │  │ ... │ │
│  │Reviewer1│  │Reviewer2│  │     │ │
│  └─────────┘  └─────────┘  └─────┘ │
│     (max_parallel = 3, semaphore)    │
└──────────────────┬───────────────────┘
                   │  mdu_results[]
                   ▼
CheckpointAgent ── evolution_gate ──▶ WrapupAgent
```

---

## Core Features

| Feature | Description |
|---------|-------------|
| **Parallel MDU Execution** | LangGraph fan-out/fan-in with configurable 1-5 concurrent MDUs via asyncio semaphore |
| **Persistent State** | SQLite + WAL mode for concurrent agent writes; all state survives session interruption |
| **LangGraph Checkpointing** | Full graph state serialized after every node, enabling exact resume |
| **Circuit Breaker** | Prevents infinite task decomposition: max depth 4, max 60 MDUs, max 8 sub-items per task |
| **Scope Lock** | Prevents AI from over-expanding — each MDU has strict coding boundaries injected into prompt |
| **Backtrack Protocol** | 5 root cause categories automatically mapped to 5 backtrack targets |
| **Change Request Protocol** | Formal `/change-request` with impact analysis, risk estimation, and user approval |
| **Bug-Driven Evolution** | **HARD CONSTRAINT** — every bug triggers three-layer drill-down: fix → root cause → framework writeback |
| **Progress Heartbeat** | Automatic reporting every 10% completion or phase change |
| **Human-in-the-Loop** | 9 well-defined interaction points where the system pauses for user input |
| **Multi-Provider LLM** | OpenAI, Anthropic, and Ollama (local) supported via LangChain abstraction |

---

## Prerequisites

- **Python 3.11+** (required for `TypedDict` + `Annotated` features)
- **LLM API key** — at least one of:
  - OpenAI API key (`OPENAI_API_KEY`)
  - Anthropic API key (`ANTHROPIC_API_KEY`)
  - Local Ollama instance running on `localhost:11434`

---

## Installation

### From Source (Recommended)

```bash
cd autopilot-agent

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install in editable mode
pip install -e .

# Verify installation
autopilot --help
```

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

### Dependencies

All dependencies are managed in `pyproject.toml`:

| Package | Version | Purpose |
|---------|---------|---------|
| `langgraph` | ≥0.2.0 | Agent orchestration DAG |
| `langchain-core` | ≥0.3.0 | LLM abstraction layer |
| `langchain-openai` | ≥0.2.0 | OpenAI + Ollama provider |
| `langchain-anthropic` | ≥0.2.0 | Anthropic provider |
| `sqlalchemy` | ≥2.0.0 | ORM + database management |
| `pydantic` | ≥2.0.0 | Settings validation |
| `typer` | ≥0.12.0 | CLI framework |
| `rich` | ≥13.0.0 | Terminal formatting |
| `aiosqlite` | ≥0.20.0 | Async SQLite driver |
| `langgraph-checkpoint-sqlite` | ≥3.0.0 | Graph state checkpoint |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (required for `openai` provider) |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (required for `anthropic` provider) |
| `AUTOPILOT_MODEL` | `gpt-4o` | LLM model name |
| `AUTOPILOT_LLM_PROVIDER` | `openai` | LLM provider: `openai`, `anthropic`, or `ollama` |
| `AUTOPILOT_MAX_PARALLEL` | `3` | Max concurrent MDU execution (1-5) |
| `AUTOPILOT_PROJECT_DIR` | `.` | Target project directory |

### Example Configurations

**OpenAI (Recommended for best results):**

```bash
export OPENAI_API_KEY="sk-proj-..."
export AUTOPILOT_MODEL="gpt-4o"
export AUTOPILOT_LLM_PROVIDER="openai"
```

**Anthropic:**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export AUTOPILOT_MODEL="claude-sonnet-4-20250514"
export AUTOPILOT_LLM_PROVIDER="anthropic"
```

**Ollama (Local, no API key needed):**

```bash
export AUTOPILOT_MODEL="llama3.1:70b"
export AUTOPILOT_LLM_PROVIDER="ollama"
# Ollama must be running on localhost:11434
```

### Tunable Parameters

These are configured in `src/config/settings.py` via `Settings` / Pydantic models:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `llm.temperature` | 0.3 | 0.0 - 2.0 | LLM sampling temperature (lower = more deterministic) |
| `llm.max_tokens` | 4096 | > 0 | Maximum tokens per LLM response |
| `concurrency.max_parallel_mdus` | 3 | 1 - 5 | Parallel MDU execution slots |
| `concurrency.llm_retry_max_attempts` | 3 | ≥ 1 | Retry attempts for failed LLM calls |
| `concurrency.llm_retry_base_delay` | 1.0s | > 0 | Base delay for exponential backoff |
| `circuit_breaker.max_depth` | 4 | ≥ 1 | Max recursion depth for task decomposition |
| `circuit_breaker.max_mdu_count` | 60 | ≥ 1 | Max total number of MDUs |
| `circuit_breaker.max_sub_items` | 8 | ≥ 1 | Max sub-items per task |
| `review.max_review_rounds` | 3 | ≥ 1 | Max code review rounds before escalation |
| `heartbeat.percent_interval` | 10 | 1 - 50 | Report progress every N% completion |

---

## Quick Start

### 1. Start a New Project

```bash
autopilot start "Build a REST API for user management with JWT auth" \
  --dir ./my-api \
  --model gpt-4o \
  --parallel 3
```

The system will:
1. Create a SQLite database at `./my-api/autopilot.db`
2. Enter the **Requirement Phase** — AI will ask 3-5 clarifying questions
3. Answer the questions to lock the requirement
4. Proceed automatically through architecture → spike → decomposition → execution

### 2. Interact at Decision Points

The system pauses at **9 well-defined interaction points**:

| Interaction | When | What You Do |
|-------------|------|-------------|
| Requirement Q&A | Step 3 | Answer 3-5 multiple-choice questions about scope and boundaries |
| Architecture Confirm | Step 4 | Review and approve/adjust the proposed architecture |
| Spike Failure | Step 6 | Choose alternative approach if a technical spike fails |
| Execution Plan Confirm | Step 9 | Confirm MDU count, batch schedule, and critical path |
| Phase Acceptance | Phase boundary | Run code locally and report test results |
| Backtrack Confirm | Backtrack trigger | Confirm backtrack target and impact analysis |
| Change Request | `/change-request` | Confirm change impact and additional work |
| Review Deadlock | After 3 failed reviews | Confirm root cause classification and next action |
| Phase Acceptance Block | Phase boundary | Complete pending bug evolution writebacks |

### 3. Monitor Progress

```bash
# Rich table showing MDU status
autopilot status --dir ./my-api
```

Output example:

```text
┌───────────────────────┐
│   Project Progress    │
├────────────┬──────────┤
│ Metric     │ Value    │
├────────────┼──────────┤
│ Total MDUs │ 24       │
│ Completed  │ 18       │
│ In Progress│ 2        │
│ Pending    │ 3        │
│ Skipped    │ 0        │
│ Blocked    │ 1        │
│ Completion │ 75%      │
└────────────┴──────────┘
```

### 4. Resume After Interruption

```bash
autopilot resume --dir ./my-api
```

The system will:
1. Load checkpoint from `autopilot_checkpoint.db`
2. Display current phase, step, and completed MDU count
3. Resume from the exact graph state where it was interrupted

---

## CLI Reference

### `autopilot start`

Start a new autopilot development session.

```text
Usage: autopilot start [OPTIONS] REQUIREMENT

Arguments:
  REQUIREMENT  One-sentence project requirement [required]

Options:
  -d, --dir PATH         Target project directory [default: .]
  -m, --model TEXT       LLM model name [default: gpt-4o]
  -p, --provider TEXT    LLM provider (openai|anthropic|ollama) [default: openai]
  --parallel INTEGER     Max parallel MDUs (1-5) [default: 3]
  -v, --verbose          Enable debug logging
```

### `autopilot resume`

Resume an interrupted session from the last checkpoint.

```text
Usage: autopilot resume [OPTIONS]

Options:
  -d, --dir PATH    Project directory [default: .]
  -v, --verbose     Enable debug logging
```

### `autopilot status`

Show current project progress as a formatted table.

```text
Usage: autopilot status [OPTIONS]

Options:
  -d, --dir PATH    Project directory [default: .]
```

### `autopilot decisions`

View all Architecture Decision Records (ADRs) with spike verification status.

```text
Usage: autopilot decisions [OPTIONS]

Options:
  -d, --dir PATH    Project directory [default: .]
```

### `autopilot backtrack`

Trigger explicit backtrack to an earlier phase.

```text
Usage: autopilot backtrack [OPTIONS] REASON

Arguments:
  REASON  Reason for backtracking [required]
```

Root cause is automatically classified:

| Keywords in Reason | Classification | Backtrack Target |
|--------------------|----------------|------------------|
| requirement, 需求, spec | `REQUIREMENT` | Step 3 (Requirement Lock) |
| architecture, 架构, design | `ARCHITECTURE` | Step 4 (Architecture Design) |
| tech selection, library | `TECH_SELECTION` | Step 6 (Spike) |
| decomposition, 拆解, mdu | `DECOMPOSITION` | Step 8 (Task Refinement) |
| (anything else) | `IMPLEMENTATION` | No backtrack, retry current MDU |

### `autopilot skip`

Skip the current MDU and automatically mark downstream dependents as `blocked`.

```text
Usage: autopilot skip [OPTIONS]

Options:
  -r, --reason TEXT  Skip reason [default: "User requested skip"]
```

### `autopilot pause`

Pause execution loop and save state.

```text
Usage: autopilot pause [OPTIONS]
```

### `autopilot change-request`

Submit a formal requirement change with impact analysis.

```text
Usage: autopilot change-request [OPTIONS] DESCRIPTION

Arguments:
  DESCRIPTION  Description of the change [required]
```

---

## Development Lifecycle

The system follows a strict **6-phase lifecycle** as defined in [dev-autopilot-skill v2](../dev-autopilot-skill.md):

### Phase 1: Requirement Understanding & Locking (Steps 1-3)

**Agent:** `RequirementAgent`

1. **Step 1** — Receive raw requirement (verbatim recording)
2. **Step 2** — AI directly expands understanding (no prompt optimization layer)
3. **Step 3** — Interactive locking: AI asks 3-5 multiple-choice questions to fill gaps

**Output:** `locked_requirement` — a frozen, unambiguous requirement document

**Design rationale:** v1 used Prompt Generator → Self-Auditor → AI → Decomposer (4 steps). v2 reduces to 2 steps because the bottleneck is "user doesn't know what they want," not "prompt isn't good enough."

### Phase 2: Architecture Design (Steps 4-5)

**Agent:** `ArchitectAgent`

4. **Step 4** — Generate architecture plan with technology choices
5. **Step 5** — Record decisions as ADRs (Architecture Decision Records) in JSON format

**Output:** `architecture_plan` + `decisions[]` + `spike_candidates[]`

Each ADR contains: background, candidates, decision, tradeoffs, overturn conditions, and whether a spike is required.

### Phase 3: Technical Spike (Step 6)

**Agent:** `SpikeAgent`

6. **Step 6** — For each `spike_candidate`, design a minimal verification test, execute it, and analyze the result

**Output:** `validated_decisions[]` — all spike-required decisions are now verified or replaced

If a spike fails, the system triggers the backtrack protocol to return to architecture (Step 4).

### Phase 4: Task Decomposition (Steps 7-9)

**Agent:** `DecomposerAgent` + `CircuitBreaker`

7. **Step 7** — Decompose into task tree
8. **Step 8** — Recursively refine to MDUs (Minimum Deployable Units), enforcing circuit breaker limits
9. **Step 9** — Dependency analysis + batch scheduling + user confirmation

**Output:** `execution_plan` with `mdus[]`, `batches[]`, and dependency graph

**Circuit Breaker enforces:**
- Max recursion depth: 4
- Max total MDUs: 60
- Max sub-items per task: 8

### Phase 5: Execution Loop

**Agents:** `CoderAgent` + `ReviewerAgent` (per MDU, parallel within batch)

For each batch:
1. Fan-out: Create parallel tasks for each MDU in the batch
2. For each MDU: Compile prompt → Generate code → Scope violation check → Code review loop (max 3 rounds)
3. Fan-in: Collect all MDU results
4. Progress heartbeat

**Review loop handles three outcomes:**
- ✅ **Approved** — MDU marked complete, proceed
- 🔄 **Fix needed** — Coder receives fix instructions, re-implements (up to 3 rounds)
- ⛔ **Upstream issue** — Triggers backtrack protocol

### Phase 6: Global Wrapup

**Agent:** `CheckpointAgent` + `WrapupAgent`

1. Verify all bug evolution writebacks are complete (hard gate)
2. Generate delivery summary
3. Sync final `PROGRESS.md` and `DECISIONS.md`

---

## Engineering Mechanisms

### 1. Circuit Breaker

**File:** `src/mechanisms/circuit_breaker.py`

Prevents infinite task decomposition by enforcing hard limits:

```python
# Trips when ANY limit is exceeded
cb.check_all(depth=2, mdu_count=30, sub_items=5, task_name="auth-module")
# Returns True (safe) or False (tripped)
```

When tripped, decomposition stops immediately and the current tree is used as-is.

### 2. Scope Lock

**File:** `src/mechanisms/scope_lock.py`

Injected into every MDU's coding prompt to prevent AI over-expansion:

- Only implement what the MDU spec describes
- Do NOT refactor unrelated code
- Do NOT use workarounds for upstream issues (report them instead)
- Do NOT add features beyond the spec

Post-generation, a static check scans for workaround keywords and scope violations.

### 3. Backtrack Protocol

**File:** `src/mechanisms/backtrack.py`

5-category root cause classification → automatic backtrack target mapping:

| Root Cause | Target Step | What Happens |
|------------|-------------|--------------|
| Requirement issue | Step 3 | Re-lock requirements with user |
| Architecture issue | Step 4 | Re-design architecture |
| Tech selection issue | Step 6 | Re-run spike with alternatives |
| Decomposition issue | Step 8 | Re-refine task tree |
| Implementation issue | — | Retry current MDU with different approach |

**Trigger sources:** MDU execution, review deadlock (3+ rounds), user command, phase acceptance failure.

### 4. Change Request Protocol

**File:** `src/mechanisms/change_request.py`

Formal requirement change handling:

1. Pause execution
2. Analyze impact: affected MDUs, new MDUs needed, estimated work
3. Risk estimation based on completion percentage
4. User approval/rejection
5. Update locked requirement + execution plan

If impact exceeds 50% of MDUs, recommends restarting the project.

### 5. Progress Heartbeat

**File:** `src/mechanisms/heartbeat.py`

Automatic progress reporting:

- Fires every 10% completion
- Fires on every phase change
- Can be force-fired at any time

Format: `📍 进度心跳 | MDU {X}/{Total} | 完成度：{percent}% | 阶段：{phase} | 当前：{mdu}`

### 6. Bug-Driven Evolution (HARD CONSTRAINT)

**File:** `src/mechanisms/bug_driven_evolution.py`

**This is not optional.** Every bug discovered during development must pass through a three-layer drill-down:

**Layer 1 — Fix the Bug:**
- Locate direct cause
- Apply minimal fix
- Verify fix works

**Layer 2 — Root Cause Analysis:**

Classify into one of 6 categories:

| Category | Example | Code Target |
|----------|---------|-------------|
| `prompt_deficiency` | Agent prompt missing constraint | `src/prompts/` |
| `flow_omission` | Protocol missing check step | `src/orchestrator/` |
| `mechanism_blind_spot` | Circuit breaker doesn't cover this case | `src/mechanisms/` |
| `data_model_defect` | State schema missing field | `src/state/` |
| `dependency_gap` | MDU dependency analysis incomplete | `src/agents/decomposer.py` |
| `acceptance_gap` | Phase checkpoint missing check | `src/agents/checkpoint.py` |

**Layer 3 — Framework Evolution:**
- Update `dev-autopilot-skill.md` with new defense
- Update corresponding agent code
- Record in PROGRESS.md change log
- Check for similar patterns elsewhere (举一反三)

**Hard enforcement:** `enforce_evolution_gate()` blocks phase transitions if any `[待回写]` bugs remain unresolved.

---

## Data Model

8-table SQLAlchemy ORM with SQLite WAL mode for concurrent writes:

```text
projects
├── decisions (ADRs)
├── phases
│   └── tasks
│       └── mdus
│           └── mdu_dependencies (DAG edges)
├── backtrack_log
└── change_log
```

### Entity Details

| Table | Key Fields | Status Values |
|-------|------------|---------------|
| `projects` | name, goal, locked_requirement, architecture_plan | pending, in_progress, completed |
| `decisions` | adr_number, title, content (JSON), spike_required | decided, verified, overturned |
| `phases` | phase_number, name, checkpoint_result (JSON) | pending, in_progress, completed |
| `tasks` | task_number, name, depth_level | pending, in_progress, completed, skipped |
| `mdus` | mdu_number, description, batch_number, code_changes (JSON) | pending, in_progress, completed, skipped, blocked |
| `mdu_dependencies` | mdu_id → depends_on_mdu_id | — |
| `backtrack_log` | trigger_source, root_cause_category, backtrack_target_step | — |
| `change_log` | change_type, description, impact_scope | — |

### Database Files

| File | Purpose |
|------|---------|
| `autopilot.db` | Main project state (all 8 tables) |
| `autopilot_checkpoint.db` | LangGraph graph state checkpoint |

Both use **WAL (Write-Ahead Logging)** mode for safe concurrent reads/writes from parallel MDU execution.

---

## State Files

The system generates two Markdown state files for human readability:

### `PROGRESS.md`

Auto-generated from database state. Contains:

- Project info (name, goal, creation time)
- Global metrics (total MDUs, completed, completion %)
- Phase overview table
- Current position (phase, batch, MDU)
- Change log (backtracks, change requests, framework evolutions)

### `DECISIONS.md`

Auto-generated from `decisions` table. Contains:

- All ADRs in numbered format
- Background, candidates, decision, tradeoffs
- Overturn conditions
- Spike verification status

---

## Project Structure

```text
autopilot-agent/
├── pyproject.toml                # Package config + dependencies
├── README.md                     # This file
├── spike_test.py                 # Technical spike verification scripts
│
├── src/
│   ├── __init__.py
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py               # Typer CLI: start, resume, status, decisions,
│   │                              #   backtrack, skip, pause, change-request
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Pydantic settings: LLM, concurrency, circuit
│   │                              #   breaker, review, heartbeat configs
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite engine + session factory + WAL init
│   │   ├── models.py              # 8-table ORM: Project, Decision, Phase, Task,
│   │   │                          #   MDU, MDUDependency, BacktrackLog, ChangeLog
│   │   ├── schema.py              # LangGraph AutopilotState TypedDict with reducers
│   │   └── queries.py             # All CRUD operations (create/get/update/list)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseAgent: LLM invoke with retry + JSON parse
│   │   ├── requirement.py         # Steps 1-3: understand + lock requirement
│   │   ├── architect.py           # Steps 4-5: design architecture + record ADRs
│   │   ├── spike.py               # Step 6: check/evaluate/analyze spike results
│   │   ├── decomposer.py          # Steps 7-9: decompose + refine + dependency analysis
│   │   ├── coder.py               # MDU coding: compile prompt + generate code
│   │   ├── reviewer.py            # Code review loop with fix instructions
│   │   └── checkpoint.py          # Phase acceptance + evolution gate enforcement
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── requirement.py         # System prompts for RequirementAgent
│   │   ├── architect.py           # System prompts for ArchitectAgent
│   │   ├── spike.py               # System prompts for SpikeAgent
│   │   ├── decomposer.py          # System prompts for DecomposerAgent
│   │   ├── coder.py               # System prompts for CoderAgent (with scope lock)
│   │   ├── reviewer.py            # System prompts for ReviewerAgent (with bug evolution)
│   │   └── checkpoint.py          # System prompts for CheckpointAgent (with evolution gate)
│   │
│   ├── mechanisms/
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py     # Decomposition limits: depth, count, sub-items
│   │   ├── scope_lock.py          # MDU execution boundary enforcement
│   │   ├── backtrack.py           # 5-category root cause → 5 backtrack targets
│   │   ├── change_request.py      # Formal requirement change with impact analysis
│   │   ├── heartbeat.py           # Progress reporting on interval or phase change
│   │   └── bug_driven_evolution.py # THREE-LAYER BUG DRILL-DOWN (HARD CONSTRAINT)
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── main_graph.py          # Top-level LangGraph: 6 phases + human_gate
│   │   │                          #   + backtrack_router with conditional edges
│   │   ├── phase_graphs.py        # Phase node implementations (delegates to agents)
│   │   └── parallel.py            # Fan-out/fan-in MDU execution with semaphore
│   │
│   └── tools/
│       ├── __init__.py
│       ├── file_manager.py        # File I/O utilities (read/write/list/exists)
│       └── code_writer.py         # Code writer + PROGRESS.md/DECISIONS.md sync
│
└── tests/
    ├── __init__.py
    ├── test_state.py              # DB init, ORM CRUD, concurrent writes (10 tests)
    └── test_mechanisms.py         # All 6 mechanisms unit tests (23 tests)
```

---

## Testing

### Run All Tests

```bash
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

### Test Coverage

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_state.py` | 10 | DB init, WAL mode, Project CRUD, Phase CRUD, MDU lifecycle (create/complete/skip/block), progress summary, Decision CRUD, spike candidates, concurrent writes (3 threads × 5 MDUs), change log |
| `test_mechanisms.py` | 23 | CircuitBreaker (depth/count/sub-items/reset), ScopeLock (build/violation detection), Backtrack (classify/create/no-backtrack/target mapping), Heartbeat (interval/phase-change/force/zero), BugDrivenEvolution (full lifecycle/defer/gate/error), ChangeRequest (create/analyze/high-completion/approve) |

### Run Specific Test Classes

```bash
# State layer only
python -m pytest tests/test_state.py -v

# Single mechanism
python -m pytest tests/test_mechanisms.py::TestBugDrivenEvolution -v

# Single test
python -m pytest tests/test_mechanisms.py::TestCircuitBreaker::test_depth_limit -v
```

---

## Best Practices

### 1. Requirement Writing

**Do:**
- Provide a clear, specific one-sentence requirement
- Include the most important constraint (e.g., "with JWT auth", "using PostgreSQL")
- Be ready to answer clarifying questions

**Don't:**
- Write multi-paragraph requirements (the AI will ask for details)
- Include implementation details (that's the architecture phase's job)

**Good:** `"Build a REST API for user management with JWT authentication and role-based access control"`

**Bad:** `"I want something like a user system, maybe with login, and it should be fast, also maybe a database"`

### 2. Architecture Decisions

- **Review every ADR** at the interaction point — this is your last chance before decomposition
- **Request spikes** for any technology you're unsure about (the system will auto-spike high-risk decisions)
- **Document overturn conditions** — knowing when to change a decision is as important as making it

### 3. During Execution

- **Don't skip MDUs unless necessary** — downstream MDUs will be automatically blocked
- **Report test results honestly** at phase acceptance — the system relies on your local verification
- **Use backtrack early** — catching an architecture issue at MDU 5 is better than MDU 50
- **Let the review loop run** — the 3-round limit exists for a reason; trust the process

### 4. Bug-Driven Evolution

- **Never silently fix a bug** — always go through the three-layer drill-down
- **The `[待回写]` tag is a debt** — it must be resolved before the phase ends
- **举一反三 (generalize)** — after fixing one vulnerability, check if similar patterns exist elsewhere
- **Both doc and code must be updated** — framework changes without code changes (or vice versa) are incomplete

### 5. Session Management

- **Use `autopilot pause`** before closing your terminal — gives the system a clean save point
- **Use `autopilot resume`** in a new terminal — it will show exactly where you left off
- **Check `autopilot status`** if you lose context — it's designed for this exact scenario
- **Never manually edit `autopilot.db`** — all state changes should go through the system

### 6. Parallel Execution Tuning

| Scenario | Recommended `--parallel` |
|----------|--------------------------|
| Simple CRUD project, fast API | 3 (default) |
| Complex interdependent modules | 1-2 |
| Independent microservices | 4-5 |
| Rate-limited API (free tier) | 1 |
| Ollama on consumer hardware | 1 |

### 7. Model Selection

| Model | Strengths | Best For |
|-------|-----------|----------|
| `gpt-4o` | Best overall code quality | Complex projects, default choice |
| `gpt-4o-mini` | Fast, cost-effective | Simple projects, iteration |
| `claude-sonnet-4-20250514` | Strong reasoning, detailed review | Architecture-heavy projects |
| `llama3.1:70b` (Ollama) | Local, no API cost | Privacy-sensitive, offline work |

---

## Troubleshooting

### Common Issues

**"API key not found"**

```bash
# Check if the key is set
echo $OPENAI_API_KEY

# Set it
export OPENAI_API_KEY="sk-proj-..."
```

**"No checkpoint found" on resume**

The project hasn't been started yet, or the database was deleted. Use `autopilot start` instead.

**Review loop stuck (3+ rounds)**

This triggers **Anomaly C** automatically. The system will:
1. Pause the review loop
2. Classify the root cause
3. Ask you to confirm: backtrack or retry with different approach

**MDU blocked unexpectedly**

A dependency (upstream MDU) was skipped. Check with:

```bash
autopilot status --dir ./my-project
```

To unblock, you need to either unskip the upstream MDU or restructure the execution plan via `change-request`.

**"EVOLUTION GATE BLOCKED" at phase boundary**

You have pending bug evolution writebacks marked `[待回写]`. Complete the three-layer drill-down for each before the system allows proceeding. This is a hard constraint and cannot be bypassed.

**SQLite "database is locked"**

This shouldn't happen with WAL mode, but if it does:
1. Check for zombie processes: `lsof autopilot.db`
2. Reduce `--parallel` to 1
3. Delete `autopilot.db-wal` and `autopilot.db-shm` files, then resume

**LLM call timeouts**

The system retries with exponential backoff (1s → 2s → 4s). If all 3 attempts fail, the MDU is marked as failed. Resume to retry.

---

## Architecture Decisions (ADRs)

| ADR | Decision | Rationale | Status |
|-----|----------|-----------|--------|
| 001 | **LangGraph** as Agent framework | Native DAG support, conditional edges, checkpointing, human-in-the-loop | Verified (spike passed) |
| 002 | **LangChain Core** for LLM abstraction | Multi-provider support, structured output, async-first | Decided |
| 003 | **SQLite + SQLAlchemy 2.0** for state | Zero-config, WAL for concurrency, single-file portability | Verified (spike passed) |
| 004 | **Typer** for CLI | Type hints → CLI args, Rich integration, minimal boilerplate | Decided |
| 005 | **asyncio fan-out**, default 3 parallel | Real parallelism within LangGraph, semaphore-controlled concurrency | Verified (spike passed) |
| 006 | **pyproject.toml** for packaging | Modern Python packaging standard, `pip install -e .` | Decided |
| 007 | **8-table data model** | Normalized schema covering all v2 protocol entities and relationships | Decided |

---

## Contributing

### Adding a New Agent

1. Create prompt template in `src/prompts/your_agent.py`
2. Implement agent logic in `src/agents/your_agent.py`
3. Register the agent in `src/orchestrator/phase_graphs.py`
4. Add tests in `tests/test_your_agent.py`

### Adding a New Mechanism

1. Implement in `src/mechanisms/your_mechanism.py`
2. Integrate into relevant agents or orchestrator nodes
3. Document in `dev-autopilot-skill.md`
4. Add tests in `tests/test_mechanisms.py`

### Code Style

- Python 3.11+ type hints required
- `from __future__ import annotations` in all files
- Async-first for all agent operations
- Pydantic for all configuration
- SQLAlchemy 2.0 mapped_column style

---

## License

This project is part of the [Better-Prompt](https://github.com/1055373165/Better-Prompt) skill package.
