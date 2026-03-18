# BetterPrompt Library + Workbench Engineering Execution Plan v1

## 1. Goal

This plan locks the engineering execution scope for BetterPrompt v1 around one product slice only:

- a personal `Prompt Library`
- a focused `Optimization Workbench`
- the closed loop between them

The goal is not to ship the full long-term platform. The goal is to ship the minimum production-worthy slice that lets a user:

1. create or save prompts
2. organize them with nested categories
3. reopen any saved prompt in the workbench
4. generate, debug, evaluate, and continue optimizing from that saved prompt
5. save the result back as a new prompt or a new version

## 2. Step 0: Scope Challenge

### 2.1 What Already Exists

Existing code that already solves part of the problem:

- `prompt-agent` request/response flows already exist and should be reused
- `prompt_sessions` and `prompt_iterations` already exist as the right execution-log concept
- the frontend already has a working workbench shell and stream handling
- product and database blueprints already describe `asset` and `asset_version` concepts
- the design plan already locks the user-facing IA for `Library + Workbench`

### 2.2 Minimum Change Set

The minimum complete change set is:

- add `prompt_categories`
- add `prompt_assets`
- add `prompt_asset_versions`
- persist `session + iteration` for every workbench action
- add library read/write APIs
- add library routes and pages
- allow workbench actions to optionally start from a saved asset version
- allow saving workbench output as a new asset or new version
- add tests, logging, and query/index guardrails for these flows

### 2.3 Scope Reductions Applied

To keep this execution plan engineered enough and not overbuilt, the following are explicitly removed from v1 scope:

- no `template` domain implementation
- no auth rollout
- no billing or quota system
- no team or workspace model
- no Redis, background jobs, or async pipeline for this slice
- no refactor from `/prompt-agent/*` to a fully new session-driven API surface

### 2.4 Complexity Check

If implemented as one change, this feature would touch far more than 8 files and would violate the complexity smell test.

Therefore this plan is locked as a sequence of small PRs:

- `PR-1 Data Foundation`
- `PR-2 Backend Flow Integration`
- `PR-3 Frontend Library + Workbench`
- `PR-4 Hardening`

Each PR should be reviewable on its own and should leave the system deployable.

### 2.5 Completeness Check

This plan explicitly chooses the complete version over the shortcut version:

- every user-visible flow has loading, empty, error, success, and partial-state behavior
- every backend write path has conflict and retry/error behavior
- every new flow has test coverage
- every key data path has indexing and pagination decisions

No "ship the happy path and clean up later" shortcuts are allowed in this slice.

## 3. Locked Scope

### In Scope

- nested prompt categories
- prompt asset list/detail/version history
- workbench open-from-saved-prompt
- save result as new asset
- save result as new asset version
- session + iteration persistence for workbench actions
- structured error handling for new APIs
- unit, integration, frontend, and end-to-end coverage for critical paths

### NOT in Scope

- public prompt marketplace
- shared/team libraries
- template system
- auth hardening
- usage billing
- provider routing policies beyond the current single-provider path
- background jobs for asset processing

## 4. Architecture Lock

### 4.1 System Architecture

```text
Browser
  |
  v
React App
  |
  +-- Library Routes
  |     +-- Category Tree
  |     +-- Asset List
  |     +-- Asset Detail
  |
  +-- Workbench Route
        +-- Existing Prompt Agent UI
        +-- Source Asset Context
        +-- Save Sheet
  |
  v
FastAPI App
  |
  +-- /api/v1/prompt-agent/*
  |     +-- PromptAgentService
  |     +-- PromptAgentOrchestrator
  |     +-- Session/Iteration persistence
  |
  +-- /api/v1/prompt-assets/*
  |     +-- PromptAssetService
  |     +-- Category + Asset + Version logic
  |
  +-- /api/v1/prompt-sessions/*
  |
  v
SQLAlchemy + Alembic + Postgres
  |
  +-- prompt_sessions
  +-- prompt_iterations
  +-- prompt_categories
  +-- prompt_assets
  +-- prompt_asset_versions
```

### 4.2 Architecture Decisions

- Keep `prompt-agent` endpoints and extend them. Do not replace them in v1.
- Add one new backend domain surface: `prompt_assets`.
- Keep categories inside the `prompt_assets` domain to avoid introducing a second new domain.
- Keep `session` and `iteration` as execution logs, not top-level user-facing objects.
- Treat `asset` as the user-facing object and `asset_version` as the saved version chain.

### 4.3 Why This Is the Smallest Correct Architecture

- it reuses working agent flows instead of rebuilding them
- it introduces only one new domain surface instead of `assets + templates + library + history` separately
- it avoids premature async infrastructure
- it preserves future extensibility for templates and auth without forcing them into v1

## 5. Data Model Lock

### 5.1 Existing Tables Reused

- `prompt_sessions`
- `prompt_iterations`

### 5.2 New Tables

#### `prompt_categories`

```text
id                  uuid pk
user_id             uuid null
parent_id           uuid null fk prompt_categories(id)
name                varchar(120) not null
path                varchar(1024) not null
depth               integer not null default 0
sort_order          integer not null default 0
created_at          timestamptz not null
updated_at          timestamptz not null
```

Indexes:

- `(user_id, parent_id, sort_order)`
- `(user_id, path)`

Rules:

- no category cycles
- max depth enforced at service layer
- deleting a category with children is blocked in v1

#### `prompt_assets`

```text
id                  uuid pk
user_id             uuid null
category_id         uuid null fk prompt_categories(id)
name                varchar(255) not null
description         text null
is_favorite         boolean not null default false
current_version_id  uuid null
tags_json           jsonb/text not null default '[]'
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(user_id, category_id, updated_at desc)`
- `(user_id, is_favorite, updated_at desc)`
- `(user_id, name)`

#### `prompt_asset_versions`

```text
id                      uuid pk
asset_id                uuid not null fk prompt_assets(id)
version_number          integer not null
content                 text not null
source_iteration_id     uuid null fk prompt_iterations(id)
source_asset_version_id uuid null fk prompt_asset_versions(id)
change_summary          text null
created_at              timestamptz not null
```

Indexes:

- unique `(asset_id, version_number)`
- `(asset_id, created_at desc)`

### 5.3 Current Table Changes

No schema change is required for `prompt_iterations` in v1 if the request context is persisted inside `input_payload_json` and the saved asset version points back to `source_iteration_id`.

This is the smallest correct choice.

## 6. API Lock

### 6.1 Keep Existing APIs

- `POST /api/v1/prompt-agent/generate`
- `POST /api/v1/prompt-agent/generate/stream`
- `POST /api/v1/prompt-agent/debug`
- `POST /api/v1/prompt-agent/evaluate`
- `POST /api/v1/prompt-agent/continue`
- `POST /api/v1/prompt-agent/continue/stream`

### 6.2 Extend Existing Request Contracts

Add optional fields where relevant:

- `session_id`
- `source_asset_version_id`

Rules:

- if `session_id` is absent, backend creates a session on first successful workbench action
- if `source_asset_version_id` is present, the iteration stores that provenance inside input payload metadata
- every successful workbench action returns `session_id` and `iteration_id`

### 6.3 New APIs

#### Categories

- `GET /api/v1/prompt-assets/categories/tree`
- `POST /api/v1/prompt-assets/categories`
- `PATCH /api/v1/prompt-assets/categories/{category_id}`
- `DELETE /api/v1/prompt-assets/categories/{category_id}`

#### Assets

- `GET /api/v1/prompt-assets`
- `POST /api/v1/prompt-assets`
- `GET /api/v1/prompt-assets/{asset_id}`
- `PATCH /api/v1/prompt-assets/{asset_id}`

#### Versions

- `GET /api/v1/prompt-assets/{asset_id}/versions`
- `POST /api/v1/prompt-assets/{asset_id}/versions`

### 6.4 Error Contract

The new APIs must use explicit error categories:

- `VALIDATION_ERROR`
- `NOT_FOUND`
- `CONFLICT`
- `DATABASE_ERROR`
- `PROVIDER_ERROR`
- `INTERNAL_SERVER_ERROR`

## 7. Data Flow Lock

### 7.1 Library Page Load

```text
Browser
-> GET category tree
-> GET asset list for current category
-> GET selected asset detail
-> render tree/list/detail
```

Shadow paths:

- no categories -> warm empty state
- category fetch fails -> retry card in tree pane
- asset detail missing -> list remains visible, detail pane shows recovery state

### 7.2 Open Saved Prompt in Workbench

```text
Asset Detail
-> click Open in Workbench
-> route to /workbench?source_asset_version_id=...
-> load source asset version metadata
-> render source context card
-> user submits Generate/Debug/Evaluate/Continue
```

Shadow paths:

- source version deleted -> workbench opens without source and shows warning
- metadata fetch slow -> source context skeleton

### 7.3 First Workbench Submit

```text
Workbench submit
-> validate request
-> create session if absent
-> call prompt-agent service
-> persist iteration
-> return result + iteration ref
-> render result
```

Shadow paths:

- LLM config missing -> 503, show actionable config message
- upstream provider failure -> 502, preserve input and retry affordance
- DB write fails after provider success -> return error, log provider + request ids, do not silently lose result

### 7.4 Save as New Prompt

```text
Result
-> open Save Sheet
-> choose Save as new prompt
-> validate name/category
-> create asset
-> create version 1
-> set current_version_id
-> return asset detail payload
-> route to asset detail
```

### 7.5 Save as New Version

```text
Result
-> open Save Sheet
-> choose Save as new version
-> lock target asset
-> compute next version_number
-> create asset_version
-> update asset.current_version_id
-> return updated version timeline
```

Failure path:

- concurrent write on same asset -> return 409 conflict, refresh timeline, ask user to retry

## 8. Realistic Production Failure Scenarios

| Codepath | Failure Scenario | Accounted For? | Handling |
|---|---|---|---|
| `generate/continue` | upstream provider returns 502 or malformed payload | yes | map to provider error, preserve input, show retry |
| session creation | DB unavailable after request validation | yes | return 500/database error, no partial session record |
| save new version | two saves race on same asset | yes | unique constraint + 409 retry path |
| category delete | category has children or assets | yes | block delete with validation error |
| asset detail page | current_version_id points to missing version | yes | show degraded detail pane and log integrity error |
| stream UI | SSE disconnect mid-stream | yes | retain partial output and offer retry from partial |

## 9. Code Quality Lock

### 9.1 Backend Structure

Keep the backend changes boring and explicit:

- one new router: `prompt_assets`
- one new service: `PromptAssetService`
- model files for categories, assets, asset versions
- schemas for category/asset/version API contracts

Do not add:

- repository abstraction if the service pattern remains small
- separate category service
- generic domain event bus
- template abstraction

### 9.2 Frontend Structure

Keep the frontend split to:

- `pages/library`
- `features/prompt-library`
- existing `features/prompt-agent`

Do not clone the existing workbench into a second similar feature.

### 9.3 DRY Rules

- one save sheet for both save modes
- one asset list item component
- one asset detail data hook reused by detail route and post-save refresh
- one shared error-banner pattern across library and workbench

### 9.4 Edge Cases That Must Be Explicitly Handled

- 47+ char category names
- deeply nested categories near max depth
- asset name duplicate in same category
- saving a result with empty trimmed content
- opening workbench from archived asset
- stale asset detail after new version saved from another tab
- empty search result
- partial stream result

## 10. Test Review

### 10.1 Test Diagram

```text
NEW UX
├── Library page
├── Category tree
├── Asset detail
├── Workbench source context
└── Save sheet

NEW DATA FLOWS
├── Category tree fetch
├── Asset list fetch
├── Asset detail fetch
├── Prompt-agent submit with optional source asset version
├── Save as new prompt
└── Save as new version

NEW BACKEND CODEPATHS
├── Create session on first submit
├── Persist iteration after successful result
├── Create category
├── Create asset + version 1
├── Append asset version
└── Conflict handling on version number race

NEW BRANCHES / OUTCOMES
├── Workbench from scratch vs from saved prompt
├── Save as new prompt vs save as new version
├── Category tree empty vs populated
├── Asset detail available vs missing current version
└── Full stream vs partial stream
```

### 10.2 Required Test Coverage

#### Backend Unit Tests

- category path building and cycle rejection
- save new prompt service path
- save new version service path
- version conflict handling
- session auto-create behavior
- iteration persistence payload includes source asset metadata when present

#### Backend Integration Tests

- category tree CRUD
- asset create + detail + version list
- prompt-agent generate returns `session_id` + `iteration_id`
- save result from iteration into new asset
- save result into existing asset as next version
- 404 and 409 API mappings

#### Frontend Component/Hook Tests

- library empty state
- asset detail happy/error state
- workbench source context render
- save sheet mode switch
- partial stream retry affordance

#### E2E Tests

- create category -> generate from scratch -> save new prompt -> reopen detail
- open saved prompt -> continue optimize -> save as new version
- search asset -> open detail -> open in workbench

### 10.3 QA Artifact

This execution plan itself is the primary QA input until dedicated QA automation wiring is added.

Critical paths for QA:

- first prompt from scratch
- save and reopen prompt
- optimize from saved prompt
- append version under concurrency-safe path

## 11. Performance Review

### 11.1 Query Rules

- category tree fetched once per page load
- asset list paginated, default 20
- asset list must eager-load current version metadata to avoid N+1 detail lookups
- version timeline paginated, latest 10 by default

### 11.2 Index Rules

- category tree path index
- asset list category/update index
- favorite/update index
- version unique `(asset_id, version_number)`

### 11.3 Search Rules

v1 search is boring by default:

- simple name search
- debounced client input
- server-side prefix/ILIKE search

Do not spend an innovation token on vector search or semantic retrieval here.

### 11.4 Memory and Streaming

- do not buffer unlimited version history in one payload
- do not buffer whole category subtree repeatedly on each list fetch
- SSE partial text kept in client state only for current workbench session

## 12. PR Plan

### PR-1 Data Foundation

Deliver:

- env-driven DB config
- Alembic setup
- migrations for categories/assets/versions
- SQLAlchemy models
- schemas for new APIs

Acceptance:

- migrations run clean locally
- app boots against configured DB
- empty category tree endpoint works

### PR-2 Backend Flow Integration

Deliver:

- `prompt_assets` router
- `PromptAssetService`
- prompt-agent session/iteration persistence
- save new prompt/new version flows
- structured API errors for new paths

Acceptance:

- first workbench submit returns iteration refs
- asset create/detail/version endpoints work
- save from result works end-to-end via API

### PR-3 Frontend Library + Workbench

Deliver:

- library routes and pages
- category tree/list/detail panes
- workbench source context
- save sheet
- open-from-library to workbench flow

Acceptance:

- user can save and reopen prompts
- user can optimize from a saved prompt
- library empty/error/partial states render correctly

### PR-4 Hardening

Deliver:

- backend unit/integration tests
- frontend tests
- E2E critical path coverage
- logging and request correlation
- query/index review

Acceptance:

- critical paths all covered by automated tests
- structured logs include session/iteration/asset ids where available
- no N+1 in asset list/detail core flow

## 13. Failure Modes

| Codepath | Failure Mode | Rescued? | Test? | User Sees? | Logged? |
|---|---|---|---|---|---|
| create category | invalid parent or cycle | yes | yes | inline validation | yes |
| list assets | category missing | yes | yes | empty recovery state | yes |
| generate/debug/evaluate/continue | provider unavailable | yes | yes | actionable error banner | yes |
| persist iteration | DB write fails | yes | yes | retryable request failure | yes |
| save new prompt | invalid name/category | yes | yes | save sheet field errors | yes |
| save new version | version conflict | yes | yes | conflict toast + refresh | yes |
| load asset detail | missing current version | yes | yes | degraded detail state | yes |
| stream result | interrupted stream | yes | yes | partial result + retry | yes |

Any silent failure in this table is a blocker.

## 14. What Already Exists

- existing workbench UI and stream hooks
- existing `prompt-agent` backend routes
- session and iteration data model
- design plan for `Library + Workbench`
- high-level product and DB blueprints

## 15. TODO Capture

No repository-level `TODOS.md` exists today.

Deferred items that should be captured later:

- auth and user isolation
- template domain
- usage and cost tracking
- dark mode polish
- public/share flows

## 16. Completion Summary

```text
+====================================================================+
|       ENGINEERING EXECUTION PLAN — COMPLETION SUMMARY              |
+====================================================================+
| Step 0               | scope reduced to Library + Workbench v1     |
| Architecture         | locked                                       |
| Data Model           | locked                                       |
| API Surface          | locked                                       |
| Data Flows           | locked with ASCII diagrams                   |
| Edge Cases           | explicit list included                       |
| Test Coverage        | unit/integration/frontend/E2E matrix locked  |
| Performance          | query/index/search rules locked              |
+--------------------------------------------------------------------+
| NOT in scope         | written                                      |
| What already exists  | written                                      |
| Failure modes        | written                                      |
| PR plan              | 4 PRs                                        |
| QA input             | included                                     |
+====================================================================+
```

If we follow this plan, BetterPrompt ships the smallest complete version of the product that matches the intended user workflow without wasting effort on template, billing, or team abstractions too early.
