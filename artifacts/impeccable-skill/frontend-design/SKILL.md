---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with strong visual direction and non-generic UI craft. Use this when redesigning pages, components, apps, or product surfaces that need a memorable design point of view.
---

# Frontend Design

Use this skill to build frontend work that feels intentionally designed rather than auto-generated. Favor strong hierarchy, disciplined typography, clear interaction cues, and layouts that earn their density.

## Context Check

Before design work, confirm:

- Target audience
- Core jobs to be done
- Brand personality and tone

Look for a `Design Context` section in the current instructions first. If it is not there, read `.impeccable.md` from the project root. If the context is still missing, ask the user instead of guessing from the codebase.

## Working Style

Pick a clear design direction and commit to it:

- Define the purpose of the interface and the emotional tone
- Choose one memorable differentiator
- Match implementation complexity to the visual ambition
- Keep the result functional, accessible, and production-ready

## Core Rules

### Typography

Read `reference/typography.md`.

- Use a deliberate type system with visible contrast between roles
- Prefer a distinctive display voice plus a highly readable body voice
- Use fluid sizing sparingly; product UI should stay spatially stable
- Avoid default-looking font choices that erase personality

### Color

Read `reference/color-and-contrast.md`.

- Use tinted neutrals and a restrained accent palette
- Prefer coherent, branded surfaces over loud gradients
- Keep contrast strong without pure black or pure white
- Never rely on generic cyan, purple, or neon "AI" palettes

### Layout

Read `reference/spatial-design.md`.

- Build rhythm with varied spacing, not one repeated padding value
- Use asymmetry and directional composition when it improves hierarchy
- Flatten hierarchy where possible; not everything needs a card
- Avoid repetitive icon-heading-text grids and nested panels

### Motion

Read `reference/motion-design.md`.

- Use motion to clarify state and sequence
- Favor one strong entry choreography over many tiny flourishes
- Animate transform and opacity instead of layout properties
- Support reduced-motion preferences

### Interaction

Read `reference/interaction-design.md`.

- Make primary actions unmistakable
- Use progressive disclosure for advanced options
- Design empty, loading, and error states as part of the product
- Keep forms generous and low-pressure

### Responsive

Read `reference/responsive-design.md`.

- Start from mobile constraints and scale upward with intent
- Adapt structure for smaller screens instead of hiding key capability
- Use container-aware layouts where useful

### Writing

Read `reference/ux-writing.md`.

- Make labels direct and specific
- Avoid repeating what the heading already says
- Keep helper copy calm, useful, and concise

## Anti-Patterns

Avoid the fingerprints of generic AI UI:

- Interchangeable glow-heavy SaaS visuals
- Purple or cyan gradients used as a shortcut for "intelligence"
- Card inside card inside card
- Gray text on colored surfaces
- Large decorative icons above every section title
- Centered-everything landing-page composition for tool workflows
- Decorative charts, sparkles, and glass effects without product meaning

## Quality Bar

Run a final "AI slop" check:

- Would this feel instantly machine-made because it follows a template?
- Is there one visual choice people will remember?
- Does the hierarchy still work with real content, long text, and mobile width?

If the answer is weak, refine the direction rather than adding more decoration.
