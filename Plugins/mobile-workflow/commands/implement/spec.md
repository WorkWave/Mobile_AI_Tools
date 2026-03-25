# /spec — Feature Specification Generator

Generate a structured feature specification from a description and acceptance criteria.
This spec becomes the single source of truth for `/standards-check`, `/adversarial-check`,
`/tests`, and `/implement`.

---

## Step 1 — Detect Project Context

Before generating anything, silently inspect the current working directory and nearby files
to determine which project and architecture pattern applies.

**Detection signals (check in this order):**

1. Read `CLAUDE.md` in the project root — if it names the project or architecture, use that
2. Inspect namespace patterns in nearby `.cs` files
3. Look for structural markers:
   - `Managers/` directory + `Bootstrap.cs` → **Manager pattern** (TinyIoC, async/await, singleton DI)
   - `Repositories/` + `Commands/` or `Queries/` directories → **Repository pattern** (manual construction, synchronous I/O)
   - `ViewModels/` + API proxy classes → **MVVM + Proxy pattern**
4. Check for `TinyIoCContainer` usage → confirms Manager/singleton pattern
5. Check async patterns — `async Task` throughout vs `Thread`/`Timer` → modern vs legacy async model

If context is ambiguous after inspection, ask one targeted question before proceeding:
> "I can see [what you found] but couldn't confirm [what's missing]. Is this project using [specific pattern A] or [specific pattern B]?"

---

## Step 2 — Gather Input

Ask the user for the following. Accept either interactive input or a pre-written description:

```
1. Feature name (will become the folder name — use kebab-case, e.g., "user-deactivation")
2. Feature description — what does this feature do? What problem does it solve?
3. Acceptance criteria — how do we know this is done? List each criterion separately.
4. Any known constraints or dependencies? (optional)
```

---

## Step 3 — Generate the Spec File

Create the following file structure:

```
docs/specs/{feature-name}/
  spec.md
```

Read `docs/Resources/spec-template.md` to get the canonical template, then populate `spec.md`
using that template with the following field mappings:

- `[Type]: Short Description` → `{Feature Type}: {Feature Name}` (Type = "Feature", "Fix", "Refactor", etc.)
- `Branch` → `feat/{feature-name}` (kebab-case)
- `Created` / `Updated` → today's date
- `Summary / Description` → restate the feature description in clear, implementation-neutral language; remove ambiguity; note any inferences made
- `Acceptance Criteria` → one checkbox per criterion, rewritten in testable "given/when/then" format where possible
- `Unanswered Questions` → anything needing a decision before implementation; leave Answer/Resolved blank
- `Plan` → break the implementation into numbered steps with a suggested commit message per step, based on the detected architecture pattern
- `Execution Log` → leave blank (populated during execution)
- `Files Changed` → list existing files likely to be touched; infer from architecture notes
- `Testing` → describe expected automated tests and manual testing needed
- `Final Notes` → any architecture notes, DI registration required, or scope boundary notes

---

## Step 4 — Confirm and Save

After generating `spec.md`:

1. Show the user a summary of what was created
2. Ask: "Does this look right, or should we adjust anything before moving to the next step?"
3. Once confirmed, tell the user:
   > "Spec saved to `docs/specs/{feature-name}/spec.md`. Run `/implement` to execute the full
   > workflow, or run `/standards-check`, `/adversarial-check`, and `/tests` individually."
