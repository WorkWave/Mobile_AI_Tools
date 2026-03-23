# /tests — Test Suite Generator

Generate a complete test suite for a feature using the spec and adversarial findings
as inputs. Tests cover happy paths from the spec and unhappy paths from the adversarial
analysis — not just one or the other.

---

## Step 1 — Detect Project Context

Silently inspect the working directory:

1. Read `CLAUDE.md` if present
2. Check namespace patterns and structural markers
3. Confirm: testing framework (xUnit, NUnit, MSTest), assertion library (FluentAssertions
   or other), mocking library (Moq or other), DI container (TinyIoC or manual construction)
4. If no test project exists, note this and ask whether to create one or generate
   test code for review only

---

## Step 2 — Locate Input

Require both inputs before generating tests. Check for:

1. `/specs/{feature-name}/spec.md` — acceptance criteria and architecture notes
2. `/specs/{feature-name}/adversarial-findings.md` — failure modes and test cases to write

If adversarial findings are missing, ask:
> "I have the spec but no adversarial findings. Run `/adversarial-check` first for
> the best test coverage, or tell me to proceed with happy-path tests only."

---

## Step 3 — Plan the Test Suite

Before writing any test code, produce a test plan and ask the user to confirm it.

```
## Test Plan: {Feature Name}

### Happy Path Tests (from spec acceptance criteria)
{List each test — method name and one-line description}

### Unhappy Path Tests (from adversarial findings)
{List each test — method name, one-line description, finding it covers}

### Edge Case Tests
{List each test — method name and one-line description}

**Total tests planned:** {n}
**Estimated coverage area:** {which classes/methods will be exercised}

Confirm this plan or tell me what to add, remove, or change.
```

---

## Step 4 — Generate Test Code

After plan confirmation, generate the full test file following project conventions.

---

### MANAGER PATTERN PROJECTS — Test Structure

```csharp
// File location: Tests/{ProjectName}.Tests/Managers/{Domain}ManagerTests.cs
// Namespace: {ProjectName}.Tests.Managers

public class {Domain}ManagerTests : IDisposable
{
    // ── Fields ────────────────────────────────────────────────────────
    private readonly TinyIoCContainer _container;
    private readonly Mock<I{Dependency}> _mock{Dependency};
    // add one field per mock dependency
    private readonly I{Domain}Manager _sut;

    // ── Constructor ───────────────────────────────────────────────────
    public {Domain}ManagerTests()
    {
        _container = new TinyIoCContainer();

        _mock{Dependency} = new Mock<I{Dependency}>();

        // Register on both containers — required for RGBaseManager.BuildUp()
        _container.Register(_mock{Dependency}.Object);
        TinyIoCContainer.Current.Register(_mock{Dependency}.Object);

        _container.Register<I{Domain}Manager, {Domain}Manager>();
        _sut = new {Domain}Manager();
    }

    // ── Tests ─────────────────────────────────────────────────────────

    [Fact]
    public async Task {MethodName}_{Scenario}_{ExpectedResult}()
    {
        // Arrange
        var fixture = {Domain}Fixtures.Standard{Entity}();
        _mock{Dependency}
            .Setup(x => x.{Method}(It.IsAny<{Type}>()))
            .ReturnsAsync(fixture);

        // Act
        var result = await _sut.{MethodName}({args});

        // Assert
        result.Should().NotBeNull();
        result.Should().BeEquivalentTo(fixture);
    }

    // ── Disposal ──────────────────────────────────────────────────────
    public void Dispose() => _container?.Dispose();
}
```

---

### REPOSITORY PATTERN PROJECTS — Test Structure

```csharp
// Adapt to the project's existing test patterns
// Use constructor injection for dependencies
// Follow the same AAA structure

public class {Entity}RepositoryTests
{
    private readonly Mock<IConnection> _mockConnection;
    private readonly {Entity}Repository _sut;

    public {Entity}RepositoryTests()
    {
        _mockConnection = new Mock<IConnection>();
        _sut = new {Entity}Repository(_mockConnection.Object);
    }

    [Fact]
    public void {MethodName}_{Scenario}_{ExpectedResult}()
    {
        // Arrange
        // Act
        // Assert
    }
}
```

---

### TEST NAMING RULES

Always follow: `{MethodUnderTest}_{Scenario}_{ExpectedResult}`

```
✅ GetEmployeesAsync_WithNoEmployees_ReturnsEmptyList
✅ SubmitPaymentAsync_WithNegativeAmount_ThrowsArgumentException
✅ HasPermission_WithDeactivatedEmployee_ReturnsFalse
✅ SyncQueue_WhenNetworkFailsMidBatch_RetainsUnprocessedItems

❌ TestGetEmployees
❌ GetEmployees_Test1
❌ ShouldReturnEmployees
```

---

### ASSERTION RULES

Always use FluentAssertions. Never use `Assert.Equal()` or xUnit primitives.

```csharp
// Return value assertions
result.Should().NotBeNull();
result.Should().Be(expected);
result.Should().BeEquivalentTo(expected);
result.Should().HaveCount(3);
result.Should().BeEmpty();
result.Should().BeTrue();

// Exception assertions
await action.Should().ThrowAsync<ArgumentException>();
await action.Should().ThrowAsync<ArgumentException>()
    .WithMessage("*expected message*");

// Mock interaction assertions
_mockDependency.Verify(x => x.Method(It.IsAny<Type>()), Times.Once);
_mockDependency.Verify(x => x.Method(It.IsAny<Type>()), Times.Never);
```

---

### FIXTURE RULES

Generate a companion Fixtures file alongside the test file.

```csharp
// File: Tests/{ProjectName}.Tests/Fixtures/{Domain}Fixtures.cs

public static class {Domain}Fixtures
{
    // Standard happy-path object
    public static {Entity} Standard{Entity}() => new {Entity}
    {
        // populate with realistic but non-sensitive values
    };

    // Scenario-specific variants
    public static {Entity} {Entity}With{Condition}() => new {Entity}
    {
        // populate for the specific scenario
    };

    // Collections
    public static IEnumerable<{Entity}> Multiple{Entities}() =>
        new List<{Entity}> { Standard{Entity}(), {Entity}With{Condition}() };

    public static IEnumerable<{Entity}> Empty{Entity}List() =>
        Enumerable.Empty<{Entity}>();
}
```

---

### THEORY TESTS FOR INPUT VARIATIONS

Use `[Theory]` + `[InlineData]` when the same test logic applies across multiple inputs.
This is the right pattern for boundary condition tests from the adversarial findings.

```csharp
[Theory]
[InlineData(null)]
[InlineData("")]
[InlineData(" ")]
[InlineData("a very long string that exceeds expected input length...")]
public async Task {MethodName}_WithInvalidInput_ThrowsArgumentException(string input)
{
    // Arrange
    // Act
    var action = async () => await _sut.{MethodName}(input);

    // Assert
    await action.Should().ThrowAsync<ArgumentException>();
}
```

---

## Step 5 — Output Files

Create the following files:

```
/specs/{feature-name}/
  tests-plan.md        ← the confirmed test plan

Tests/{ProjectName}.Tests/Managers/{Domain}ManagerTests.cs   ← test file
Tests/{ProjectName}.Tests/Fixtures/{Domain}Fixtures.cs       ← fixture file
```

---

## Step 6 — Run Tests

After generating, run the tests immediately:

```bash
dotnet test --filter "FullyQualifiedName~{Domain}ManagerTests"
```

Check results and respond to each outcome:

- **Compile error** — fix the error before continuing; do not ask the user to fix it
- **Tests fail as expected (red)** — this is correct; proceed to Step 7
- **Tests unexpectedly pass** — flag this explicitly:
  > "Warning: {n} tests are passing before implementation exists. This usually means
  > the test isn't asserting correctly. Review these before proceeding."
- **Any test fails for the wrong reason** — diagnose and fix; offer a corrected version

If fixes are needed, re-run until the suite compiles cleanly and only fails for
the right reasons (missing implementation).

---

## Step 7 — Report and Follow-up

Generate a report file:

**Location:** `Tests/reports/tests-{feature-name}-{timestamp}.md`

```markdown
# Test Generation Report

**Generated:** {timestamp}
**Feature:** {feature-name}
**Spec:** /specs/{feature-name}/spec.md
**Adversarial findings:** /specs/{feature-name}/adversarial-findings.md

---

## Summary

| Metric | Value |
|--------|-------|
| Test file | {path} |
| Fixture file | {path} |
| Total tests | {n} |
| Happy path tests | {n} |
| Unhappy path tests | {n} |
| Edge case tests | {n} |
| Compile status | {Clean / Errors} |
| Tests red (expected) | {n} |
| Tests unexpectedly passing | {n} |

---

## Tests Created

| # | Test Name | Type | Status |
|---|-----------|------|--------|
{rows}

---

## Adversarial Findings Not Coverable by Unit Tests

{List any findings that require integration tests, infrastructure changes,
or runtime conditions — with a note on how they should be validated instead.
If none, write "None — all findings are covered."}

---

## Next Steps

- [ ] Confirm all red tests are failing for the right reasons
- [ ] Proceed to implementation: run `/implement` Phase 5
- [ ] After implementation, re-run: `dotnet test`
```

After generating the report, ask:
> "Are there additional test scenarios you'd like to add before we move to implementation?"
