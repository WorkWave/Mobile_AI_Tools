# /create-pr — PR Workflow for WorkWave Mobile

Automates the full PR workflow for both the core (MobileCore submodule) and product repos: pre-flight checks, commit generation, standards validation, AC validation, and PR creation.

**Repo layout assumption:** This command is run from the product repo root. The core repo is the git submodule at `./MobileCore/`.

---

## Step 1 — Intake

Collect all three inputs before any phase runs. Do not ask for anything mid-command.

Ask the user:

```
To get started I need three things:

1. Story ticket number (e.g. MOB-1234 or MO-123)
2. Story description — paste the title or description from Jira
3. AC check preference:
   (1) Auto-detect or provide path to spec.md
   (2) Paste AC manually
   (3) Skip AC checks
```

After receiving all three, confirm back:

```
Got it. Here's what I'll work with:
  Ticket:  {ticket}
  Story:   {description}
  AC:      {option chosen}

Proceeding to Phase 1 — Pre-flight & Commit.
```

Store these values. Do not ask for them again at any point.

---

## Phase 1 — Pre-flight & Commit

Run every check in the listed order. On any hard stop: tell the user exactly what to fix and do not proceed until they say they've resolved it and ask to continue. When they retry, **re-run all checks from Check 1**.

Sync and rebase failures are hard stops — the user must resolve them manually. Uncommitted changes are not a blocker; they are committed in-line as part of this phase.

---

### Core repo

#### Check 1 — Core branch pattern

```bash
git -C MobileCore branch --show-current
```

The branch name must contain a Jira-style ticket ID: one or more uppercase letters, a hyphen, and digits (e.g. `MOB-1234`, `MO-123`). A branch like `feature/MOB-1234-add-thing` passes. A branch like `brianna/my-fix` fails.

If it does not match:
> ⚠️ Core branch `{branch}` does not follow the expected naming pattern. Branch names should contain a ticket reference such as `feature/MOB-1234-description`. Please confirm you want to continue with this branch name, or switch to a correctly named branch first.

Wait for explicit user confirmation before continuing.

---

#### Check 2 — Core up to date with remote

```bash
git -C MobileCore fetch origin
CORE_BRANCH=$(git -C MobileCore branch --show-current)
git -C MobileCore log HEAD..origin/$CORE_BRANCH --oneline
```

If there is any output:
> 🔴 Core branch is behind its remote. Run the following to bring it up to date, then retry:
> ```
> git -C MobileCore pull
> ```

**Stop. Do not proceed.**

---

#### Check 3 — Core up to date with master

```bash
git -C MobileCore fetch origin master
git -C MobileCore log HEAD..origin/master --oneline
```

If there is any output:
> 🔴 Core branch is behind `master`. You must rebase before creating a PR:
> ```
> cd MobileCore
> git rebase origin/master
> ```
> Resolve any conflicts, then return to the product root and retry.

**Stop. Do not proceed.**

---

#### Core commit

```bash
git -C MobileCore status --porcelain
```

**If there are uncommitted changes:**

Derive a short title from the intake story description (5–8 words, imperative mood, lowercase after the ticket number — e.g. `add offline support for work orders`).

Present the proposed commit message:
> Proposed core commit message:
> ```
> [{ticket}] {short title}
> ```
> Approve this message, or provide an edited version.

After approval:
```bash
git -C MobileCore add -A
git -C MobileCore commit -m "[{ticket}] {approved title}"
```

**If there are no uncommitted changes:**

Check whether commits already exist ahead of master:
```bash
git -C MobileCore log origin/master..HEAD --oneline
```

If commits exist, validate each message against the pattern `[TICKET-NNN] description` (uppercase letters, hyphen, digits, space, description text). If any do not match:
> ⚠️ The following core commit(s) do not follow the required format `[MOB-XXXX] short title of change`:
> {list of non-conforming messages}
> Please amend or rebase these commit messages before merging.

If no uncommitted changes and no commits ahead of master:
> ℹ️ Core repo has no uncommitted changes and no new commits ahead of master. Skipping core commit step.

---

### Product repo

#### Check 4 — Submodule pointer is current

Now that any core changes are committed, verify the product repo's submodule pointer:

```bash
git submodule status MobileCore
```

If the line starts with `+`: the pointer is stale and needs to be staged. Note this — the submodule pointer update will be included in the product commit below.

If the line starts with `-`:
> 🔴 The MobileCore submodule is not initialized. Run:
> ```
> git submodule update --init MobileCore
> ```
> Then retry.

**Stop only if the submodule is uninitialized. A stale pointer is handled in the product commit step.**

---

#### Check 5 — Product branch pattern

```bash
git branch --show-current
```

Apply the same pattern check as Check 1.

If it does not match:
> ⚠️ Product branch `{branch}` does not follow the expected naming pattern. Branch names should contain a ticket reference such as `feature/MOB-1234-description`. Please confirm you want to continue with this branch name, or switch to a correctly named branch first.

Wait for explicit user confirmation before continuing.

Note: core and product branch names do not need to match each other — only that each independently follows the pattern.

---

#### Check 6 — Product up to date with remote

```bash
git fetch origin
PRODUCT_BRANCH=$(git branch --show-current)
git log HEAD..origin/$PRODUCT_BRANCH --oneline
```

If there is any output:
> 🔴 Product branch is behind its remote. Run the following, then retry:
> ```
> git pull
> ```

**Stop. Do not proceed.**

---

#### Check 7 — Product up to date with dev

```bash
git fetch origin dev
git log HEAD..origin/dev --oneline
```

If there is any output:
> 🔴 Product branch is behind `dev`. You must rebase before creating a PR:
> ```
> git rebase origin/dev
> ```
> Resolve any conflicts, then retry.

**Stop. Do not proceed.**

---

#### Product commit

```bash
git status --porcelain
```

**If there are uncommitted changes** (including a stale submodule pointer flagged in Check 4):

If the only change is the MobileCore submodule pointer, use this message:
```
[{ticket}] update core submodule
```

If there are other changes alongside or instead of the submodule pointer, derive a short title from the intake story description as in the core commit step.

Present the proposed message:
> Proposed product commit message:
> ```
> {proposed message}
> ```
> Approve this message, or provide an edited version.

After approval:
```bash
git add -A
git commit -m "{approved message}"
```

**If there are no uncommitted changes:**

Check whether commits already exist ahead of dev:
```bash
git log origin/dev..HEAD --oneline
```

If commits exist, validate each message against the same pattern. If any do not match:
> ⚠️ The following product commit(s) do not follow the required format `[MOB-XXXX] short title of change`:
> {list of non-conforming messages}
> Please amend or rebase these commit messages before merging.

If no uncommitted changes and no commits ahead of dev:
> ℹ️ Product repo has no uncommitted changes and no new commits ahead of dev. Skipping product commit step.

---

#### Check 8 — Product has commits ahead of dev

```bash
git log origin/dev..HEAD --oneline
```

If there is no output:
> 🔴 Product branch has no commits ahead of `dev`. There is nothing to include in a PR. Make your changes and commit them first, then retry.

**Stop. Do not proceed.**

---

### Phase 1 complete

> ✅ Pre-flight and commit steps complete. Proceeding to Phase 2 — Standards Check.

---

## Phase 2 — Standards Check

Compute the diffs that will be used for all remaining phases:

**Core diff** — changes in core that are not yet in master:
```bash
git -C MobileCore diff origin/master...HEAD
```

**Product diff** — changes in product that are not yet in dev (C# and project files only):
```bash
git diff origin/dev...HEAD -- '*.cs' '*.csproj' '*.xaml'
```

Save both diffs — they will be reused in Phases 3 and 4 without recomputing.

---

Run `/standards-check` against the changed code, using the core diff and product diff computed above as the input. Follow the `/standards-check` command in full — including the Mobile.Core reuse check and all standards categories.

---

### After standards output

**If there are no ⚠️ or 🔴 findings:** proceed automatically to Phase 3.

**If there are ⚠️ Needs Attention or 🔴 Violations findings**, ask:
> I found {n} standards issue(s) in the changed code. Would you like help addressing them now?
> - **Yes** — I'll walk through each issue and make the fixes with you
> - **No** — I'll note them in the PR description and continue

**If the user says yes:**

Work through each ⚠️ and 🔴 finding with the user. For each one:
1. Show the specific file and line, explain the violation, and propose a fix
2. Apply the fix after user confirmation
3. Move to the next finding

Once all agreed fixes are applied, offer a follow-up commit:
> Here is the proposed commit message for the standards fixes:
> ```
> [{ticket}] address standards violations
> ```
> Approve this message, or provide an edited version.

After approval, commit in both repos where changes were made:
```bash
# If core files were changed:
git -C MobileCore add -A
git -C MobileCore commit -m "[{ticket}] address standards violations"

# If product files were changed:
git add -A
git commit -m "[{ticket}] address standards violations"
```

Re-compute the diffs after the commit so Phases 3 and 4 use the updated code:
```bash
git -C MobileCore diff origin/master...HEAD
git diff origin/dev...HEAD -- '*.cs' '*.csproj' '*.xaml'
```

**If the user says no** (or if only 💡 Suggestions remain with no violations):

Store the 🔴 violations list for inclusion in the PR description. Proceed to Phase 3.

---

## Phase 3 — AC Validation

Use the AC preference collected at intake. The diffs from Phase 2 are reused here.

---

### Option 1 — spec.md (auto-detect or path)

First, attempt to auto-detect the spec file. Search in this order:
1. `docs/specs/` — look for any `spec.md` file whose folder name matches the ticket number or a slug derived from the story description
2. `docs/specs/spec.md`
3. Any `spec.md` anywhere under `docs/specs/`

If found, tell the user the path being used and proceed.

If not found:
> I couldn't find a spec.md automatically. Please provide the path to the spec file.

Once located, read the full spec content.

---

### Option 2 — manual AC

Ask:
> Please paste your acceptance criteria. Type or paste all items, then let me know when you're done.

---

### Option 3 — skip

> ℹ️ AC validation skipped.

Proceed directly to Phase 4.

---

### AC comparison

Compare each AC item against the core diff (feature vs master) and the product diff (feature vs dev). For each item, determine whether the diff contains evidence it was addressed.

Output a checklist:

```
## AC Validation: {ticket}

- [x] {AC item} — addressed in {filename}
- [x] {AC item} — addressed in {filename}
- [ ] {AC item} — not found in diff ⚠️
```

If there are unchecked items:
> ⚠️ {n} AC item(s) were not found in the diff. These will be noted in the PR description. Proceed to Phase 4 — PR Generation?

Store any AC gaps for inclusion in the PR description.

AC gaps are non-blocking — they surface information for the reviewer; they do not prevent the PR from being created.

---

## Phase 4 — PR Generation

### PR title

Construct the title from the intake story description:
```
[{ticket}] {short title derived from story description}
```

Present to the user:
> Proposed PR title:
> ```
> [{ticket}] {short title}
> ```
> Approve or edit.

---

### PR description

Build the description in this exact order:

```markdown
> 🤖 This PR was created with [Claude Code](https://claude.ai/claude-code).

## Story
[{ticket}](https://workwave.atlassian.net/browse/{ticket})

{story description from intake}

## Summary
{1–3 sentences summarising what changed, derived from the diffs}

## Key Technical Notes
{Bullet points of notable implementation details from the core diff (feature vs master) and product diff (feature vs dev). Focus on non-obvious choices, new patterns, and anything a reviewer should pay attention to.}
```

If standards violations were found in Phase 2 and the user chose to proceed without fixing, append:

```markdown
## Standards Violations
The following violations were identified and should be addressed before merging:

{🔴 violations list from Phase 2}
```

If AC gaps were identified in Phase 3, append:

```markdown
## AC Gaps
The following acceptance criteria items were not confirmed in the diff and should be verified manually:

{unchecked AC items from Phase 3}
```

---

### Present for review

Show the full title and description:

> Here is the proposed PR:
>
> **Title:** `[{ticket}] {short title}`
>
> **Description:**
> {full description}
>
> Does this look right? Approve to open the PRs, or tell me what to change.

Wait for explicit user approval. Apply any requested edits and re-present before opening.

---

### Open the PRs

After approval, open both PRs. Use the approved title and description for both.

**Core PR (MobileCore → master):**
```bash
cd MobileCore && gh pr create \
  --base master \
  --title "[{ticket}] {approved title}" \
  --body "{approved description}"
```

**Product PR (root → dev):**
```bash
gh pr create \
  --base dev \
  --title "[{ticket}] {approved title}" \
  --body "{approved description}"
```

Capture the URL returned by each command.

Present the results:
> ✅ Both PRs are open:
> - **Core:** {core PR URL}
> - **Product:** {product PR URL}
>
> ⚠️ Remember to set reviewers on both PRs before requesting review.
