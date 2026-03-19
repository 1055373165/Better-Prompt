# Better Prompt

Prompt engineering knowledge base and product prototype for building stronger prompts with a practical workflow.

`betterprompt/` is the active app in this repository: a Prompt Agent workspace with a React frontend, a FastAPI backend, and a growing set of product and architecture docs. The rest of the repo contains prompt-writing references, playbooks, and design notes that informed the product direction.

## Why This Repo Exists

- Turn vague prompt ideas into reusable, high-quality prompts.
- Provide a structured workflow for `Generate`, `Debug`, `Evaluate`, and iterative refinement.
- Keep prompt engineering guidance close to a working product, instead of splitting docs and implementation across different repos.

## Highlights

- React + Vite frontend for a workspace-style Prompt Agent UI.
- FastAPI backend with rule-based diagnosis and real LLM-backed `generate`.
- DeepSeek-ready OpenAI-compatible model integration.
- Prompt engineering references, playbooks, and product planning docs in one place.

## Repository Layout

```text
better-prompt/
├── betterprompt/
│   ├── backend/               # FastAPI API, prompt orchestration, LLM integration
│   ├── frontend/              # React + Vite Prompt Agent UI
│   ├── docs/                  # Product docs, milestones, architecture notes
│   └── README.md              # Subproject-specific notes
├── docs/                      # Planning and architecture drafts
├── prompt-*.md                # Prompt engineering references and playbooks
├── howtowritepromptv*.md      # Writing guidance iterations
└── SKILL_README.md            # Skill-oriented repo guidance
```

## Product Snapshot

The current product prototype focuses on one workflow:

1. `Generate`: convert a vague request into a structured prompt.
2. `Debug`: analyze a weak prompt and repair missing control layers.
3. `Evaluate`: score prompt or output quality across multiple dimensions.
4. `Continue`: iterate on the current result with targeted refinement goals.

## Architecture

```mermaid
flowchart LR
    UI["React Frontend\nPrompt Agent Workspace"] --> API["FastAPI Backend"]
    API --> ORCH["Prompt Orchestrator"]
    ORCH --> RULES["Task Understanding\nDiagnosis\nModule Routing"]
    ORCH --> LLM["OpenAI-Compatible LLM Client\n(DeepSeek)"]
    ORCH --> RESULT["Structured Response"]
```

## Quick Start

### Prerequisites

- Python `3.11+`
- Node.js `18+`
- npm

### 1. Backend Setup

```bash
cd betterprompt/backend
uv venv .venv
.venv/bin/pip install -e .
cp .env.example .env
```

Then edit `.env` and set at least:

```bash
BETTERPROMPT_LLM_API_KEY=your-deepseek-api-key
BETTERPROMPT_LLM_MODEL=deepseek-chat
BETTERPROMPT_LLM_BASE_URL=https://api.deepseek.com
```

Start the API:

```bash
cd betterprompt/backend
.venv/bin/alembic -c alembic.ini upgrade head
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend now auto-loads `betterprompt/backend/.env`, so `--env-file` is no longer required for normal local development.
If you do not set `BETTERPROMPT_DATABASE_URL`, the default SQLite database lives at `betterprompt/backend/betterprompt.db`.

### 2. Frontend Setup

```bash
cd betterprompt/frontend
npm install
npm run dev
```

By default the frontend talks to `/api/v1`. During local development, Vite proxies `/api` to `http://127.0.0.1:8000`; when you use `./dev` or `./scripts/betterprompt-dev.sh`, the proxy target follows the backend port selected by the script.

### 3. One-Command Dev Workflow

If you want a single command to bring both services up or down:

```bash
./dev up
./dev down
```

This root shortcut forwards to the full script below:

```bash
./scripts/betterprompt-dev.sh start
./scripts/betterprompt-dev.sh stop
```

The script also supports:

```bash
./dev restart
./dev status
./dev ports
./dev logs
```

Equivalent direct script commands:

```bash
./scripts/betterprompt-dev.sh restart
./scripts/betterprompt-dev.sh status
./scripts/betterprompt-dev.sh ports
./scripts/betterprompt-dev.sh logs
```

If you prefer a service-style entrypoint, the project now also includes:

```bash
./service start
./service stop
./service restart
./service status
./service ports
./service logs
```

It starts:

- FastAPI backend on `127.0.0.1:8000`
- Vite frontend on `127.0.0.1:5173`

If `8000` or `5173` is already occupied, the script automatically picks the next available port instead of failing. Runtime logs are written to `betterprompt/.run/logs/`, and the selected ports are recorded in `betterprompt/.run/dev-ports.env`. The script expects backend dependencies, frontend dependencies, and `betterprompt/backend/.env` to be ready first.
Both `./scripts/betterprompt-dev.sh start` and `./service start` now run backend migrations before starting the API, so the local stack fails earlier instead of surfacing missing-table errors at runtime.

### 4. Open the App

- Frontend: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Backend health: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- FastAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Environment Variables

### Backend

- `BETTERPROMPT_LLM_API_KEY`: required
- `BETTERPROMPT_LLM_MODEL`: required
- `BETTERPROMPT_LLM_BASE_URL`: optional, defaults to OpenAI; use `https://api.deepseek.com` for DeepSeek
- `BETTERPROMPT_LLM_ENDPOINT`: optional, defaults to `chat/completions`
- `BETTERPROMPT_LLM_TIMEOUT_SECONDS`: optional, defaults to `120`
- `BETTERPROMPT_LLM_TEMPERATURE`: optional, defaults to `0.3`
- `BETTERPROMPT_ALLOW_TEMPLATE_FALLBACK`: optional, only enable if you want the old local-template behavior when LLM config is missing

## API Overview

Core endpoints:

- `POST /api/v1/prompt-agent/generate`
- `POST /api/v1/prompt-agent/debug`
- `POST /api/v1/prompt-agent/evaluate`
- `POST /api/v1/prompt-agent/continue`
- `GET /api/v1/health`

`generate` now returns which backend produced the result:

- `generation_backend: "llm"` when a real model was used
- `generation_backend: "template"` when explicit fallback is enabled

## Verification

- Backend unit tests: `cd betterprompt/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_*.py'`
- Backend syntax smoke: `cd betterprompt/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m compileall app tests`
- Unified acceptance smoke: `betterprompt/backend/.venv/bin/python scripts/verify_acceptance_stack.py`
- Full-stack V2 smoke: `betterprompt/backend/.venv/bin/python scripts/verify_v2_stack.py`
- Full-stack V3 smoke: `betterprompt/backend/.venv/bin/python scripts/verify_v3_stack.py`
- V4 backend contracts smoke: `betterprompt/backend/.venv/bin/python scripts/verify_v4_backend_contracts.py`
- Browser live-stack smoke: `betterprompt/backend/.venv/bin/python scripts/verify_browser_live_stack.py`
- Frontend unit tests: `cd betterprompt/frontend && npm test`
- Frontend typecheck: `cd betterprompt/frontend && ./node_modules/.bin/tsc -p tsconfig.json --pretty false`
- Frontend build smoke: `cd betterprompt/frontend && ./node_modules/.bin/vite build --outDir /tmp/betterprompt-frontend-smoke`

## Security Notes

- Real secrets belong in `.env`, not `.env.example`.
- `.gitignore` is configured to keep `.env` files out of version control while preserving `*.env.example`.
- If a real API key ever lands in a tracked file or commit history, rotate it immediately.

## Docs Worth Reading

- [Project analysis and frontend fix notes](betterprompt/docs/project-analysis-and-frontend-style-fix.md)
- [Prompt Agent architecture blueprint](docs/plans/betterprompt-product-architecture-blueprint-v1.md)
- [Prompt product frontend spec](docs/plans/prompt-product-frontend-spec.md)
- [Prompt engineering quick reference](prompt-playbook-quick-reference.md)

## Roadmap

- `V2`: workflow assets, run presets, session provenance, Library, Workbench, and Sessions are live, and the local stack now has a reusable full-stack verification script.
- `V3`: workspace schema foundation, backend CRUD, the first workspace shell, and a reusable V3 full-stack verification script are live. `Workspaces`, `Workbench`, and `Sessions` now share workspace-scoped provenance through `domain_workspace_id / subject_id`.
- `V4`: schema foundation, backend contracts, and the first manual runtime trigger path are now live for `watchlists / agent_monitors / agent_runs / agent_alerts / freshness_records`. Preset-backed monitor triggers now execute through `prompt-agent`, fill `agent_run` status plus `prompt_session / prompt_iteration` provenance, and ship with a reusable HTTP verification script. The next step is broader runtime orchestration such as scheduler/freshness/alert production, when that work is unblocked.
- Keep improving docs, onboarding, and local developer ergonomics as the product surface grows.

## Contributing

The repo is still evolving quickly, so the easiest way to contribute is:

1. Read the docs in `betterprompt/docs/` and `docs/plans/`.
2. Run the app locally.
3. Open focused PRs that improve either product quality or prompt quality.

## Acknowledgements

This README structure is informed by common GitHub open-source conventions:

- Clear project overview first
- Fast local setup
- Explicit environment configuration
- API and architecture summary
- Security and roadmap sections for collaborators
