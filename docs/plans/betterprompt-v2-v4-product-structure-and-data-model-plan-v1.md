# BetterPrompt V2-V4 Product Structure and Data Model Plan v1

## 1. Frame

This document continues from:

- `docs/plans/betterprompt-product-reframe-v2-ceo-review.md`
- `docs/plans/betterprompt-library-workbench-eng-execution-plan-v1.md`

Its purpose is to answer one question only:

- after V1 `Library + Workbench`, what exactly should `V2 / V3 / V4` mean at the product-object level and at the data-model level?

This is not an implementation PR plan.
This is the product and data decomposition for the next three layers.

## 2. Locked Assumptions

These assumptions should now be treated as fixed unless the whole roadmap changes.

### 2.1 Product Thesis

BetterPrompt is not just a prompt optimizer.

It is a personal AI workflow studio that evolves in four layers:

```text
V1  Asset Layer
V2  Workflow Asset Layer
V3  Domain Workspace Layer
V4  Freshness-Aware Agent Layer
```

### 2.2 Stable Runtime Foundation

Across V1 through V4, these two objects remain the runtime backbone:

- `prompt_sessions`
- `prompt_iterations`

They stay as execution logs, not the main user-facing product object.

### 2.3 Stable Asset Foundation

Across V1 through V4, these remain real user-owned durable objects:

- `prompt_categories`
- `prompt_assets`
- `prompt_asset_versions`

Future layers should build on them, not replace them.

### 2.4 Agent Boundary

Even in V4, BetterPrompt should stay:

- high-control
- evidence-aware
- freshness-aware
- structured

It should not become:

- a generic chatbot
- an unconstrained autonomous agent
- a trading bot

### 2.5 Wedge Lock

The first serious V4 wedge should still be:

- `Stock / Market Research`

But the schema should stay generic enough to support:

- company research
- deep research

without requiring a second rewrite.

## 3. Evolution Model

### 3.1 Product Progression

```text
V1: Prompt Library + Optimization Workbench
    User owns prompt assets and versions.

        ->

V2: Workflow Assets
    User owns reusable setup objects for repeated AI work.

        ->

V3: Domain Workspaces
    User works inside domain-native environments built from workflow assets.

        ->

V4: Freshness-Aware Agents
    User gets repeated reruns, monitored subjects, diffs, alerts, and recency signals.
```

### 3.2 Object Hierarchy by Layer

```text
Layer 1: Base Assets
  - PromptAsset
  - PromptAssetVersion

Layer 2: Workflow Assets
  - ContextPack
  - ContextPackVersion
  - EvaluationProfile
  - EvaluationProfileVersion
  - WorkflowRecipe
  - WorkflowRecipeVersion
  - RunPreset

Layer 3: Domain Objects
  - DomainWorkspace
  - WorkspaceSubject
  - ResearchSource
  - ResearchReport
  - ResearchReportVersion

Layer 4: Agent Objects
  - Watchlist
  - WatchlistItem
  - AgentMonitor
  - AgentRun
  - AgentAlert
  - FreshnessRecord

Runtime Spine:
  - PromptSession
  - PromptIteration
```

### 3.3 Cross-Version Data Rule

Use this rule throughout V2-V4:

- if the object is user-facing, durable, reusable, and revisitable, give it a first-class table
- if the object is versioned content, use `root table + version table`
- if the object is mostly launch configuration, short-lived binding, or fast-changing nested structure, keep it in `json/jsonb`
- if the field will be used for filtering, sorting, joins, or dashboards, make it a first-class column

This avoids two bad extremes:

- under-modeling everything into giant JSON blobs
- over-modeling every nested step into too many tables too early

## 4. V2: Workflow Assets

### 4.1 V2 Job To Be Done

V2 exists to stop the user from rebuilding the same analysis setup every time.

The user should be able to save not only a prompt, but also the reusable setup around the prompt:

- what context to inject
- what quality standard to evaluate against
- what run sequence to follow
- what preset to launch next time

### 4.2 V2 Product Structure

V2 should add four new first-class objects:

1. `Context Pack`
2. `Evaluation Profile`
3. `Workflow Recipe`
4. `Run Preset`

Definitions:

- `Context Pack`: reusable input bundle such as company facts, writing style, assumptions, or domain notes
- `Evaluation Profile`: reusable quality contract such as evidence quality, bearish-case completeness, or formatting rigor
- `Workflow Recipe`: reusable ordered run logic such as `generate -> evaluate -> continue`
- `Run Preset`: one-click launch bundle that binds concrete versions of prompt, context, evaluation, and workflow settings

### 4.3 V2 Information Architecture

Recommended V2 structure:

```text
Library
  ├── Prompts
  ├── Context Packs
  ├── Evaluation Profiles
  └── Workflow Recipes

Workbench
  ├── Prompt selector
  ├── Context pack selector
  ├── Evaluation profile selector
  ├── Workflow recipe selector
  ├── Run settings
  └── Save as Run Preset

Runs
  └── Session history
```

### 4.4 V2 Data Relationships

```text
User
  ├── PromptAsset
  │      └── PromptAssetVersion
  ├── ContextPack
  │      └── ContextPackVersion
  ├── EvaluationProfile
  │      └── EvaluationProfileVersion
  ├── WorkflowRecipe
  │      └── WorkflowRecipeVersion
  └── RunPreset
           └── refs current versions above

RunPreset / manual workbench setup
  -> PromptSession
       -> PromptIteration
```

### 4.5 V2 Minimal Correct Data Model

#### `context_packs`

```text
id                  uuid pk
user_id             uuid null
name                varchar(255) not null
description         text null
current_version_id  uuid null
tags_json           jsonb/text not null default '[]'
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(user_id, updated_at desc)`
- `(user_id, name)`

#### `context_pack_versions`

```text
id                  uuid pk
context_pack_id     uuid not null fk context_packs(id)
version_number      integer not null
payload_json        jsonb not null default '{}'
source_iteration_id uuid null fk prompt_iterations(id)
change_summary      text null
created_at          timestamptz not null
```

Unique and indexes:

- unique `(context_pack_id, version_number)`
- `(context_pack_id, created_at desc)`

Recommended `payload_json` shape:

```text
{
  "sections": [],
  "facts": [],
  "assumptions": [],
  "style_rules": [],
  "notes": [],
  "metadata": {}
}
```

#### `evaluation_profiles`

```text
id                  uuid pk
user_id             uuid null
name                varchar(255) not null
description         text null
current_version_id  uuid null
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(user_id, updated_at desc)`
- `(user_id, name)`

#### `evaluation_profile_versions`

```text
id                      uuid pk
evaluation_profile_id   uuid not null fk evaluation_profiles(id)
version_number          integer not null
rules_json              jsonb not null default '{}'
change_summary          text null
created_at              timestamptz not null
```

Unique and indexes:

- unique `(evaluation_profile_id, version_number)`
- `(evaluation_profile_id, created_at desc)`

Recommended `rules_json` shape:

```text
{
  "criteria": [],
  "weights": {},
  "pass_threshold": null,
  "strictness": "balanced",
  "failure_conditions": [],
  "output_requirements": {}
}
```

#### `workflow_recipes`

```text
id                  uuid pk
user_id             uuid null
name                varchar(255) not null
description         text null
domain_hint         varchar(80) null
current_version_id  uuid null
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(user_id, updated_at desc)`
- `(user_id, domain_hint, updated_at desc)`

#### `workflow_recipe_versions`

```text
id                  uuid pk
workflow_recipe_id  uuid not null fk workflow_recipes(id)
version_number      integer not null
definition_json     jsonb not null default '{}'
source_iteration_id uuid null fk prompt_iterations(id)
change_summary      text null
created_at          timestamptz not null
```

Unique and indexes:

- unique `(workflow_recipe_id, version_number)`
- `(workflow_recipe_id, created_at desc)`

Recommended `definition_json` shape:

```text
{
  "steps": [],
  "required_inputs": [],
  "default_output_schema": {},
  "supports_continue": true,
  "recommended_profile_id": null,
  "model_policy": {},
  "notes": []
}
```

#### `run_presets`

```text
id                  uuid pk
user_id             uuid null
name                varchar(255) not null
description         text null
definition_json     jsonb not null default '{}'
last_used_at        timestamptz null
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(user_id, updated_at desc)`
- `(user_id, last_used_at desc)`
- `(user_id, name)`

Recommended `definition_json` shape:

```text
{
  "prompt_asset_version_id": null,
  "context_pack_version_ids": [],
  "evaluation_profile_version_id": null,
  "workflow_recipe_version_id": null,
  "output_format": {},
  "run_settings": {}
}
```

### 4.6 V2 Runtime Schema Additions

When V2 is actually implemented, `prompt_sessions` should gain a few nullable fields:

```text
run_kind                    varchar null
run_preset_id               uuid null fk run_presets(id)
workflow_recipe_version_id  uuid null fk workflow_recipe_versions(id)
```

Why these deserve real columns:

- they are high-value query dimensions
- they will drive run history filters
- they will be used by future workspace and agent layers

### 4.7 What V2 Should Not Do

V2 should not yet introduce:

- domain workspaces
- live market data ingestion
- watchlists
- alerts
- autonomous reruns

V2 is still a user-launched system.

## 5. V3: Domain Workspaces

### 5.1 V3 Job To Be Done

V3 exists to package workflow assets into domain-native working environments.

The user should no longer feel like they are launching raw prompt machinery.
They should feel like they are operating inside a workspace built for a real task.

### 5.2 V3 Product Strategy Lock

V3 should not ship as three separate products.

Instead:

- build one generic `DomainWorkspace` substrate
- ship one first-class workspace first
- map later domains onto the same base objects

Recommended rollout order:

1. `Stock Analysis Workspace`
2. `Company Research Workspace`
3. `Deep Research Workspace`

### 5.3 V3 Core Product Objects

V3 should add these first-class objects:

1. `Domain Workspace`
2. `Workspace Subject`
3. `Research Source`
4. `Research Report`

Definitions:

- `Domain Workspace`: a single-user domain hub such as stock analysis or company research
- `Workspace Subject`: the thing being analyzed such as a ticker, company, or topic
- `Research Source`: a durable evidence input such as a URL, filing, note, transcript, or uploaded document
- `Research Report`: a user-facing saved conclusion built from one or more runs

### 5.4 V3 Information Architecture

Recommended V3 structure:

```text
Workspaces
  ├── Workspace Home
  ├── Subjects
  ├── Sources
  ├── Reports
  └── Run Panel

Library
  └── still exists as the asset source of truth

Workbench
  └── still exists as the low-level execution surface
```

Key product decision:

- `Library` does not disappear in V3
- `Domain Workspaces` sit above Library and Workbench
- a workspace consumes workflow assets; it does not replace them

### 5.5 V3 Data Relationships

```text
User
  └── DomainWorkspace
        ├── WorkspaceSubject
        ├── ResearchSource
        ├── ResearchReport
        │      └── ResearchReportVersion
        └── config_json -> refs RunPreset / WorkflowRecipe / ContextPack / EvaluationProfile

DomainWorkspace / WorkspaceSubject
  -> PromptSession
       -> PromptIteration
```

### 5.6 V3 Minimal Correct Data Model

#### `domain_workspaces`

```text
id                  uuid pk
user_id             uuid null
workspace_type      varchar(80) not null
name                varchar(255) not null
description         text null
status              varchar(40) not null default 'active'
config_json         jsonb not null default '{}'
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(user_id, workspace_type, updated_at desc)`
- `(user_id, updated_at desc)`

Recommended `config_json` shape:

```text
{
  "default_run_preset_id": null,
  "default_recipe_version_id": null,
  "default_context_pack_ids": [],
  "default_evaluation_profile_id": null,
  "layout_preferences": {},
  "domain_settings": {}
}
```

#### `workspace_subjects`

```text
id                  uuid pk
workspace_id        uuid not null fk domain_workspaces(id)
subject_type        varchar(80) not null
external_key        varchar(255) null
display_name        varchar(255) not null
metadata_json       jsonb not null default '{}'
status              varchar(40) not null default 'active'
created_at          timestamptz not null
updated_at          timestamptz not null
```

Indexes:

- `(workspace_id, updated_at desc)`
- `(workspace_id, subject_type, updated_at desc)`
- optional unique `(workspace_id, subject_type, external_key)`

Examples:

- stock workspace: `subject_type=ticker`, `external_key=AAPL`
- company workspace: `subject_type=company`, `external_key=openai`
- deep research workspace: `subject_type=topic`, `external_key` nullable

#### `research_sources`

```text
id                  uuid pk
workspace_id        uuid not null fk domain_workspaces(id)
subject_id          uuid null fk workspace_subjects(id)
source_type         varchar(40) not null
canonical_uri       varchar(2048) null
title               varchar(255) null
content_json        jsonb not null default '{}'
source_timestamp    timestamptz null
ingest_status       varchar(40) not null default 'ready'
created_at          timestamptz not null
updated_at          timestamptz not null
```

Indexes:

- `(workspace_id, subject_id, updated_at desc)`
- `(workspace_id, source_type, source_timestamp desc)`

Recommended `content_json` shape:

```text
{
  "summary": null,
  "body": null,
  "structured_fields": {},
  "attachments": [],
  "metadata": {}
}
```

#### `research_reports`

```text
id                  uuid pk
workspace_id        uuid not null fk domain_workspaces(id)
subject_id          uuid null fk workspace_subjects(id)
report_type         varchar(80) not null
title               varchar(255) not null
latest_version_id   uuid null
status              varchar(40) not null default 'active'
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(workspace_id, subject_id, updated_at desc)`
- `(workspace_id, report_type, updated_at desc)`

#### `research_report_versions`

```text
id                  uuid pk
report_id           uuid not null fk research_reports(id)
version_number      integer not null
content_json        jsonb not null default '{}'
summary_text        text null
source_session_id   uuid null fk prompt_sessions(id)
source_iteration_id uuid null fk prompt_iterations(id)
confidence_score    numeric(4,2) null
created_at          timestamptz not null
```

Unique and indexes:

- unique `(report_id, version_number)`
- `(report_id, created_at desc)`

Recommended `content_json` shape:

```text
{
  "thesis": null,
  "bull_case": [],
  "bear_case": [],
  "key_risks": [],
  "open_questions": [],
  "evidence_refs": [],
  "next_actions": []
}
```

### 5.7 V3 Runtime Schema Additions

When V3 is implemented, `prompt_sessions` should gain:

```text
domain_workspace_id   uuid null fk domain_workspaces(id)
subject_id            uuid null fk workspace_subjects(id)
run_kind              varchar null
```

Recommended `run_kind` values by this point:

```text
manual_workbench
preset_run
workspace_run
```

### 5.8 Important Naming Decision

Do not call the V3 table just `workspaces` unless team collaboration is also in scope.

Use:

- `domain_workspaces`

This avoids a future collision with:

- team/workspace membership concepts
- org-level collaboration concepts

### 5.9 What V3 Should Not Do

V3 should not yet introduce:

- scheduled autonomous reruns
- watchlists with monitoring logic
- alert feeds
- event-trigger systems
- trading actions
- team collaboration tables

V3 is domain-native, but still primarily user-driven.

## 6. V4: Freshness-Aware Agents

### 6.1 V4 Job To Be Done

V4 exists to keep the user continuously informed in a changing domain.

At this point, BetterPrompt stops being only a workspace and becomes an update engine:

- rerun when new information matters
- show what changed
- show whether information is stale
- alert the user when a tracked subject materially changes

### 6.2 V4 Product Structure

V4 should add these first-class objects:

1. `Watchlist`
2. `Agent Monitor`
3. `Agent Run`
4. `Agent Alert`
5. `Freshness Record`

Definitions:

- `Watchlist`: named set of tracked subjects inside a domain workspace
- `Agent Monitor`: rule describing when and how to rerun analysis
- `Agent Run`: one freshness-aware execution instance produced by a monitor
- `Agent Alert`: user-visible material update generated from an agent run
- `Freshness Record`: explicit recency state for sources, subjects, or reports

### 6.3 V4 Information Architecture

Recommended V4 structure inside a domain workspace:

```text
Workspace
  ├── Subjects
  ├── Watchlists
  ├── Monitors
  ├── Updates Feed
  ├── Reports
  └── Run Detail / Diff View
```

Every report and update should visibly show:

- data timestamp
- last run timestamp
- stale / aging / fresh status
- change summary

### 6.4 V4 Data Relationships

```text
DomainWorkspace
  ├── Watchlist
  │      └── WatchlistItem -> WorkspaceSubject
  ├── AgentMonitor
  │      └── AgentRun
  │             ├── refs PromptSession / PromptIteration
  │             └── AgentAlert
  └── FreshnessRecord

ResearchSource
  └── FreshnessRecord
```

### 6.5 V4 Minimal Correct Data Model

#### `watchlists`

```text
id                  uuid pk
workspace_id        uuid not null fk domain_workspaces(id)
name                varchar(255) not null
description         text null
created_at          timestamptz not null
updated_at          timestamptz not null
archived_at         timestamptz null
```

Indexes:

- `(workspace_id, updated_at desc)`
- `(workspace_id, name)`

#### `watchlist_items`

```text
id                  uuid pk
watchlist_id        uuid not null fk watchlists(id)
subject_id          uuid not null fk workspace_subjects(id)
sort_order          integer not null default 0
created_at          timestamptz not null
```

Unique and indexes:

- unique `(watchlist_id, subject_id)`
- `(watchlist_id, sort_order)`

#### `agent_monitors`

```text
id                          uuid pk
workspace_id                uuid not null fk domain_workspaces(id)
watchlist_id                uuid null fk watchlists(id)
subject_id                  uuid null fk workspace_subjects(id)
run_preset_id               uuid null fk run_presets(id)
workflow_recipe_version_id  uuid null fk workflow_recipe_versions(id)
monitor_type                varchar(40) not null
trigger_config_json         jsonb not null default '{}'
alert_policy_json           jsonb not null default '{}'
status                      varchar(40) not null default 'active'
last_run_at                 timestamptz null
next_run_at                 timestamptz null
created_at                  timestamptz not null
updated_at                  timestamptz not null
```

Indexes:

- `(workspace_id, status, next_run_at)`
- `(subject_id, status, next_run_at)`

Constraint:

- exactly one of `watchlist_id` or `subject_id` should be set in the common case

Recommended `monitor_type` values:

```text
schedule
event
hybrid
```

#### `freshness_records`

```text
id                  uuid pk
workspace_id        uuid not null fk domain_workspaces(id)
subject_id          uuid null fk workspace_subjects(id)
source_id           uuid null fk research_sources(id)
freshness_kind      varchar(40) not null
observed_at         timestamptz not null
expires_at          timestamptz null
status              varchar(40) not null
details_json        jsonb not null default '{}'
created_at          timestamptz not null
```

Indexes:

- `(workspace_id, status, observed_at desc)`
- `(source_id, observed_at desc)`
- `(subject_id, observed_at desc)`

Recommended `status` values:

```text
fresh
aging
stale
unknown
failed
```

#### `agent_runs`

```text
id                  uuid pk
monitor_id          uuid not null fk agent_monitors(id)
workspace_id        uuid not null fk domain_workspaces(id)
subject_id          uuid null fk workspace_subjects(id)
prompt_session_id   uuid null fk prompt_sessions(id)
prompt_iteration_id uuid null fk prompt_iterations(id)
previous_run_id     uuid null fk agent_runs(id)
trigger_kind        varchar(40) not null
run_status          varchar(40) not null
input_freshness_json jsonb not null default '{}'
change_summary_json jsonb not null default '{}'
conclusion_summary  text null
confidence_score    numeric(4,2) null
started_at          timestamptz not null
finished_at         timestamptz null
created_at          timestamptz not null
```

Indexes:

- `(monitor_id, started_at desc)`
- `(workspace_id, subject_id, started_at desc)`
- `(run_status, started_at desc)`

Recommended `trigger_kind` values:

```text
manual_refresh
scheduled_rerun
source_event
threshold_event
```

#### `agent_alerts`

```text
id                  uuid pk
run_id              uuid not null fk agent_runs(id)
workspace_id        uuid not null fk domain_workspaces(id)
subject_id          uuid null fk workspace_subjects(id)
severity            varchar(40) not null
title               varchar(255) not null
body_text           text not null
status              varchar(40) not null default 'unread'
delivered_at        timestamptz null
created_at          timestamptz not null
```

Indexes:

- `(workspace_id, status, created_at desc)`
- `(subject_id, created_at desc)`

### 6.6 V4 Runtime Schema Additions

When V4 is implemented, `prompt_sessions` should gain:

```text
agent_monitor_id   uuid null fk agent_monitors(id)
trigger_kind       varchar null
run_kind           varchar null
```

By V4, recommended `run_kind` values are:

```text
manual_workbench
preset_run
workspace_run
agent_run
```

### 6.7 V4 Product Rules

V4 must enforce three product rules:

1. Every update must show recency
2. Every rerun must show what changed
3. Every alert must point to evidence and a run trace

Without those three, V4 looks like an "agent" but is not trustworthy enough to matter.

### 6.8 What V4 Should Still Not Do

Even in V4, avoid:

- black-box buy/sell recommendations
- direct brokerage or trading execution
- open-ended autonomous planning without review boundaries
- too many verticals at once

## 7. Cross-Version Schema Guidance

### 7.1 Stable Forever

These patterns should remain stable:

- `root table + version table` for durable user-facing assets
- `prompt_sessions + prompt_iterations` as runtime log spine
- explicit workspace and monitor objects instead of giant generic JSON blobs

### 7.2 High-Value Query Dimensions Should Be Columns

These deserve explicit columns once introduced:

- `run_kind`
- `run_preset_id`
- `workflow_recipe_version_id`
- `domain_workspace_id`
- `subject_id`
- `agent_monitor_id`
- `trigger_kind`

These will be queried heavily in:

- history pages
- workspace timelines
- subject pages
- monitor dashboards
- alert feeds

### 7.3 Fast-Changing Nested Structures Should Stay in JSON

These should stay inside version JSON or config JSON until proven otherwise:

- recipe step internals
- evaluation rule details
- context pack nested sections
- workspace layout preferences
- monitor trigger details
- alert policy details

This keeps the schema explicit where it matters and flexible where it changes quickly.

### 7.4 Do Not Prematurely Build a Generic `assets` Table

Do not collapse all future objects into one polymorphic mega-table like:

- `assets`
- `asset_versions`

That looks elegant too early and becomes painful later because:

- prompts, context packs, evaluation profiles, reports, and monitors do not behave the same
- query patterns differ
- lifecycle and version semantics differ
- permissions and future product rules will differ

Separate root tables with shared naming patterns are the better long-term choice.

### 7.5 Do Not Prematurely Build Team Collaboration Tables

Even though older docs mention possible team/workspace directions, this roadmap should not front-load:

- organizations
- memberships
- roles
- shared libraries

The V3 workspace in this document is a single-user domain workspace, not a collaboration primitive.

## 8. Recommended Build Order After V1

The recommended order remains:

1. finish V1 `Library + Workbench`
2. build V2 workflow assets
3. build one V3 domain workspace on top of V2
4. only then build V4 freshness-aware agent behavior

Recommended domain sequence:

1. stock analysis
2. company research
3. deep research

This order matters because:

- V2 gives reusable operating building blocks
- V3 gives domain-native packaging
- V4 gives continuous value

If V4 is attempted before V2 and V3 are real, the product will become a thin "agent demo" instead of a durable system.

## 9. Final Lock

The most important structural decision is this:

- V2 should introduce reusable workflow objects
- V3 should introduce reusable domain containers
- V4 should introduce continuous monitored execution

That means the roadmap is not:

```text
prompt tool -> bigger prompt tool -> stock chatbot
```

It is:

```text
prompt asset system
-> workflow asset system
-> domain workspace system
-> freshness-aware agent system
```

That is the product line that gives BetterPrompt a real ceiling.
