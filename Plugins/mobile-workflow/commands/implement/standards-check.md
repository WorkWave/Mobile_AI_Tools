# /standards-check — Coding Standards Validator

Review a spec or implementation against project coding standards and flag violations
before code is written or during review.

---

## Step 1 — Detect Project Context

Silently inspect the working directory using the same detection logic as `/spec`:

1. Read `CLAUDE.md` if present
2. Check namespace patterns in nearby `.cs` files
3. Look for structural markers: `Managers/` + `Bootstrap.cs`, `Repositories/` + `Commands/`,
   `TinyIoCContainer` usage, async patterns
4. If ambiguous, ask one targeted question before proceeding

---

## Step 2 — Locate Input

Check for input in this order:

1. `/specs/{feature-name}/spec.md` — if a spec exists, use it as the primary input
2. A file path provided by the user — review that file directly
3. No input provided — ask: "What would you like me to review? You can point me at a spec
   file, an existing class, or describe what you're planning to build."

---

## Step 3 — Mobile.Core Reuse Check

Before evaluating any new implementation or flagging something as missing, search the
MobileCore submodule for existing implementations that already solve the problem.

The MobileCore submodule lives at `MobileCore/src/` and contains these key projects:

| Project | What it contains |
|---|---|
| `Mobile.Core` | Extensions, utilities, database/service access layer, base manager, bus, TinyIoC |
| `Mobile.Core.Mvvm.Common` | Commands (`AsyncRelayCommand`, `RelayCommand`), collections (`ObservableRangeCollection`), converters, ViewModels, bindings |
| `Mobile.Core.Common.Android` / `.iOS` | Platform-specific utilities, permission services, dialog services |

**High-value areas to search first:**
- `Mobile.Core/Utilities/Extensions/` — string, list, enum, date, integer, currency, stream extensions
- `Mobile.Core/Utilities/` — `AsyncLock`, `Retry`, `OptionalResult<T>`, `LRUCache`, `AmountUtils`, `DateFormatUtility`, `PhoneNumberUtils`
- `Mobile.Core/SAL/` — `PersistentClient`, `RestClient`, `AuthRestClient`, base proxy contracts
- `Mobile.Core/DL/` — `DatabaseProxy`, `IAsyncDatabaseProxy`, `ISecureStore`
- `Mobile.Core/BL/Managers/BaseManager.cs` — base class all managers inherit from
- `Mobile.Core.Mvvm.Common/Commands/` — async and sync relay commands with cancellation support

**Rules:**
1. If an existing Core implementation covers the need: use it directly — do not reimplement it in RG.Mobile.Core
2. If an existing implementation is close but its signature or behavior would need to change to fit: **do not modify the existing Core implementation** — create a new class in the appropriate `MobileCore/src/Mobile.Core*` project, following the same conventions as adjacent code
3. If nothing relevant exists in Core: implement in `RG.Mobile.Core` per the project conventions

Report findings in the output under a **Mobile.Core Reuse** section:
- List what was searched
- Call out any existing implementation that should be used instead of a new one
- If a new Core implementation is recommended, name the target project and file path

---

## Step 4 — Run Standards Checks

Apply all checks relevant to the detected project pattern. Organize output by category.

---

### NAMING CONVENTIONS

**All projects:**
- [ ] Classes use PascalCase with no underscores
- [ ] Interfaces use the `I` prefix
- [ ] Async methods end with the `Async` suffix
- [ ] Boolean-returning methods use `Is`, `Has`, `Can`, or `Should` prefix
- [ ] Query methods use `Get` or `Select` prefix
- [ ] Public properties use PascalCase
- [ ] Private fields that back a property setter use the `_` prefix (`_camelCase`); other private fields use plain `camelCase` with no underscore
- [ ] Business logic classes named `{Domain}Manager`
- [ ] All managers have a corresponding `I{Domain}Manager` interface
- [ ] API communication classes named `{Domain}Proxy`
- [ ] Test classes named `{ClassUnderTest}Tests`
- [ ] Test fixture classes named `{Domain}Fixtures`
- [ ] Test methods follow `{MethodUnderTest}_{Scenario}_{ExpectedResult}`

---

### FILE STRUCTURE & LAYER PLACEMENT

- [ ] Business logic lives in `Managers/{Domain}/` — not in ViewModels or Proxies
- [ ] Each domain folder has exactly one interface and one implementation
- [ ] API communication classes live in `ServerAccess/Proxies/`
- [ ] DI registration lives exclusively in `Bootstrap.cs`
- [ ] Tests live in `Tests/.../Managers/{Domain}ManagerTests.cs`
- [ ] Platform-specific code does not live in the Core project
- [ ] If a change affects shared behavior, both Android and iOS platform projects are updated
- [ ] Shared logic is placed in Core — platform-specific logic is in the correct platform project
- [ ] Each layer only calls the layer directly below it — no layer skipping
- [ ] Models and entities contain no business logic

---

### ARCHITECTURE PATTERNS

- [ ] All business logic lives in a Manager — not in ViewModels, Proxies, or UI code
- [ ] Manager dependencies declared as `[Inject]` properties — not constructor parameters
- [ ] Proxy methods that need mocking are declared `public virtual`
- [ ] New domains registered in `Bootstrap.cs` as singletons
- [ ] New API endpoints have their own Proxy class
- [ ] Code handles network unavailability gracefully — API calls account for offline/unreachable scenarios

---

### DEPENDENCY INJECTION

- [ ] All registrations in `Bootstrap.cs` — no registration elsewhere
- [ ] Every registration uses `.AsSingleton()` unless there is an explicit reason otherwise
- [ ] No `Container.Resolve<T>()` calls in production code — use `[Inject]` properties
- [ ] Infrastructure registered before Managers
- [ ] Container not passed as a constructor argument

---

### ASYNC PATTERNS

**Modern async projects:**
- [ ] All database and API calls are async — no `.Result` or `.Wait()` blocking calls; if blocking is truly required, use `await RunWithConnectivity.RunWithGifLoadingAnimation(...)` instead
- [ ] All async methods return `Task` or `Task<T>` — never `async void` except event handlers
- [ ] All async methods include the `Async` suffix
- [ ] Test methods for async code are `public async Task` — not `async void`

**Legacy sync projects:**
- [ ] No `async/await` introduced to existing synchronous methods without a migration plan
- [ ] Threading done via existing patterns in the codebase — no mixing of Task-based async

**All async projects:**
- [ ] `ConfigureAwait(false)` used in library/Core project async methods where UI
  context is not needed
- [ ] `Task.Run()` not used to wrap synchronous work inside an async method signature —
  truly async I/O used instead
- [ ] No `async` methods with a single `await` at the end and no logic before it —
  remove `async/await` and return the Task directly

---

### ERROR HANDLING

- [ ] Specific exception types used where error type is meaningful to callers
- [ ] Exceptions not swallowed silently — always logged before catching and continuing
- [ ] Exceptions not used for control flow (e.g., not thrown to signal "not found")
- [ ] `finally` used to release resources or re-enable timers when needed
- [ ] User-facing error messages are generic — no exception messages, stack traces, or
  internal identifiers exposed to callers
- [ ] `catch (Exception)` not used unless rethrowing or logging at a top-level boundary
- [ ] `catch` and re-throw uses `throw;` — not `throw ex;` (preserves stack trace)
- [ ] Caught exceptions include enough context in the log message to identify the
  operation and relevant identifiers (e.g., order ID, location ID)

---

### LOCALIZATION

**Manager pattern projects:**
- [ ] New user-facing strings are defined in `.resx` resource files — not hardcoded inline
- [ ] String resources are provided for all supported languages: `en`, `es`, `fr`
- [ ] No raw string literals passed directly to UI components

---

### TESTING STANDARDS

**Manager pattern projects:**
- [ ] New `TinyIoCContainer` created per test class — not per test method
- [ ] Mocks registered on both the isolated container and `TinyIoCContainer.Current`
- [ ] SUT instantiated after all mocks are registered
- [ ] Test class implements `IDisposable` and disposes the container in `Dispose()`
- [ ] Each test covers exactly one behavior
- [ ] `[Fact]` for single-case tests, `[Theory]` + `[InlineData]` for input variations
- [ ] FluentAssertions used — no `Assert.Equal()` or similar xUnit primitives
- [ ] Every test has `// Arrange`, `// Act`, `// Assert` sections
- [ ] Fixture methods are `public static` factory methods in a dedicated Fixtures class
- [ ] New code that changes behavior has corresponding new or updated tests

---

### C# LANGUAGE CONVENTIONS

- [ ] All `using` statements explicit — no implicit usings
- [ ] Unused `using` statements removed before committing
- [ ] Access modifiers always specified explicitly
- [ ] `private readonly` for fields set in constructor and never changed
- [ ] `FirstOrDefault()` when zero results is valid; `First()` only when absence is a bug
- [ ] No more than 3–4 LINQ operations chained inline
- [ ] Public state exposed via properties — not public fields
- [ ] Class members appear in this order: `[Inject]` public properties, other public properties, private fields, constructor, public methods, private methods
- [ ] Nullable reference types respected — no `!` (null-forgiving) operators without a
  comment explaining why the compiler is wrong
- [ ] Null guard clauses at the top of public methods — fail fast before any work begins
- [ ] `string.IsNullOrWhiteSpace()` used when empty/whitespace are equally invalid;
  `string.IsNullOrEmpty()` only when whitespace is a meaningful value
- [ ] No magic strings or magic numbers — use `const`, `enum`, or a named static field
- [ ] Switch expressions preferred over `if/else if` chains with 3 or more branches
- [ ] Ternary operators used only for simple assignments — no nested ternaries, no
  ternaries with side effects
- [ ] Method parameter count does not exceed 4 — if more are needed, introduce a
  parameter object
- [ ] No `out` parameters on public API methods — return a result type instead

---

### NULL SAFETY & DEFENSIVE CODING

- [ ] Collections returned from public methods are never `null` — return empty
  collections instead (`Enumerable.Empty<T>()`, `new List<T>()`)
- [ ] Null-conditional operator (`?.`) used for single null checks; guard clauses used
  when null should be treated as an error

---

### DISPOSAL & RESOURCE MANAGEMENT

- [ ] Classes that own unmanaged resources or subscribe to events implement `IDisposable`
- [ ] `using` declarations (C# 8+) preferred over `using` statement blocks for
  single-scope disposables
- [ ] Event subscriptions have a corresponding unsubscription — no bare `+=` without
  a matching `-=` in `Dispose()` or a lifecycle method
- [ ] `await using` used for `IAsyncDisposable` — not `using` followed by manual dispose
- [ ] `HttpClient` not instantiated per-call — use a shared instance or factory

---

### CANCELLATION

- [ ] All public async methods that perform I/O accept a `CancellationToken` as the
  last parameter
- [ ] `CancellationToken` is passed through to every awaited call — not swallowed at
  the entry point
- [ ] `token.ThrowIfCancellationRequested()` called between logically distinct async
  steps in long-running operations
- [ ] `CancellationTokenSource` owned and cancelled by the object that created it —
  never passed to a collaborator that might cancel it independently

---

### API & DATA ACCESS

- [ ] HTTP endpoint paths defined as `private const string` at the top of the Proxy class
- [ ] All proxy methods `public virtual`
- [ ] Requests wrapped in the project's standard request envelope before serialization
- [ ] JSON serialization via Newtonsoft.Json

---

### DATA PERSISTENCE

- [ ] The full DTO is stored locally — not a trimmed or re-mapped subset
- [ ] If a record is stored locally without a mobile GUID, verify this is intentional — most locally persisted records should include one
- [ ] For RealGreen: locally stored records live in a separate table as individual rows — not serialized as JSON blobs (PestPac and WinTeam use JSON blobs; RealGreen does not)

---

## Step 5 — Format Output

Return findings in this structure:

```
## Standards Check: {feature or file name}
**Project pattern detected:** {pattern}
**Date:** {today}

### ✅ Looks Good
{List items that are clearly correct — brief, one line each}

### ⚠️ Needs Attention
{List items that need improvement — include the specific issue and a suggested fix}

### 🔴 Violations
{List clear violations — include the specific problem, where it occurs, and what the
correct pattern is with a short code example if helpful}

### 💡 Suggestions
{Optional improvements that go beyond standards — things that would make the code
better but aren't strictly required}
```

If no violations are found, say so explicitly — an empty violations section is a
meaningful result.
