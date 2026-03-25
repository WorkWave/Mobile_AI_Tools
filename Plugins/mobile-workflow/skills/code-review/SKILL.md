---
name: code-review
description: "Use this skill when the user asks to review code, check a PR, look at a diff, audit a class or method, or asks whether code is secure, correct, or follows standards. Triggers: 'review this', 'look at this code', 'check this PR', 'is this secure', 'does this follow our patterns', 'audit this class', 'what do you think of this code'"
---

# Code Review Skill

## When to Use
- User provides code and asks for a review, audit, or feedback
- User asks whether code is secure or follows WorkWave patterns
- User shares a diff or PR and asks for an assessment

## Context: WorkWave Codebases
- **RG** (RealGreen Mobile): .NET 9, Manager/Proxy pattern, TinyIoC, async/await, XUnit + Moq + FluentAssertions — shared logic in `RG.Mobile.Core`
- **PPM** (PestPac Mobile): .NET 9, same Manager/Proxy/TinyIoC stack — shared logic in `PP.Mobile.Common`
- Detect which codebase is in scope from file paths or namespaces (`RG.Mobile` vs `PP.Mobile`)

## Review Process

This skill orchestrates three layers of analysis:

1. **Standards check** — runs `/standards-check` to validate coding conventions, naming, architecture patterns, and Mobile.Core reuse
2. **Adversarial check** — runs `/adversarial-check` to surface failure modes, edge cases, and security vulnerabilities
3. **Holistic review** — items requiring broader judgment that neither sub-command covers

## Steps

1. Identify which codebase the code belongs to (RG or PPM)
2. Read the code fully before analyzing
3. Run `/standards-check` on the code — capture the full output
4. Run `/adversarial-check` on the code — compile **all findings without per-finding interactive responses**; the review output is where the user will act on them
5. Apply the Holistic Checklist below for items not covered by the sub-commands
6. Produce unified output using the Output Format below

## Holistic Checklist

These items are not covered by `/standards-check` or `/adversarial-check` — apply them manually:

### AI-Generated Code Concerns
- Outdated patterns: AI may suggest approaches deprecated for security or correctness
- False confidence: code compiles cleanly does not mean it is correct or secure
- Context blindness: flag anything that assumes knowledge the AI does not have about the codebase or business rules

### Platform Coverage (RG)
- If the change affects both Android and iOS, are both platforms updated?
- Are shared changes in `RG.Mobile.Core` where appropriate?
- Are platform-specific changes in the correct platform projects?

### Testing Implications
- Are there test implications? Should tests be added or updated?
- Are existing tests still valid after this change?
- Are new behaviors adequately covered?

### Architectural Fit
- Does this belong in the right layer (Manager vs Proxy vs ViewModel)?
- Is this the right abstraction — or is there an existing pattern in the codebase that should be reused?
- Does the change introduce coupling that will make the codebase harder to maintain?

---

## Output Format

Produce a unified review with these sections:

---

### Summary
One sentence verdict: **Approved** / **Approved with comments** / **Needs changes**

---

### Changes Made
Summary of all changed files with paths (when reviewing a diff or PR).

---

### Standards Findings
Output from `/standards-check`, formatted as:

**✅ Looks Good**
{List items clearly correct — brief, one line each}

**⚠️ Needs Attention**
{Items needing improvement — include the specific issue and a suggested fix}

**🔴 Violations**
{Clear violations — include problem, location, and correct pattern with a short code example if helpful}

---

### Adversarial Findings
Compiled findings from `/adversarial-check`, formatted as a table. Do not use per-finding interactive responses — compile all findings and present them here.

| # | Severity | Category | Failure Mode | Recommended Mitigation |
|---|----------|----------|--------------|------------------------|

Severity: 🔴 Critical / ⚠️ High / 💡 Low

If no adversarial findings apply, state that explicitly — an empty table is a meaningful result.

---

### Holistic Findings
Items from the Holistic Checklist above.

| Severity | Category | Finding | Recommendation |
|----------|----------|---------|----------------|

Severity levels: Critical / Major / Minor / Advisory

---

### What's Good
2–3 things done well — be specific, reference actual code.

---

### Next Steps
Numbered list in priority order: Critical first, then Major, then Minor/Advisory.

---

## Example

See `examples/route-manager-example.md` for a worked example with expected review output.
