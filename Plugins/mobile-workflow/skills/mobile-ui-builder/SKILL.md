---
name: mobile-ui-builder
description: Use when asked to create, generate, or build a mobile UI screen or layout from a Figma link, screenshot, image, or design spec for iOS (storyboard) or Android (XML layout). Also use when adding image/icon assets to xcassets or drawable resources.
---

# Mobile UI Builder

## Overview

Dispatch **two parallel specialized agents** — one iOS expert, one Android expert — using the `Agent` tool. Each agent handles its platform end-to-end: assets, layout generation, and validation. The orchestrator (you) only gathers inputs and synthesizes results.

---

## Step W — Wizard Mode (activate when no design input is provided)

**Trigger condition:** The user's request does NOT include any of the following:
- A Figma URL (`figma.com/design/…` or `figma.com/file/…`)
- A local image or screenshot path
- An explicit, detailed description of the UI to build (e.g. listing components, layout structure, or visual hierarchy)

If the trigger condition is met, run this wizard **before** Step 0. Do **not** skip to Step 0 and ask for a Figma URL — guide the user through the design definition instead.

---

### W.0 — Platform selection

Ask first with numbered choices:

> "Which platform(s) do you want to generate?
>
> 1. iOS only
> 2. Android only
> 3. Both iOS and Android"

Carry the answer as `{{platforms}}` and use it throughout the wizard and when dispatching agents — only gather platform-specific inputs (storyboard path / VC class name for iOS; layout path / layout file name for Android) for the selected platform(s).

---

### W.0b — Design reference

Ask immediately after W.0:

> "Do you have a design reference to start from?
>
> 1. Yes — I have a **Figma URL** (paste it)
> 2. Yes — I have a **screenshot or image** (paste the local path, or attach it directly in the chat)
> 3. No — I'll describe what I want step by step"

**If the user picks 1:** skip W.1–W.8 entirely. Use the Figma URL and continue from **Step 0b** of the normal flow, with `{{platforms}}` already set from W.0.

**If the user picks 2:** skip W.1–W.8 entirely. The image may arrive as:
- A **local file path** (e.g. `/Users/foo/design.png`) → pass as `{{generation_input}}`
- An **inline image attachment** in the conversation → treat it as the design input directly; no path needed

Continue from **Step 1** of the normal flow with the image as design source, and `{{platforms}}` already set from W.0.

**If the user picks 3:** continue with W.1–W.8 below.

---

### W.1 — Screen type

Ask the user to pick the screen type. Present the numbered list and wait for their answer:

> "What kind of screen do you want to create? Pick a number or describe it:
>
> 1. **List / Feed** — scrollable list of items (jobs, customers, products…)
> 2. **Detail** — read-only detail view of a single item
> 3. **Form** — data entry with fields and a save/submit action
> 4. **Chat / Messaging** — message thread with input bar
> 5. **Dashboard** — summary tiles, KPIs, or charts
> 6. **Login / Auth** — login, registration, or PIN entry
> 7. **Settings / Preferences** — grouped options and toggles
> 8. **Map** — map view with optional overlays or markers
> 9. **Other** — describe it"

---

### W.2 — Screen purpose

Ask one focused question based on their choice:

> "In one sentence: what does this screen let the user **do** or **see**?"

---

### W.3 — Key components

Based on the screen type selected in W.1, suggest a default component set and ask the user to confirm, add, or remove items.

Use this mapping for the default suggestion:

| Screen type | Default components to suggest |
|---|---|
| List / Feed | Search bar, filter chips, scrollable list rows (title + subtitle + status badge), FAB or toolbar action |
| Detail | Scrollable content area, section headers, label–value rows, action buttons (primary + secondary) |
| Form | Navigation bar with Cancel/Save, grouped input fields (text, date picker, dropdown), validation feedback |
| Chat / Messaging | Fixed header (contact name), scrollable message bubbles (sent/received), typing indicator, text input + send button |
| Dashboard | Summary cards/tiles, section headers, chart placeholder, quick-action buttons |
| Login / Auth | Logo/branding area, input fields (email + password), primary CTA button, secondary link (forgot password / register) |
| Settings / Preferences | Grouped table sections, toggle rows, disclosure rows, section footers |
| Map | Full-screen map view, search/filter bar overlay, bottom sheet for selected item detail |

Present the suggested components and ask with numbered choices:

> "Here's a default set of components for a **[screen type]** screen:
> [list from table above]
>
> What would you like to do?
>
> 1. Looks good — proceed as-is
> 2. Add one or more components
> 3. Remove one or more components
> 4. Replace the list entirely"

If the user picks 2, 3, or 4, collect the change as free text, update the component list, and confirm before continuing.

---

### W.4 — Navigation & header

Ask with numbered choices:

> "What kind of header does this screen have?
>
> 1. Standard navigation bar (title + back button)
> 2. Navigation bar with custom buttons (e.g. Cancel, Save, Edit, +) — specify which
> 3. Custom header (not a native nav bar) — describe it
> 4. No header — full-screen / edge-to-edge"

If the user picks 1, 2, or 3, follow up with: "What is the screen **title**?" (free text).

---

### W.5 — Actions & interactions

Ask:

> "What can the user **tap or interact with** on this screen? List the actions (e.g. 'tap a row to open detail', 'swipe to delete', 'tap Save to submit the form')."

---

### W.6 — Data & content

Ask:

> "What **data or content** is displayed? For example: job name, customer address, status badge, timestamp. Give me a few real field names if you have them."

---

### W.7 — Style hints (optional)

Ask with numbered choices:

> "Any style preference?
>
> 1. Match the existing app style
> 2. Custom — I'll describe it (e.g. dark background, accent color #FF6B00)
> 3. No preference"

If the user picks 2, collect the style description as free text.

---

### W.8 — Confirm and generate layout description

Synthesize the answers from W.1–W.7 into a concise layout description. Present it to the user and ask for confirmation before proceeding:

> "Here's the layout I'll generate:
>
> **Screen:** [name based on W.2]
> **Type:** [W.1 choice]
> **Structure:** [brief summary of layout hierarchy]
> **Components:** [confirmed list from W.3]
> **Header:** [W.4 answer]
> **Actions:** [W.5 answer]
> **Data fields:** [W.6 answer]
> **Style:** [W.7 answer or 'match existing app style']
>
> What would you like to do?
>
> 1. Looks good — generate the layout
> 2. Change something — tell me what"

Once confirmed, carry this layout description into Step 0 as `{{wizard_layout_description}}` and use it as the design specification in place of a Figma URL or image. Proceed with the normal flow from Step 0 onward.

**Note:** When dispatching agents in Step 2, pass `{{wizard_layout_description}}` as the `{{generation_input}}` in both agent prompts and leave `{{figma_url}}` and `{{layout_json}}` empty.

---

## Step 0 — Select platforms

**If coming from Wizard Mode (Step W):** platform selection was already captured in W.0 — skip this step and use `{{platforms}}` directly.

**If entering without the wizard** (user provided a Figma URL, image, or explicit description): ask now:

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

**Android:** Use `ConstraintLayout` for complex layouts and chat/fixed-header-footer screens. Use `RecyclerView` for scrollable lists (chat messages, item feeds) — prefer it over `ListView`. Material Components (`MaterialButton`, `TextInputLayout`, `Chip`) are available — prefer them over plain equivalents.

---

## Step 1 — iOS inputs (skip if iOS not selected)

Ask sequentially. One question at a time — do not dump all questions at once.

**1a — Storyboard path:**

> "Where should the storyboard file be created?
>
> 1. I'll type the path (e.g. `RG.Mobile.iOS/Storyboards/`)
> 2. Scan the project and suggest it for me"

If option 2: use Glob to find existing `.storyboard` files and infer the folder. Confirm with the user before proceeding.

**1b — ViewController class name:**

> "What is the **ViewController class name** for this screen? (e.g. `JobDetailVC`)"

Free text. If the user is unsure, suggest a name based on the screen purpose from W.2 or the design, and let them confirm.

**1c — xcassets path:**

> "Where is the **xcassets** folder?
>
> 1. I'll type the path (e.g. `RG.Mobile.iOS/Resources/Images.xcassets/`)
> 2. Scan the project and suggest it for me"

If option 2: use Glob to find `*.xcassets` folders and confirm.

---

## Step 2 — Android inputs (skip if Android not selected)

Ask sequentially. One question at a time.

**2a — Layout path:**

> "Where should the Android layout file be created?
>
> 1. I'll type the path (e.g. `RG.Mobile.Droid/Resources/layout/`)
> 2. Scan the project and suggest it for me"

If option 2: use Glob to find existing layout XML files and infer the folder. Confirm before proceeding.

**2b — Layout file name:**

> "What should the **layout file be named**? (e.g. `fragment_job_detail`)"

Free text. If the user is unsure, suggest a name derived from the screen purpose following the naming convention (`fragment_`, `activity_`, `dialog_`, `row_`) and let them confirm.

**2c — Drawable path:**

> "Where is the **drawable** folder?
>
> 1. I'll type the path (e.g. `RG.Mobile.Droid/Resources/drawable/`)
> 2. Scan the project and suggest it for me"

If option 2: use Glob to find existing drawable folders and confirm.

---

## Step 3 — Assets (both platforms)

Ask only if the design includes icons, logos, or images:

> "Does this screen use any icons or image assets?
>
> 1. Yes — I'll list them (names or descriptions)
> 2. Yes — extract them automatically from the Figma / image
> 3. No assets needed"

If option 1: collect as free text. If option 2: agents will extract during generation.

---

## Step 4 — Clarify ambiguous design elements

**Only ask this step if the design source is a Figma URL or image** (i.e. not coming from wizard W.1–W.8 where behavior was already defined).

Review the design and ask about anything that is **visible but behaviorally unclear**:

| Visible in design | Ask before assuming |
|---|---|
| Buttons, chips, links | Label text, tap action, what screen it navigates to |
| Lists or repeating rows | Data source, how many items, empty state |
| Conditional / stateful UI | What triggers show/hide, initial state |
| Placeholder text or images | Real content or illustrative only |

Ask all ambiguities in a **single grouped message** — do not send one question per turn. Wait for the user to answer before proceeding.

**Do not implement with assumptions.** A quick question before dispatching saves a correction loop after.

---

## Step 5 — Pre-dispatch summary and confirmation

Before dispatching agents, show a full summary and ask for confirmation:

> "Here's what I'm about to generate:
>
> **Platform(s):** [{{platforms}}]
> **Design source:** [Figma URL / image path / wizard description]
> **Screen:** [name / purpose]
>
> [If iOS selected]
> **iOS storyboard:** `[path]/[ViewController].storyboard`
> **ViewController class:** `[ViewController]`
> **xcassets:** `[path]`
>
> [If Android selected]
> **Android layout:** `[path]/[layout_name].xml`
> **Drawable:** `[path]`
>
> **Assets:** [list or 'none']
>
> Ready to generate?
>
> 1. Yes — dispatch agents now
> 2. No — I need to change something"

If option 2: ask what to change, update the relevant input, and re-show the summary.

---

## Step 6 — Dispatch agents in parallel

Use the `Agent` tool twice **in a single message** (parallel dispatch). Pass the filled-in prompt from `ios-agent-prompt.md` and `android-agent-prompt.md`.

```
Agent(iOS UI Expert)   ──┐
                          ├── run concurrently
Agent(Android UI Expert) ─┘
```

See `ios-agent-prompt.md` and `android-agent-prompt.md` for the exact prompt templates to fill in and send.

---

## Step 7 — Review and report

When both agents return, present the results as a structured summary:

> "**Generation complete.**
>
> [If iOS]
> **iOS**
> - Storyboard: `[file path]`
> - Outlets: [list]
> - Validation: ✅ passed / ⚠️ [issues]
>
> [If Android]
> **Android**
> - Layout: `[file path]`
> - View IDs: [list]
> - Validation: ✅ passed / ⚠️ [issues]
>
> **Next steps:**
> [numbered list — e.g. wire outlets in code, add localized strings, implement ViewModel bindings]
>
> What would you like to do?
>
> 1. Done — everything looks good
> 2. Fix a reported issue
> 3. Adjust the layout and regenerate"

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