# /implement — Full Implementation Workflow

Orchestrate the complete spec-driven, test-first, standards-aware implementation
workflow. Runs `/spec` → `/standards-check` → `/adversarial-check` → `/tests` →
implementation in sequence, with a human review gate between each phase.

Nothing is implemented until the spec, standards check, adversarial findings,
and test suite have all been reviewed and confirmed.

---

## Workflow Overview

```
Step 0  — Jira Story    ask for story number → /jira-story-check → pull story via MCP
           ↓ [gate: fail if ❌ results unless user chooses to proceed]
Phase 0 — Brainstorm    superpowers:brainstorming
           ↓ [review gate]
Phase 1 — Spec          /spec
           ↓ [review gate]
Phase 2 — Standards     /standards-check
           ↓ [review gate]
Phase 3 — Adversarial   /adversarial-check
           ↓ [review gate]
Phase 4 — Tests         /tests
           ↓ [review gate — confirm tests compile and fail correctly]
Phase 5 — Implement     superpowers:test-driven-development → decompose into parallel
                        workstreams → subagents for parallel implementation
                        → dotnet build → debug if failed → commit per unit
           ↓ [review gate]
Phase 6 — Verify        run tests → superpowers:systematic-debugging (if failures)
                        → superpowers:verification-before-completion → confirm passing
```

At every review gate, stop and wait for explicit confirmation before proceeding.
Do not skip phases or combine phases without the user's instruction.

---

## Step 0 — Jira Story Validation & Context

### 1. Ask for the Jira story number

Ask the user:
> "What is the Jira story number for this implementation? (e.g. MOB-12345)"

Wait for the user to provide the story number before continuing.

### 2. Run /jira-story-check

Execute the `/jira-story-check` command on the provided story number.

### 3. Handle validation results

If the story has any ❌ Fail results, display them clearly and ask:

> "This story has validation failures:
>
> {list each ❌ Fail result}
>
> Would you like to:
> 1. Stop and fix the story first
> 2. Proceed anyway (not recommended)"

**Wait for the user's response before continuing.** If the user chooses option 1, stop completely. If the user chooses option 2, note the failures and continue.

If the story passes all checks, proceed directly to step 4.

### 4. Pull full story content via Atlassian MCP

Use the `mcp__claude_ai_Atlassian__getJiraIssue` tool to fetch the full story content.
Extract and make available as context for all subsequent phases:

- **Title** — the story summary
- **Description** — full story description and background
- **Acceptance Criteria** — all AC from the story (check both description body and custom AC field)
- **Figma link** — any Figma design URL found in the description or attachments (save this for Phase 5)

This context replaces the need for the user to manually provide story details in subsequent phases.
All phases should reference this pulled story content rather than asking the user to re-describe the feature.

**Proceed to Phase 0 — Brainstorm.**

---

## Phase 0 — Brainstorm

Before any spec is written, invoke `superpowers:brainstorming` using the Skill tool.

This explores user intent, surfaces unstated requirements, and reveals design
alternatives before the spec locks in an approach.

**STOP after brainstorming completes. Do not proceed to Phase 1 under any circumstances
until the user explicitly types "confirmed" or "proceed to spec". Do not generate
a spec, plan, design, or any implementation artifacts as part of this phase.
The only output of Phase 0 is the brainstorm results and the following prompt:**

> "Brainstorming complete. Review the above and confirm when you're ready to move
> to Phase 1 — Spec. If you'd like to adjust direction first, tell me what to change."

---

## Phase 1 — Spec

Execute the `/spec` command in full:

1. Detect project context from file structure
2. Prompt for feature name, description, and acceptance criteria
3. Generate `docs/specs/{feature-name}/spec.md`
4. Show the spec and ask:
   > "Does this spec look right? Confirm to move to the standards check, or tell
   > me what to change."

**Do not proceed until confirmed.**

---

## Phase 2 — Standards Check

Execute the `/standards-check` command against the spec:

1. Read `/specs/{feature-name}/spec.md`
2. Run all applicable checks for the detected project pattern
3. Output findings in the standard format (✅ / ⚠️ / 🔴)
4. If violations are found, ask:
   > "There are {n} standards violations in the spec or proposed approach. Should
   > we resolve these before continuing, or proceed and address them during
   > implementation?"
5. Save findings to `/specs/{feature-name}/standards-findings.md`
6. Ask for confirmation before proceeding.

**Do not proceed until confirmed.**

---

## Phase 3 — Adversarial Analysis

Execute the `/adversarial-check` command against the spec:

1. Read `/specs/{feature-name}/spec.md`
2. Run all 10 adversarial categories
3. For each finding: present it, then pause and wait for the user to choose how to
   handle it before continuing to the next finding — the command manages this loop;
   do not batch findings or skip the per-finding prompt
4. After all findings have been presented and decided, save the full output — including
   the decision log — to `/specs/{feature-name}/adversarial-findings.md`
5. Review the completed decision log and ask:
   > "Adversarial analysis complete. Here's the decision summary: {n} to address in
   > implementation, {n} tests to write, {n} risks accepted, {n} skipped.
   > Any 🔴 findings not marked 'Address in implementation' should be reconsidered —
   > should we revisit any decisions before continuing to the test suite?"

**Do not proceed until confirmed.**

---

## Phase 4 — Test Suite

Execute the `/tests` command using spec + adversarial findings:

1. Read `/specs/{feature-name}/spec.md`
2. Read `/specs/{feature-name}/adversarial-findings.md` — use only findings marked
   "Add a test" in the decision log; skip findings marked "Skipped" or "Risk accepted"
3. Generate test plan and ask for confirmation
4. Generate test file and fixtures file following project conventions
5. Run `dotnet test --filter "FullyQualifiedName~{Domain}ManagerTests"` immediately
6. Evaluate the results:
   - **Compile error** — fix it; re-run; do not ask the user to fix it
   - **Tests fail as expected** — correct; continue to the review gate
   - **Any test unexpectedly passes** — flag it explicitly and fix the assertion before continuing
7. Report what was found:
   > "Tests are compiled and red. {n} tests failing as expected, {n} unexpectedly passing (if any).
   > Here are the results: {summary}
   >
   > Confirm to proceed to implementation, or tell me what to adjust."

**Do not proceed until confirmed.**

---

## Phase 5 — Implementation

Before writing any code, invoke `superpowers:test-driven-development` using the
Skill tool. This enforces the red → green → refactor loop and ensures each piece
of implementation is driven by a failing test, not written speculatively.

Then write the implementation. Follow all project conventions detected in Phase 1
and address all standards findings from Phase 2.

### Parallel workstreams

Decompose the implementation plan into independent workstreams before writing any code.
Identify which units of work have no dependencies on each other and can be implemented
simultaneously. Use subagents (via `superpowers:dispatching-parallel-agents`) to implement
independent workstreams in parallel rather than implementing everything sequentially.
Only implement units sequentially when one genuinely depends on the output of another.

### Figma UI components

If the Jira story pulled in Step 0 contains a Figma design link, use the
`/mobile-ui-builder` command to generate UI components from that Figma design as part
of the implementation. Do not skip this step if a Figma link is present.

**Implementation rules:**

### Scope
- Change a maximum of 3 files per implementation unit
- If more than 3 files need to change, break the work into separate units
- Commit after each unit — do not accumulate large uncommitted changes

### File creation checklist (Manager pattern)
- [ ] Interface created at correct path: `Managers/{Domain}/I{Domain}Manager.cs`
- [ ] Implementation created at correct path: `Managers/{Domain}/{Domain}Manager.cs`
- [ ] Implementation inherits from base manager class
- [ ] All dependencies declared as `[Inject]` properties
- [ ] Proxy methods declared `public virtual`
- [ ] Singleton registered in `Bootstrap.cs`
- [ ] Domain docs created or updated: `docs/domains/{domain}.md`

### During implementation
- Apply mitigations from the adversarial findings as you write each method
- Do not leave 🔴 critical adversarial findings unaddressed
- Add the `Async` suffix to all async methods
- Log exceptions before catching and continuing
- Do not expose exception details to callers

### After each unit — before committing

1. Run `dotnet build` against the full solution:
   ```
   dotnet build
   ```
2. If the build **fails**:
   - Invoke `superpowers:systematic-debugging` using the Skill tool to diagnose the
     cause — do not guess; read the compiler output carefully
   - Fix all errors
   - Re-run `dotnet build`
   - Repeat until the build is clean
   - Do not commit, do not ask the user to fix it, and do not move to the next unit
     until the build passes
3. If the build **passes**, prompt the user with a proposed commit message and ask for
   confirmation before committing:
   > "Build passed. Ready to commit this unit. Proposed commit message:
   >
   > `[{JIRA-STORY-NUMBER}] {unit description}`
   >
   > Confirm to commit, or tell me what to change."

   Wait for the user to confirm the commit message before running `git commit`.
   The commit message **must** follow the pattern `[MOB-XXXXX] description` using the
   story number collected in Step 0.

4. After the user confirms, commit and ask:
   > "Committed. Does this look right before I continue to the next unit?"

**Do not write all files at once without intermediate review. Do not commit a broken build.
Do not commit without user confirmation of the commit message.**

---

## Phase 6 — Verify

After implementation is complete:

1. Run `dotnet test` directly
2. If tests fail:
   - Invoke `superpowers:systematic-debugging` using the Skill tool before proposing
     any fix — do not guess at a cause; diagnose first
   - Propose a fix based on the diagnosis
   - Ask for confirmation before applying
   - Re-run `dotnet test`
   - Repeat until all tests pass
3. If all tests pass, invoke `superpowers:verification-before-completion` using the
   Skill tool to confirm the evidence before claiming done, then produce a completion
   summary:

```
## Implementation Complete: {Feature Name}

### Files created
{list}

### Files modified
{list}

### Test results
{n} tests passing, 0 failing

### Adversarial findings addressed
{list each finding and how it was mitigated}

### Standards findings addressed
{list each finding and how it was resolved}

### What was not covered
{any findings that require integration tests, infrastructure changes,
or follow-up work — with suggested next steps}

### Suggested next steps
- [ ] {e.g., register in Bootstrap.cs if not done}
- [ ] {e.g., update domain docs}
- [ ] {e.g., open PR and request review}
- [ ] {e.g., follow up on any deferred adversarial findings}
```
