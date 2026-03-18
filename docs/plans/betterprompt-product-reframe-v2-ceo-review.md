# BetterPrompt Product Reframe v2

## 1. Review Frame

This product rethink is written using the `plan-ceo-review` mindset in `SELECTIVE EXPANSION` mode.

Assumption used for this review:

- keep the current `Library + Workbench` v1 path
- do not throw away the current implementation direction
- but challenge whether the current product framing is too small for the value the system could eventually deliver

This is not a code plan. This is a product reframe.

## 2. System Audit Snapshot

### Current State

- the current working product is still a `Prompt Agent` style workbench
- the strongest existing implementation is in `generate / debug / evaluate / continue`
- the strongest new direction is `Prompt Library + Optimization Workbench`
- the repo now has:
  - a product architecture blueprint
  - a design plan for library + workbench
  - an engineering execution plan for the same scope

### Already In Flight

- the project has already started moving from a one-shot prompt page toward assetization
- PR-1 data foundation work has started to make `categories / assets / versions` real

### Key Smell

The current product still risks being framed too narrowly:

- "a better prompt editor"
- "a prompt collection site"
- "a prompt optimizer"

All three are useful, but none of them is large enough to become a truly defensible product on their own.

## 3. Step 0: Nuclear Scope Challenge

### 3.1 Premise Challenge

The most important question is:

- is the user really buying "prompt quality"?

Usually, no.

The user is buying:

- better outcomes
- reusable thinking systems
- less repeated setup
- more trustworthy AI work in changing contexts

So "prompt management" is a proxy problem.

The deeper problem is:

- users do not want to repeatedly reconstruct the same AI workflow from scratch

That is especially true in dynamic domains like:

- stock analysis
- company research
- market monitoring
- competitive intelligence
- deep technical analysis

### 3.2 What Happens If We Do Nothing

If BetterPrompt stays only as:

- a prompt library
- a prompt optimizer
- a prompt quality tool

then it likely becomes:

- useful but shallow
- easy to admire, hard to depend on
- easy to imitate
- hard to expand into a higher-value product later

The real risk is not failure to ship.
The real risk is shipping a product that users outgrow once they need live data, repeated runs, memory, and domain-specific workflows.

## 4. Existing Code Leverage

BetterPrompt already has the right seeds for something bigger:

- `Prompt Agent` already models structured execution rather than free-form chat
- `generate / debug / evaluate / continue` is already closer to a workflow engine than a chat UI
- `session + iteration` is already a run log model
- `asset + version` is already the start of reusable AI building blocks
- `Library + Workbench` already creates the right user mental model: save, reopen, refine, reuse

This means the current product should not be thrown away.

It should be reinterpreted.

## 5. Dream State Mapping

```text
CURRENT STATE
Prompt optimization tool
with the beginnings of a prompt library

        ->

THIS PLAN
Reframe BetterPrompt as a system for reusable AI work assets:
prompts first, workflows second, agents later

        ->

12-MONTH IDEAL
A personal AI operating workspace where users:
- store reusable AI assets
- run them against changing inputs
- inspect evidence and history
- evolve them into domain-specific agents
```

## 6. 10x Product Check

The 10x better version of BetterPrompt is not:

- a prettier prompt manager
- a bigger template library
- a stronger one-shot optimizer

The 10x version is:

- a personal AI workflow studio that starts with prompts and graduates into reusable domain agents

In that version, a prompt is only the first form factor.

The product eventually handles:

- prompt assets
- context packs
- evaluation rules
- saved workflows
- scheduled reruns
- freshness-aware agent outputs

## 7. Revised Product Thesis

### Old Thesis

BetterPrompt helps users collect and optimize prompts.

### Better Thesis

BetterPrompt helps users build, store, run, and evolve reusable AI work systems.

### Short Version

BetterPrompt is a personal AI workflow studio.

### Why This Matters

This framing:

- preserves the current product
- increases long-term surface area
- creates room for real agent products later
- makes the stock-analysis direction make strategic sense instead of looking like a random vertical add-on

## 8. Product Architecture by Layer

BetterPrompt should be understood as a four-layer product.

### Layer 1: Asset Layer

These are the reusable building blocks.

- prompts
- prompt versions
- categories
- tags
- context snippets
- output examples
- evaluation rubrics

This is the `Library` foundation.

### Layer 2: Execution Layer

This is the place where assets are run, inspected, and improved.

- workbench
- runs
- diagnostics
- evaluations
- iterative refinement

This is the `Workbench` foundation.

### Layer 3: Workflow Layer

This is where assets become structured workflows.

- source input + prompt + evaluation policy
- saved run presets
- domain-specific analysis kits
- repeatable operating sequences

This is the layer where BetterPrompt stops being "prompt software" and starts becoming "AI operations software."

### Layer 4: Agent Layer

This is where workflows become semi-autonomous or autonomous systems.

- rerun with fresh inputs
- monitor conditions
- update conclusions
- trigger alerts
- track changes over time

This is where stock analysis becomes a natural fit.

## 9. The Right Wedge

### Recommendation

The first serious vertical wedge should be:

- `Stock / Market Research Agent`

### Why This Wedge Works

It has all the properties that reward an agent-shaped product:

- information changes continuously
- users care about freshness
- multiple data sources must be combined
- reasoning should be repeatable, not improvised
- the user often wants updates, not just one answer

### Why This Wedge Is Better Than Generic Expansion

A generic prompt product can feel broad but weak.
A strong wedge can feel narrow but indispensable.

Stock analysis is a better proof point for BetterPrompt's future than adding more generic prompt modes.

## 10. What the Stock Agent Should Be

The stock-focused V4 should be:

- a research agent
- a monitoring agent
- a structured reasoning agent
- a freshness-aware update engine

It should not be:

- an unconstrained chatbot
- a "magic stock picker"
- a trading-execution bot
- a black-box recommendation engine

The safe and credible positioning is:

- "research-grade market intelligence assistant"

not:

- "AI that tells you what to buy"

## 11. Reframed Product Strategy

### 11.1 V1

`Prompt Library + Optimization Workbench`

Job to be done:

- help users own their reusable AI assets

### 11.2 V2

`Workflow Assets`

Add:

- context packs
- saved run presets
- evaluation profiles
- reusable workflow recipes

Job to be done:

- help users stop rebuilding the same analysis setup

### 11.3 V3

`Domain Workspaces`

Add:

- stock analysis workspace
- company research workspace
- deep research workspace

Job to be done:

- package reusable AI workflows into domain-native interfaces

### 11.4 V4

`Freshness-Aware Agents`

Add:

- rerun on fresh inputs
- tracked watchlists
- event-triggered updates
- confidence and recency markers
- change summaries between runs

Job to be done:

- keep users continuously informed in dynamic domains

## 12. Product Positioning Options

### Option A: Stay Narrow

Position BetterPrompt as:

- prompt library + optimizer

Pros:

- easy to explain
- easy to ship

Cons:

- shallow moat
- weak strategic ceiling

### Option B: Best Recommended

Position BetterPrompt as:

- personal AI workflow studio

Pros:

- preserves current roadmap
- supports future agents naturally
- makes domain verticals coherent

Cons:

- requires more disciplined messaging

### Option C: Go Full Vertical Too Early

Position BetterPrompt immediately as:

- stock AI product

Pros:

- clearer niche

Cons:

- too early
- risks locking product abstractions around one use case before the base system matures

## 13. What Changes Right Now

Even with the broader reframe, the near-term build should not explode in scope.

What changes now:

- messaging
- product thesis
- roadmap logic
- future abstraction choices

What should not change now:

- V1 execution sequence
- PR-1 / PR-2 / PR-3 / PR-4 delivery order
- decision to build `Library + Workbench` first

## 14. Immediate Product Decisions

These decisions should now be treated as locked:

- BetterPrompt is not just a prompt optimizer
- BetterPrompt should be designed as a reusable AI systems product
- `Library + Workbench` is the correct V1
- domain agents are a later layer, not the first layer
- the best future wedge is a dynamic-information domain, with stocks as the strongest candidate discussed so far

## 15. Expansion Opportunities

These are the highest-value selective expansions beyond current V1.

### Expansion 1: Context Packs

Reusable bundles of:

- company facts
- sector notes
- house style
- analytical assumptions

Why it matters:

- bridges prompt assets and domain workflows

### Expansion 2: Evaluation Profiles

Named quality standards for outputs, such as:

- bearish case completeness
- evidence quality
- scenario coverage

Why it matters:

- turns "good output" into a reusable product object

### Expansion 3: Run Presets

Saved execution bundles:

- chosen prompt
- context pack
- output format
- evaluation profile

Why it matters:

- makes repeatability real

### Expansion 4: Freshness Markers

Every output gets:

- data timestamp
- last run timestamp
- stale/not-stale indicator

Why it matters:

- absolutely necessary for market and research agents

### Expansion 5: Diff-Based Reruns

When rerunning, show:

- what changed in inputs
- what changed in conclusions
- what stayed the same

Why it matters:

- this is where agent value becomes legible

## 16. Anti-Goals

Do not do these:

- do not pivot V1 into a chat-first UI
- do not treat "agent" as a license for free-form autonomy
- do not add many verticals at once
- do not confuse a prompt library with a product moat
- do not ship stock analysis without freshness, evidence, and risk framing

## 17. Revised One-Sentence Product Definition

BetterPrompt is a personal AI workflow studio that helps users turn prompts into reusable work systems, and over time evolve those systems into domain-specific agents.

## 18. CEO Summary

The biggest product mistake available from here is to think too small.

The product you are actually building is not just:

- a prompt collector
- a prompt optimizer
- a prompt engineering helper

It is the beginning of a system where users can own durable AI work assets.

That is a much better company and a much better product.
