# BetterPrompt Prompt Library + Workbench Design Plan v1

## 1. Design Objective

BetterPrompt should evolve from a single Prompt Agent workbench into a product with two clearly legible centers:

- `Prompt Library`
  - a personal prompt collection space for saving, organizing, searching, starring, and revisiting prompts
- `Optimization Workbench`
  - a focused place to generate, debug, evaluate, and continue optimizing prompts, including prompts selected from the library

The user goal is not "use an AI tool." The user goal is:

- collect prompts they trust
- organize them with nested categories
- reopen any saved prompt as a starting point
- improve it without losing version history

This plan defines the information architecture, interaction states, visual direction, responsive behavior, and accessibility needed to make that experience feel intentional instead of improvised.

## 2. Scope

This design plan covers:

- nested category browsing
- prompt library list and detail view
- prompt version history
- selecting a saved prompt inside the optimization workbench
- saving workbench output as a new asset or a new version
- desktop, tablet, and mobile interaction behavior

This plan does not cover:

- team sharing
- public marketplace
- advanced permissions
- full dark-mode polish
- prompt benchmarking across multiple models

## 3. Design Review Snapshot

- Initial design completeness rating: `4/10`
- Target after this plan: `8.5/10`

Why it started low:

- the current product has a workbench, but not a true library-first information architecture
- there is no explicit design system document in the repository
- empty, loading, and recovery states for the future library workflow are not specified
- the current UI direction risks reading as a polished demo page instead of a durable personal tool

## 4. What Already Exists

The design should reuse these existing strengths:

- a calm, professional, non-chat workbench direction
- strong emphasis on result-first reading
- clear mode distinctions for `Generate / Debug / Evaluate`
- existing button, card, toast, and result panel primitives where they fit

The design should not carry forward these weak patterns:

- landing-page-like hero treatment as the main product surface
- decorative capability chips competing with the actual job to be done
- generic "AI product" gradients and glossy cards as the primary identity
- leftover finance/stock token naming in the global style vocabulary

## 5. Product Surfaces

The v1 product should have two top-level surfaces.

```text
BetterPrompt
├── Prompt Library (default home)
│   ├── Category Tree
│   ├── Prompt List
│   └── Prompt Detail
└── Optimization Workbench
    ├── From Scratch
    └── From Saved Prompt
```

### 5.1 Default Entry

Default home should be `Prompt Library`, not the Prompt Agent hero page.

Rationale:

- this is a collection product, not only a one-shot generator
- returning users need re-entry into prior work more often than a blank slate
- the library view makes the value proposition legible in 3 seconds: "these are my prompts, organized and reusable"

### 5.2 Top Navigation

Top navigation should contain only three primary items:

- `Library`
- `Workbench`
- `Search`

If more destinations appear later, they should live in secondary menus, not the primary bar.

## 6. Information Architecture

### 6.1 Desktop Layout

Desktop should use a three-pane tool layout.

```text
+------------------+---------------------------+---------------------------+
| Category Tree    | Prompt List              | Prompt Detail             |
|                  |                           |                           |
| My Prompts       | Current category title    | Prompt title              |
|  - Writing       | Search + filters          | Metadata                  |
|  - Coding        | Sort                      | Current version content   |
|    - Review      | -----------------------   | Version timeline          |
|    - Debug       | Asset row                 | Actions                   |
|  - Research      | Asset row                 | - Open in Workbench       |
|                  | Asset row                 | - Save notes              |
| + New Category   | + New Prompt              | - Star / Move / Rename    |
+------------------+---------------------------+---------------------------+
```

The user should see, in order:

1. where they are
2. what prompts are in this bucket
3. what this selected prompt currently says

### 6.2 Workbench Layout

The workbench remains a focused creation surface, but adds explicit source context.

```text
+---------------------------+-------------------------------------------+
| Source Context            | Workbench                                 |
|                           |                                           |
| From scratch              | Input / mode / settings                   |
| or                        | Result panel                              |
| From saved prompt         | Continue actions                          |
| - Prompt name             | Save sheet trigger                        |
| - Version badge           |                                           |
| - Category breadcrumb     |                                           |
+---------------------------+-------------------------------------------+
```

The most important addition is the source context panel. If a saved prompt is being optimized, the user must always know:

- which prompt they are editing
- which version they started from
- whether the output is currently unsaved

### 6.3 Mobile Layout

Mobile should not try to preserve the three-pane layout by force.

It should become a deliberate two-step flow:

```text
Bottom Nav
├── Library
└── Workbench

Library
├── Category Drawer
├── Prompt List
└── Prompt Detail (full screen)

Workbench
├── Source pill
├── Input
├── Mode switch
└── Result
```

## 7. Core User Flows

### 7.1 First-Time User

```text
Open app
-> sees empty Library with warm explanation
-> chooses "Create first prompt" or "Import existing prompt"
-> lands in Workbench
-> generates prompt
-> Save Sheet asks: new prompt name + category
-> returns to Library with the new prompt highlighted
```

### 7.2 Returning User

```text
Open app
-> lands in Library
-> sees recent category and recent prompts
-> opens a prompt
-> reviews current version
-> clicks "Open in Workbench"
-> continues optimizing
-> saves as new version
-> returns to same prompt detail with version timeline updated
```

### 7.3 Browse-Then-Optimize

```text
Library
-> choose nested category
-> filter or search
-> select prompt
-> inspect version
-> optimize from that version
-> save back into same asset
```

## 8. Hierarchy Rules Per Surface

### 8.1 Library

Primary:

- current category name
- selected prompt title
- primary action: `Open in Workbench`

Secondary:

- search
- sort
- star
- version count

Tertiary:

- description
- creation date
- tags

### 8.2 Workbench

Primary:

- source context
- input area
- final result

Secondary:

- mode switch
- save action
- continue actions

Tertiary:

- diagnostic details
- helper hints

## 9. Interaction State Coverage

| Feature | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| Category Tree | skeleton rows in sidebar | "No categories yet" with `Create category` CTA | inline retry with preserved tree width | tree renders with current node expanded | some nodes unavailable: disabled row + retry hint |
| Prompt List | 6-row list skeleton | warm copy: "This category is empty" + `Create prompt` and `Move prompt here` | inline error card, list frame preserved | rows render with current sort and selection | search returns subset while stale results badge shows old count |
| Prompt Detail | content skeleton + version placeholders | explanation of what a saved prompt can do | detail card with `Retry` and `Back to list` | full prompt content + actions visible | current version loads, older version timeline fails independently |
| Workbench Source Picker | search field + 4 result skeletons | "No saved prompts match" + clear search | inline picker error, workbench still usable from scratch | source pill appears with name and version | source loaded but metadata pending shows subdued placeholders |
| Generate / Debug / Evaluate | current panel locks submit and shows progress copy | n/a | error banner with actionable next step | result panel scrolls to top and highlights new output | stream interrupted: keep partial output, offer `Retry from partial` |
| Save Sheet | button enters saving state, sheet remains open | first save suggests category and name | validation under fields, do not dismiss sheet | success toast + return path to asset detail | asset saved but version note failed, show non-blocking warning |
| Global Search | tokenized skeleton results grouped by type | "No prompts, categories, or versions found" + query tips | retry row inside result popover | grouped results with recent section | categories load but versions time out |

Empty-state copy should feel like guidance, not punishment. Avoid blunt phrases like "No data" or "No items found" unless followed by context and a primary action.

## 10. User Journey and Emotional Arc

| Step | User Does | User Feels | Design Support |
|---|---|---|---|
| 1 | Lands in app | Wants proof this is organized, not noisy | Library-first layout, quiet chrome, visible category structure |
| 2 | Opens a saved prompt | Needs orientation fast | clear title, breadcrumb, version badge, last-updated info |
| 3 | Enters workbench | Wants confidence they are editing the right thing | persistent source context card |
| 4 | Gets a result | Wants quick judgment: useful or not | result-first layout, strong copy action, version comparison hint |
| 5 | Saves back | Wants safety and continuity | save sheet explains new asset vs new version in plain language |
| 6 | Returns later | Wants memory, not rediscovery | recent prompts, pinned favorites, reopened category state |

Time-horizon framing:

- first 5 seconds: "This is my prompt workspace"
- first 5 minutes: "I can find, improve, and save prompts without losing context"
- long-term: "This becomes my personal prompt memory, not another disposable AI tab"

## 11. AI Slop Risk Guardrails

To prevent the product from looking like a generic AI wrapper, the design must explicitly avoid:

- a large marketing-style hero as the default app state
- floating glass cards and bright AI gradients as the main identity
- feature chips as the primary surface
- icon-heavy card grids explaining capabilities users could simply do
- chat bubbles as the default frame for structured prompt work

The preferred visual metaphor is:

- `editorial library + focused workbench`

That means:

- quiet navigation
- strong text hierarchy
- dense but breathable list/detail layouts
- one restrained accent color
- subtle dividers instead of decorative glow

## 12. Visual Direction

### 12.1 Keywords

- Quiet
- Intentional
- Durable
- Editorial
- Precise
- Tool-like, not theatrical

### 12.2 Color System

Use a warm-neutral base with a cold, restrained action accent.

Suggested tokens:

- `canvas`: `#F6F4EE`
- `panel`: `#FFFEFB`
- `panel-muted`: `#F1EEE6`
- `line-subtle`: `#DED8CB`
- `text-primary`: `#1F2730`
- `text-secondary`: `#66707C`
- `accent-primary`: `#3A67F2`
- `accent-soft`: `#EAF0FF`
- `success`: `#1E8E5A`
- `warning`: `#B7791F`
- `danger`: `#C2413D`

Rules:

- only one action accent
- error, warning, and success are semantic, not decorative
- gradients may exist only as a subtle background wash, never as the main identity

### 12.3 Typography

Use a typography system that respects both English and Chinese reading.

Suggested stack:

- UI Sans: `"MiSans", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif`
- Mono for prompt content: `"JetBrains Mono", "SF Mono", "IBM Plex Mono", monospace`

Type roles:

- Page title: 28-32px, semi-bold
- Section title: 18-20px, medium
- Body: 14-15px
- Meta labels: 11-12px uppercase or small caps only where meaningfully scannable
- Prompt content: 14px mono with comfortable line height

### 12.4 Shape and Depth

- radius: 14px for panels, 10px for controls, 999px only for small pills
- borders before shadows
- shadows soft and short-range
- no heavy glassmorphism
- no oversized neon glows

## 13. Component Vocabulary

The design system for v1 should use this vocabulary:

- `App Shell`
- `Category Tree`
- `Asset Row`
- `Detail Panel`
- `Version Timeline`
- `Source Context Card`
- `Workbench Panel`
- `Save Sheet`
- `Status Banner`
- `Toast`

Avoid inventing separate visual languages for Library and Workbench. They should feel like two rooms in the same product.

## 14. Save Behavior Design

The save interaction must be explicit and humane.

When the user saves from the workbench, the sheet should present exactly two options:

- `Save as new version`
  - use when editing an existing saved prompt
- `Save as new prompt`
  - use when the result should stand alone

The sheet must explain the difference in plain language:

- `New version keeps this prompt's history together`
- `New prompt creates a separate item in your library`

Required fields:

- prompt name
- primary category

Optional fields:

- tags
- short change note

## 15. Responsive Behavior

### 15.1 Desktop

- three panes visible
- resizable list/detail boundary is allowed
- category tree fixed-width

### 15.2 Tablet

- tree remains left
- list and detail become a master-detail split
- workbench source picker opens as a side sheet

### 15.3 Mobile

- bottom nav with `Library` and `Workbench`
- category tree moves into a drawer
- prompt detail becomes a full-screen route
- save interaction uses a bottom sheet
- version timeline is collapsed by default

Responsive behavior must be intentional. "Stack everything" is not acceptable.

## 16. Accessibility Requirements

- minimum 44x44 touch targets
- full keyboard navigation for category tree, prompt list, version timeline, and save sheet
- visible focus states on all actionable controls
- semantic landmarks:
  - `header`
  - `nav`
  - `main`
  - `aside`
- category tree should use proper tree semantics or an equivalent accessible navigation pattern
- all status changes announced via polite live regions
- prompt version actions must have explicit labels, not icon-only ambiguity
- contrast target:
  - body text at least AA
  - muted text still readable against warm neutral surfaces

## 17. Copy Direction

Tone should be:

- clear
- low-ego
- supportive
- non-marketing

Preferred copy examples:

- `Choose a saved prompt to keep refining it`
- `This category is empty. Start by creating a prompt here.`
- `Saved as version 4`
- `You are editing the current saved version`

Avoid:

- `Unlock your AI productivity`
- `Your intelligent prompt copilot`
- `Next-gen prompt engineering platform`

## 18. Explicit Design Decisions

These decisions are resolved in this plan and should not be re-litigated during implementation:

- default home is `Library`
- top navigation contains only `Library`, `Workbench`, and `Search`
- category model is `one primary category + tags`, not multi-category placement
- desktop default layout is three-pane
- mobile uses separate Library and Workbench tabs, not a squeezed desktop clone
- save flow distinguishes `new version` and `new prompt`
- visual direction is quiet editorial tool, not glossy AI landing page

## 19. NOT in Scope

- collaborative cursors or multi-user presence
- comments on prompt versions
- kanban or board view for prompts
- gallery-style public discovery feed
- theme marketplace
- advanced dark mode tuning beyond basic parity

## 20. Implementation Handoff Notes

Before implementation starts, the team should:

- add a real `DESIGN.md` that promotes these tokens and rules into a shared design system source
- rename legacy global tokens that still refer to finance/stock semantics
- retire the current landing-page hero as the default application frame
- design the library empty state before building the first list view

If implemented faithfully, this plan should make BetterPrompt feel like a durable personal workspace rather than a generic AI feature demo.
