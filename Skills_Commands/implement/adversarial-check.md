# /adversarial-check — Adversarial Failure Mode Analysis

Systematically find failure modes, edge cases, and security vulnerabilities in a spec
or implementation. Use this before writing tests and before committing.

This command acts as an adversary — its job is to find what can go wrong, not to
validate that the happy path works.

---

## Step 1 — Detect Project Context

Silently inspect the working directory:

1. Read `CLAUDE.md` if present
2. Check namespace patterns and structural markers
3. Identify: async vs sync codebase, singleton vs manual construction, mobile vs server-side
4. Note any shared infrastructure patterns (offline queues, singleton managers, proxy layers,
   multi-tenant data access) — these are high-risk areas

---

## Step 2 — Locate Input

Check for input in this order:

1. `/specs/{feature-name}/spec.md` — preferred input
2. A specific file path provided by the user
3. No input — ask: "What would you like me to analyse? Point me at a spec, a class,
   or describe what you're building."

---

## Step 3 — Run Adversarial Analysis

Work through each category below. Apply all categories to every analysis — do not skip
categories because they seem unlikely. The most dangerous failures are the ones that
seem unlikely until they happen.

For each finding:
1. Output the structured entry (see Step 4 for format)
2. Pause and present this prompt to the user:

   > **Finding #n — how would you like to handle this?**
   > 1. Address this in the implementation approach
   > 2. Add a test for this finding
   > 3. Accept the risk — I'll document why
   > 4. Skip — not applicable

3. Wait for the user's response before outputting the next finding
4. If the user chooses (3), follow up with: "Briefly describe why the risk is acceptable."
   Wait for their rationale before continuing.
5. Record the decision (and rationale if provided) — it will appear in the summary

Do not batch findings. Present one, wait, then continue.

---

### CATEGORY 1 — Input Boundary Conditions

Every public method that accepts input is an attack surface.

Check for:
- Null input where the method assumes a value
- Empty string vs null — these often follow different code paths
- Extremely long strings — buffer behavior, exception handling, truncation
- Special characters: quotes, semicolons, angle brackets, null bytes (`\0`)
- Unicode and control characters in free-text fields
- Numeric boundary values: zero, negative, `int.MaxValue`, `double.MaxValue`
- Invalid enum values or out-of-range integers passed as enums
- `DateTime` edge cases: `MinValue`, `MaxValue`, leap day (Feb 29), timezone boundaries
- Collections: null collection, empty collection, single item, very large collection

---

### CATEGORY 2 — Concurrency & Shared State

Especially critical in projects using singleton managers or shared proxies.

Check for:
- Two callers invoking the same method simultaneously — is shared state protected?
- Singleton manager state set by method A leaking into method B
- Concurrent reads and writes to the same entity or collection
- Race conditions on authentication or session state (e.g., two login calls simultaneously)
- Thread-safe header injection — if headers are set on a shared client, are concurrent
  calls safe?
- Test order dependency — do tests pass only because of state left by a previous test?
- `Dispose()` called while an async operation is still in flight

---

### CATEGORY 3 — External System Failures

The most dangerous failures are the ones your code doesn't control.

Check for:
- HTTP 401 — does the app re-authenticate or surface a raw exception?
- HTTP 429 (rate limiting) — is there backoff logic or does it hammer the endpoint?
- HTTP 500 — does internal server detail leak to the UI or caller?
- Network timeout mid-request — is the operation left in a consistent state?
- Malformed or partial JSON response — does deserialization throw or silently return null?
- Extremely large API response — memory behavior under load
- Identity provider or auth service unavailability — what happens to sessions in flight?
- Database lock contention (deadlock on concurrent writes to the same row)
- Connection pool exhaustion — what happens when no connections are available?

---

### CATEGORY 4 — Financial & Precision Data

Applies to any feature touching amounts, quantities, or calculated values.

Check for:
- Floating point drift — is currency stored as `double` instead of `decimal`?
  (`0.1 + 0.2 == 0.30000000000000004`)
- Negative amounts where the business logic assumes positive
- Zero-value transactions — are they valid? Are they handled or silently ignored?
- `NaN` and `Infinity` as numeric inputs (can arise from upstream `double` arithmetic)
- Concurrent payment or transaction submissions — duplicate submission risk
- Rounding behavior — does rounding happen at the right layer?

---

### CATEGORY 5 — Authentication & Authorization

Applies to any feature that touches user identity, permissions, or access control.

Check for:
- Permission check with a null or non-existent user/employee ID
- Permission check after the user is deactivated — is the cache invalidated?
- Bitwise permission edge case: value `0` (no bits set) — does it correctly deny all?
- Expired or revoked token used after the fact
- Session state after a failed login — is stale data cleared?
- Concurrent login calls — race condition on token or session storage
- "Reverse logic" permission flags — verify inversion is applied correctly
- Cross-tenant data access — can a session for Tenant A access Tenant B's data?

---

### CATEGORY 6 — Offline & Queue Integrity

Applies to any feature that uses an offline queue, background sync, or deferred operations.

Check for:
- Action queued, app killed, app restarted — does it replay correctly?
- Same action queued twice — duplicate submission on sync?
- Action queued that is later invalidated server-side (e.g., record deleted) — error handling?
- Sync failure mid-batch — is partial success handled or is the whole batch retried?
- Queue state after an unhandled exception during processing
- Network restored mid-sync — does the queue resume cleanly or restart?

---

### CATEGORY 7 — Security Patterns

Check for introduction or continuation of known security anti-patterns:

- Secrets, API keys, or encryption keys hardcoded in source
- Legacy crypto used (TripleDES, DES, RC4, MD5 for key derivation, AES-ECB)
- Sensitive data (tokens, passwords, PII) written to logs
- Stack traces or internal error details returned to callers
- User input used directly in a URL, query string, or SQL without encoding/parameterization
- Cleartext HTTP used for any network call
- Certificate validation bypassed
- Auth tokens stored in insecure locations (plain preferences, unencrypted files)
- Sensitive data in URL query parameters instead of headers or request body

---

### CATEGORY 8 — Reflection & Dynamic Routing

Applies to projects using attribute-based endpoint discovery or dynamic routing.

Check for:
- Entity with no routing attribute — what happens at runtime?
- Malformed or invalid path in a routing attribute — silent failure or exception?
- Drift between attribute values and actual server endpoints
- New entity added without the required routing attribute

---

### CATEGORY 9 — Singleton State Leakage

Applies to projects where managers or services are long-lived singletons.

Check for:
- Method sets internal state — does a subsequent call on the same instance see stale state?
- Cached data that should be invalidated after a mutation (e.g., permission cache after
  role change, session cache after logout)
- Static fields that accumulate state across test runs
- Disposal of the container in tests — does it actually clear all registered instances?

---

### CATEGORY 10 — Fire-and-Forget & Side Effects

Check for:
- Async operations started with no `await` and no error handling
- Audit log, notification, or analytics calls that can silently drop on failure
- No retry logic or dead-letter queue for critical side effects
- Operations that must succeed together (e.g., billing + auth revocation) running
  independently with no compensation logic if one fails

---

### CATEGORY 11 — Secrets Exposure

Applies to any feature that handles credentials, tokens, keys, or sensitive configuration.

Check for:
- API keys or passwords hardcoded in source or committed to the repo
- Secrets logged at any level especially in catch blocks
- Sensitive values returned in API responses or error messages
- Secrets passed as URL query parameters instead of headers
- Environment variables that could be inadvertently exposed

---

### CATEGORY 12 — Input Trust

Applies to any feature that accepts external input and uses it in downstream operations.

Check for:
- User-provided strings entering a prompt or query without isolation
- External API responses used directly without schema validation
- File contents read and passed downstream without sanitization
- Input from one agent trusted implicitly by another without validation
- Form values used in file paths or SQL without encoding

---

### CATEGORY 13 — LLM Interaction Surface

Applies to any feature that constructs prompts, calls an LLM, or uses an AI agent.

Check for:
- Prompts constructed from untrusted input without tag-based isolation
- LLM output used directly in code execution or file writes without validation
- Excessive tool permissions granted to an AI agent
- No human-in-the-loop checkpoint before consequential actions
- Agent output trusted as ground truth without a verification step

---

## Step 4 — Format Output

Return findings in this structure. Every finding must include all four fields.

```
## Adversarial Analysis: {feature or file name}
**Project context:** {detected pattern}
**Date:** {today}

---

### Finding #{n}
**Category:** {category name from above}
**Failure mode:** {one sentence — what goes wrong}
**Blast radius:** {what state does this leave the system in? Is it recoverable?}
**Trigger condition:** {what specific input, timing, or sequence causes this}
**Recommended mitigation:** {what should be done — be specific}
**Test case to write:** {describe the test that would catch this}
**Decision:** {populated after user responds — one of: Address in implementation | Add a test | Risk accepted | Skipped}
**Rationale:** {populated only for "Risk accepted" decisions}

---
```

Produce findings in priority order:
1. 🔴 Data corruption or security vulnerability
2. ⚠️ Unhandled exception or silent failure
3. 💡 Edge case with degraded but recoverable behavior

End with a summary:

```
## Summary
**Total findings:** {n}
**Critical (🔴):** {n}
**High (⚠️):** {n}
**Low (💡):** {n}

### Decision Log
| # | Severity | Failure Mode | Decision | Rationale |
|---|----------|-------------|----------|-----------|
| 1 | 🔴/⚠️/💡 | {one-line summary} | Address in implementation / Add a test / Risk accepted / Skipped | {rationale if risk accepted, otherwise —} |
| … | | | | |

### Open Items
**To address in implementation:** {list finding numbers, or "none"}
**Tests to write:** {list finding numbers, or "none"}
**Risks accepted:** {list finding numbers, or "none"}
**Skipped:** {list finding numbers, or "none"}
```
