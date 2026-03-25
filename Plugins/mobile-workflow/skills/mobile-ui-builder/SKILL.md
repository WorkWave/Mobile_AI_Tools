---
name: mobile-ui-builder
description: Use when asked to create, generate, or build a mobile UI screen or layout from a Figma link, screenshot, image, or design spec for iOS (storyboard) or Android (XML layout). Also use when adding image/icon assets to xcassets or drawable resources.
---

# Mobile UI Builder

## Overview

Dispatch **two parallel specialized agents** — one iOS expert, one Android expert — using the `Agent` tool. Each agent handles its platform end-to-end: assets, layout generation, and validation. The orchestrator (you) only gathers inputs and synthesizes results.

---

## Step 0 — Select platforms

Before gathering any technical inputs, ask:

> "Which platform(s) do you want to generate: iOS, Android, or both?"

Only gather platform-specific inputs (storyboard path / VC class name for iOS; layout path / layout file name for Android) for the selected platform(s). Skip rows in the input table that belong to unselected platforms.

---

## Step 0b — Figma URL: fetch design context (if applicable)

If the design input is a Figma URL (`figma.com/design/…` or `figma.com/file/…`), run this step before dispatching agents.

### a) Parse the URL

- Extract `fileKey` from the path segment: `/design/{fileKey}/` or `/file/{fileKey}/`
- Extract `nodeId` from the `node-id` query parameter
- **Convert dashes to colons:** `node-id=1-2` → `nodeId="1:2"` — the API requires colon format

### b) Call `get_design_context`

```
get_design_context(
  fileKey = "<fileKey>",
  nodeId  = "<nodeId>",
  clientLanguages  = "csharp",
  clientFrameworks = "uikit,android"
)
```

Note: `clientLanguages` and `clientFrameworks` are telemetry-only — they do not change the response format. The response code is always React+Tailwind and must be translated using the mapping table below.

### c) Assess structural signal

Fall back to the image path if **both** of the following are true:
- Fewer than 2 distinct interactive or structural component types from the mapping table appear in the React output
- No flex/grid class (`flex`, `grid`, `flex-col`, `flex-row`) appears on any container element

### d) JSON path (structural signal sufficient)

1. Translate the React+Tailwind output to layout JSON using the **mapping table** below
2. Build iOS layout JSON if iOS is selected (see `server/docs/layout_schema.md` for full schema)
3. Build Android layout JSON if Android is selected (see `server/docs/layout_schema.md` for full schema)
4. Dispatch agents with `{{layout_json}}` populated and `{{figma_url}}` set to the original Figma URL

### e) Image path / fallback (structural signal insufficient)

1. The `get_design_context` response embeds a screenshot — save it to a temporary local path (e.g. `/tmp/figma_screenshot_{nodeId}.png`)
2. Dispatch agents with `{{generation_input}}` set to the temporary path, `{{figma_url}}` set to the original Figma URL, and `{{layout_json}}` empty

---

### Mapping table: React+Tailwind → Layout JSON

The response from `get_design_context` is always React+Tailwind. Use this table to map it to the platform JSON schemas.

| React / Tailwind | iOS layout JSON | Android layout JSON |
|---|---|---|
| `div` with `flex-col` | `UIStackView` axis=vertical | `LinearLayout` orientation=vertical |
| `div` with `flex-row` | `UIStackView` axis=horizontal | `LinearLayout` orientation=horizontal |
| Root wrapper `div` (screen root, no flex) | `UIScrollView` → content `UIView` | `ScrollView` → `LinearLayout` (vertical, match_parent) |
| Nested wrapper `div` (no flex) | `UIView` with constraints | `RelativeLayout` |
| `button`, `<Button>` | `UIButton` | `Button` |
| `input` (single-line) | `UITextField` | `EditText` inputType=text |
| `textarea`, multi-line input | `UITextView` | `EditText` inputType=textMultiLine |
| `<p>`, `<span>` | `UILabel` | `TextView` |
| `<h1>` | `UILabel` textStyle=largeTitle | `TextView` textAppearance=headline5 |
| `<h2>` | `UILabel` textStyle=title1 | `TextView` textAppearance=headline6 |
| `<h3>` | `UILabel` textStyle=title2 | `TextView` textAppearance=subtitle1 |
| `<h4>`–`<h6>` | `UILabel` textStyle=title3/headline/subheadline | `TextView` textAppearance=subtitle2/body1 |
| `<img>`, `<Image>` | `UIImageView` contentMode=scaleAspectFit | `ImageView` + contentDescription (required) |
| `<ScrollView>` | `UIScrollView` | `ScrollView` |
| `<Card>` | `UIView` (note cornerRadius in outlets) | `androidx.cardview.widget.CardView` |
| `text-xs` | caption | overline |
| `text-sm` | footnote | caption |
| `text-base` | body | body2 |
| `text-lg` | callout | body1 |
| `text-xl` | headline | subtitle2 |
| `text-2xl` | title2 | subtitle1 |
| `text-3xl` | title1 | h6 |
| `text-4xl`+ | largeTitle | h5/h4 |
| Hex / rgb color | hex string or system color name | hex (note: ideally `@color/` ref) |
| `gap-*` | `spacing` on UIStackView | margin on children |
| `p-*`, `px-*`, `py-*` | constraint `constant` | `padding` attribute |
| `rounded-*` | note in outlets (set layer.cornerRadius in code) | note in warnings |
| `flex-1`, `flex-grow` | UIStackView `distribution=fillEqually` | `layout_weight=1` |
| `items-center` | UIStackView `alignment=center` | `gravity=center_vertical` |
| `justify-between` | UIStackView `distribution=equalSpacing` | spacer views with `layout_weight=1` |
| `opacity-*` | `alpha` 0.0–1.0 | `alpha` attribute |

**Android constraint:** This project does NOT have ConstraintLayout or Material Components. Use only `RelativeLayout`, `LinearLayout`, `ScrollView`, `Button`, `EditText`, `ListView`, `androidx.cardview.widget.CardView`. Never emit `ConstraintLayout`, `MaterialButton`, `TextInputLayout`, or `TextInputEditText`.

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