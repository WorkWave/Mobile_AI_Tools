---
name: mobile-ui-builder
description: Use when asked to create, generate, or build a mobile UI screen or layout from a Figma link, screenshot, image, or design spec for iOS (storyboard) or Android (XML layout). Also use when adding image/icon assets to xcassets or drawable resources.
---

# Mobile UI Builder

## Overview

Dispatch **two parallel specialized agents** — one iOS expert, one Android expert — using the `Agent` tool. Each agent handles its platform end-to-end: assets, layout generation, and validation. The orchestrator (you) only gathers inputs and synthesizes results.

Generate both platforms unless the user explicitly asks for only one.

---

## Step 1 — Gather inputs before dispatching

Collect everything both agents will need. **Stop and ask if anything is missing.**

| Input | Required by |
|---|---|
| Figma URL **or** local image/screenshot path | Both |
| iOS storyboard path (e.g. `PP.Mobile.IOS/Storyboards/`) | iOS agent |
| iOS ViewController class name (e.g. `WAIveChatVC`) | iOS agent |
| Android layout path (e.g. `PP.Mobile.Droid/Resources/layout/`) | Android agent |
| Android layout file name (e.g. `fragment_waive_chat`) | Android agent |
| xcassets path (e.g. `PP.Mobile.IOS/Resources/Images.xcassets/`) | iOS agent |
| Drawable path (e.g. `PP.Mobile.Droid/Resources/drawable/`) | Android agent |
| Asset names / icon list (if known) | Both |

### Clarify ambiguous design requirements before dispatching

Technical inputs (paths, class names) are not the only thing to clarify. **Also ask about any design elements whose content or behavior is unclear**, even if they are visible in the design.

Common cases that require clarification:

| Visible in design | Ask before assuming |
|---|---|
| Interactive elements (buttons, chips, links) | Labels, tap behavior, what message/action they trigger |
| Lists or repeating items | How many items, where data comes from |
| Conditional/stateful UI | What triggers show/hide, initial state |
| Placeholder content | Whether it is real or illustrative |

**Do not implement with assumptions.** If something is visible but its behavior or content is not specified by the user, ask. A quick question before dispatching saves a correction loop after.

---

## Step 2 — Dispatch agents in parallel

Use the `Agent` tool twice **in a single message** (parallel dispatch). Pass the filled-in prompt from `ios-agent-prompt.md` and `android-agent-prompt.md`.

```
Agent(iOS UI Expert)   ──┐
                          ├── run concurrently
Agent(Android UI Expert) ─┘
```

See `ios-agent-prompt.md` and `android-agent-prompt.md` for the exact prompt templates to fill in and send.

---

## Step 3 — Review and report

When both agents return:
1. Summarize what each agent generated (file paths, outlets/IDs, validation status)
2. Flag any unresolved issues or discrepancies between platforms
3. List any next steps (e.g. wiring outlets in code, adding localized strings)

---

## Asset format rules (pass to both agents)

- Icons, logos, UI elements → `format="svg"` (Android) / `format="pdf"` (iOS) — vectors
- Photos, raster-only images → `format="png"` (both)

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Dispatching agents sequentially | Send both in one message — they are fully independent |
| Missing VC class name or layout name | Collect before dispatching — agents will fail without them |
| PNG for icons | Instruct agents to use SVG/PDF for all icons |
| Skipping validation | Both agent prompts include validation — do not remove it |
| Agent edits the other platform's files | Each prompt scopes the agent to its platform only |
| Assuming behavior of visible design elements | Ask about labels, tap actions, and conditions before dispatching |