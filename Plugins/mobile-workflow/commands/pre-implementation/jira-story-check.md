# /jira-story-check — Post-Grooming Story Validation

Post-grooming validation tool. Given a Jira story number, checks that the
story has all required components and is correctly configured before
implementation begins.

Run this **after grooming** to confirm the story is ready for development.
Also used automatically as **Step 0 in /implement** — if the story fails
validation, the user is asked whether to proceed or stop before any
implementation work begins.

**Usage:** `/jira-story-check [story-number]`
**Example:** `/jira-story-check PPM-1234`

---

## Step 1 — Collect Story Number

If the story number was not provided at invocation, ask the user for it now.
Use the Atlassian MCP server to fetch the full story and all fields.

---

## Step 2 — Run Validation Checks

Check every item below. **Never stop early** — run all checks regardless of failures.
Record the result of each as ✅ Pass, ⚠️ Note, or ❌ Fail, then continue to the next check.

| Check | Pass Condition | Fail / Note Condition |
|---|---|---|
| Story status | Status is "To Do" | Any other status — ⚠️ Note, do not fail |
| Grooming label | "groomed" label present | ❌ Fail if missing — note and continue |
| Story prefix | Starts with PPM, PPM-API, RGM, RGM-API, WTM, or RM | ❌ Fail if wrong prefix — note and continue |
| Product field | Product field is populated | ❌ Fail if empty — note and continue |
| Blocked status | Story is not marked blocked | ❌ Fail — show blocked reason — note and continue |
| Description | Description present and non-empty | ❌ Fail if missing — note and continue |
| Acceptance criteria | AC present and non-empty | ❌ Fail if missing — note and continue |
| AC coverage | AC covers all scenarios in description | ⚠️ Note gaps — do not fail |
| Figma link | Figma URL present | ⚠️ Note if missing — do not fail |
| Work breakdown | WorkBreakdown field is populated | ❌ Fail if empty — note and continue |

---

## Step 3 — Determine Overall Readiness

**Ready:** All ❌ checks pass. Any ⚠️ notes are acceptable to proceed.

**Not Ready:** One or more ❌ checks failed. List what must be fixed
before implementation begins.

**When called from /implement and story is Not Ready:**
Present failures clearly and ask:
> "This story has validation failures. Would you like to:
> 1. Stop and fix the story before continuing
> 2. Proceed anyway (not recommended)"

Wait for the user's response before continuing.

---

## Output Format

```
## Jira Story Check — [Story Number]: [Story Title]

### Overall Status: ✅ Ready for Implementation
                or: ❌ Not Ready — action required

### Validation Results
✅ Story prefix: [prefix]
✅ Grooming label: present
✅ Product field: [product name]
✅ Description: present
✅ Acceptance criteria: present
⚠️ Story status: [current status] (expected To Do)
⚠️ Figma link: not found — confirm whether a design is needed
❌ Blocked: story is blocked — reason: [blocked reason]
❌ Grooming label: missing

### AC Coverage
[Scenarios not covered by AC, or "AC covers all described scenarios"]

### Action Required
[Items that must be fixed before implementation]
[or "None — story is ready for implementation"]
```
