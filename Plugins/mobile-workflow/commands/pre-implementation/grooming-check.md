# /grooming-check — Pre-Grooming Preparation

Pre-grooming preparation tool. Given a Jira story number, pulls the story
and any linked Figma design, inspects the local codebase where available,
and produces a grooming preparation package as a `.docx` file saved locally.

Run this **before** a grooming session to surface technical questions,
estimate complexity, and identify gaps in the story before the meeting.

**Usage:** `/grooming-check [story-number]`
**Example:** `/grooming-check PPM-1234`

---

## Step 1 — Collect Story Number

If the story number was not provided at invocation, ask the user for it now.

Use the Atlassian MCP server to fetch the full story (title, description, AC, labels, status, issue type).

---

## Step 1a — Detect Issue Type

After fetching the issue, check its `issuetype` field:

**If the issue type is "Epic":**
- Switch to **Epic Mode** (see Step 1b below)
- Do NOT continue with the single-story flow

**If the issue type is a story, task, or sub-task:**
- Continue with the single-story flow
- Proceed to Step 1c to look for a parent epic

---

## Step 1b — Epic Mode

When the input issue is an Epic, run a grooming check for the epic itself and all of its child stories.

1. **Fetch all child stories** of the epic using `searchJiraIssuesUsingJql` with query: `"Epic Link" = [epic-key] OR parent = [epic-key]`
2. **Announce the plan** to the user: list the epic key + title and all child story keys + titles found. Confirm before proceeding.
3. **For each item (epic + each child story), run the full grooming check flow** (Steps 2–8) independently:
   - Produce a separate `.docx` for each: `docs/pre-grooming-check/[story-number].docx`
   - At the end of each, continue to the next without waiting for user input
4. **After all individual docs are generated**, produce a **combined Epic Summary doc** at `docs/pre-grooming-check/[epic-key]-SUMMARY.docx` that includes:
   - Epic title and description
   - A table of all child stories with: key, title, suggested story point estimate, and one-line tech summary
   - Aggregate questions for grooming that apply across multiple stories
   - Overall complexity assessment and whether any stories should be broken down further

After completing Epic Mode, skip the remainder of Step 1 and proceed directly to Step 8d.

---

## Step 1c — Check for Parent Epic (Story Mode)

After fetching a non-epic issue, check whether it belongs to a parent epic:

- Look for an `Epic Link`, `parent`, or `customfield_*` epic field in the story payload
- If a parent epic is found:
  1. Fetch the epic using `getJiraIssue` — capture its title, description, and goal
  2. Fetch all sibling stories in the epic using `searchJiraIssuesUsingJql`: `"Epic Link" = [epic-key] OR parent = [epic-key]`
  3. For each sibling story (excluding the current story), capture: key, summary, status
  4. Use this context throughout the analysis to:
     - Understand the broader goal the current story fits into
     - Identify patterns or shared work across sibling stories
     - Surface questions about scope overlap or dependencies
  5. Include an **Epic Context** section in the output (see Step 8b)
- If no parent epic is found: note "No parent epic found" and continue

---

## Step 2 — Pull Figma Design

If a Figma URL exists in the story, use the Figma MCP server to pull design details.
If no link exists, flag it as missing and continue — do not stop.

---

## Step 3 — Check Repo Freshness

Before inspecting any local paths, check when each relevant repo was last pulled.

For the mobile project root, Mobile.core, and the mobile API directory (if path is known), run:
```
git -C <path> log -1 --format="%ar" FETCH_HEAD
```

If any repo's last pull was more than 1 day ago (or FETCH_HEAD does not exist), surface a warning and ask the user:
> "The [project/core/api] repo was last pulled [X]. Would you like to pull before continuing, or proceed with the current state?"

- If user chooses to pull: run `git -C <path> pull` for the affected repo(s) and confirm success before continuing
- If user chooses to skip: note the last-pull date in the output so the reader is aware the analysis may be stale

Continue to the next step regardless of the user's choice.

---

## Step 4 — Locate Project Paths

**Mobile API directory:**
- Check CLAUDE.md for the path
- If not found: ask the user
- If user provides a path and the directory exists: inspect it
- If user provides no path or directory does not exist locally: skip inspection — describe what endpoints would likely be needed based on story content instead

**Mobile.core:**
- Always look at the solution root for a `Mobile.core` project
- If not found: ask the user

---

## Step 5 — Pull Linked Items

Using the Atlassian MCP, fetch all items linked to the story (sub-tasks, blockers, related issues, epics, etc.).
- Use `getJiraIssueRemoteIssueLinks` and any inward/outward issue links returned in the story payload
- For each linked item, capture: key, link type (e.g. "blocks", "is blocked by", "relates to", "sub-task of"), summary, and status
- Include the full list in the output even if empty (say "No linked items found")

---

## Step 6 — Completeness Check

Check for required story components. Flag any that are missing with ⚠️ but do not stop — continue to analysis regardless.

Required components:
- Description present and non-empty
- Acceptance criteria present and non-empty
- AC covers all scenarios described in the description
- Figma design linked (flag if missing — note whether a design is likely needed based on the story type)

---

## Step 7 — Analysis

Produce the following for each area:

**Story Point Estimate**
Suggest a story point estimate with reasoning.
Scale: 1=trivial, 2=small, 3=medium, 5=large, 8=needs breakdown.
Flag if the story should be broken down before estimating.

**API Changes Needed**

If API directory is available locally:
- Identify existing endpoints that cover the story's needs
- Identify endpoints that partially cover the need
- Identify net new endpoints needed
- Format: "Existing / Partial — X exists but Y missing / Net new needed"

If API directory is not available locally:
- Describe what API endpoints would likely be needed based on story content
- Clearly note that the API directory was not available for inspection

**Core Changes Needed**
Inspect Mobile.core at the solution root.
- Identify existing classes, services, or utilities that can be reused
- Identify new Mobile.core additions that would be needed
- Format: "Existing coverage / Partial — X exists but Y needed / Net new needed"

**Multi-Product Consideration**
Unless the story description explicitly states cross-product usage, treat this as an open question for grooming rather than an assertion.
- If explicitly stated: flag which products are affected, note that shared logic should live in Mobile.core
- If not explicitly stated: flag as an open question for grooming

**Tech Implementation Overview**
High-level (2-4 sentence) summary of what layers or areas of the app are likely touched — e.g. UI, API, core/shared logic, data layer.
Stay conceptual; do not reference specific files or class names.

**Product Questions for Grooming**
Specific questions the engineer should raise with the product manager.
Focus on: ambiguous AC, missing edge cases, unclear scope, assumptions the tech overview had to make, multi-product open question if applicable, and any Figma design gaps.

**AC Completeness**
List scenarios described in the story that are not covered by AC.
If AC is complete, say so explicitly.

---

## Step 8 — Generate .docx and Save Locally

### 8a — Ensure output directory exists

Create the output directory if it does not already exist:

```bash
mkdir -p docs/pre-grooming-check
```

### 8b — Write the markdown file

Write the full report content to a temporary markdown file at `/tmp/grooming-check-[story-number].md`.

**File content:**

```
# Grooming Check — [Story Number]: [Story Title]

## Story Summary
[2-3 sentence plain-language summary of what this story is asking for and why]

## Epic Context
(omit section if no parent epic was found)
**Epic:** [epic-key] — [Epic Title]
**Epic Goal:** [1-2 sentence summary of the epic's purpose]
**Sibling Stories:**
| Key | Summary | Status |
|-----|---------|--------|
| [key] | [summary] | [status] |
**How this story fits:** [1 sentence explaining where this story sits within the broader epic]

## ⚠️ Missing Components
[Flagged gaps, or "None — story looks complete"]

## Repo Freshness
[Last-pull date for each repo inspected, or "Pulled fresh before analysis"]

## Linked Items
| Key | Link Type | Summary | Status |
|-----|-----------|---------|--------|
| [key] | [type] | [summary] | [status] |
[or "No linked items found"]

## Story Point Estimate
**Suggested estimate:** [number]
**Reasoning:** [explanation]

## Technical Overview
[High-level summary of what layers/areas are touched]

## Conditional Logic
(if applicable)
| Condition | Outcome |
|-----------|---------|
| If X and Y | Do A |
| If Y and Z | Do B |
[or omit section if no conditional logic identified]

## Change Impact
**API changes:** [details]
**Core changes:** [details]
**Multi-product consideration:** [open question or assertion]

## AC Completeness
[Gaps, or "AC appears to cover all described scenarios"]

## Questions for Grooming
1. [Question]
2. [Question]
...

## Figma Design
[Summary of design details, or "No Figma link found"]
```

### 8c — Convert to .docx

Use a Python script (python-docx) to convert the markdown to a Word document saved at `docs/pre-grooming-check/[story-number].docx`.

If `python-docx` is not installed, run `pip3 install python-docx` first.

Write and run a Python script that:
- Reads `/tmp/grooming-check-[story-number].md`
- Parses headings (H1/H2/H3), paragraphs, bullet lists, numbered lists, tables, and inline bold (`**text**`)
- Outputs to `docs/pre-grooming-check/[story-number].docx`

### 8d — Instruct the user

After the file is saved, respond with:

```
Grooming check saved to: docs/pre-grooming-check/[story-number].docx

To attach it to the Jira story, open:
https://workwave.atlassian.net/browse/[story-number]

Then drag and drop the file onto the ticket, or use the paperclip / Attach button.
```
