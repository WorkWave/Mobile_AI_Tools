# C# XUnit Complete Coverage Generation

Generate comprehensive test coverage for all C# classes in the project.

## Usage

```
/project:testing/coverage[directory]
```

## Arguments

- `$ARGUMENTS` - Optional: Directory containing services/models (default: auto-detect)

## Instructions

When invoked, execute this multi-step workflow:

### Step 1: Analyze the Codebase

1. Find all classes that need testing:
   - Search in `Services/`, `src/`, `Models/`, `Repositories/`, or similar directories
   - Look for classes like services, repositories, handlers, processors, validators
2. Identify existing test coverage:
   - Check `Tests/` or `Tests/Unit/` for existing test classes
   - Note which classes have tests and which don't

### Step 2: Create Coverage Report

Generate a summary:

```
## Coverage Analysis

### Classes Found:
- OrderService (/Services/OrderService.cs)
- UserRepository (/Repositories/UserRepository.cs)
- PaymentProcessor (/Services/PaymentProcessor.cs)

### Existing Tests:
- OrderServiceTests.cs (5 tests)

### Missing Coverage:
- UserRepository (no fixture, no tests)
- PaymentProcessor (fixture exists, no tests)
```

### Step 3: Generate Missing Fixtures

For each class without fixtures:

1. Read the class structure and its dependencies
2. Create a fixture class with:
   - `Standard{Name}()` - Happy path
   - `Empty{Name}()` - Empty/minimal data
   - `NotFound()` - Null/error case
   - `Invalid{Name}()` - Invalid state for validation testing
3. Save to `Tests/Fixtures/{ClassName}Fixtures.cs`

### Step 4: Generate Missing Tests

For each class without tests:

1. Read the class and fixture
2. Create a test class with:
   - Happy path test
   - Empty input test
   - Not found test
   - Theory test for input variations
   - Exception handling test
   - Mock verification test
3. Save to `Tests/{ClassName}Tests.cs`

### Step 5: Run All Tests

Execute the test suite:

```bash
dotnet test
```

Report results:
- Total tests
- Passed/Failed/Skipped
- Any failures to investigate

### Step 6: Generate Final Report

```
## Coverage Generation Complete

### Created:
- Fixtures: 3 new classes (12 methods)
- Tests: 3 new classes (18 tests)

### Test Results:
- Total: 23 tests
- Passed: 23
- Failed: 0

### Coverage Improvement:
- Before: 25% class coverage
- After: 100% class coverage

### Files Created:
- Tests/Fixtures/UserRepositoryFixtures.cs
- Tests/Fixtures/PaymentProcessorFixtures.cs
- Tests/UserRepositoryTests.cs
- Tests/PaymentProcessorTests.cs
```

## Options

Add to `$ARGUMENTS`:
- `--fixtures-only` - Only generate fixtures
- `--tests-only` - Only generate tests (assumes fixtures exist)
- `--dry-run` - Show what would be created without creating files

## Example Output

```
Analyzing codebase...

Found 4 classes to test:
  - OrderService
  - UserRepository
  - PaymentProcessor
  - NotificationService

Existing coverage:
  - OrderServiceTests.cs (5 tests)

Generating missing coverage...

Created UserRepositoryFixtures.cs:
  - StandardUser() - typical user data
  - EmptyUser() - minimal user data
  - AdminUser() - user with admin role
  - NotFound() - Returns null

Created UserRepositoryTests.cs:
  - GetUser_WithValidId_ReturnsUser
  - GetUser_WithInvalidId_ReturnsNull
  - CreateUser_WithValidData_ReturnsCreatedUser
  - CreateUser_WhenRepositoryThrows_PropagatesException

Running tests...
All 23 tests passing.

Coverage complete!
```

## After Generation

1. Generate the report file
2. Show summary of what was created
3. Run all tests and show results
4. Highlight any failures that need attention
5. Offer to add more edge case tests

### Step 7: Generate Report

Create a markdown report file in `Tests/reports/`:

**Filename format:** `coverage-generation-{timestamp}.md`

**Example:** `Tests/reports/coverage-generation-2026-01-20-144530.md`

```markdown
# Coverage Generation Report

**Generated:** 2026-01-20 14:45:30
**Command:** /csharp-coverage
**Scope:** Full codebase

---

## Executive Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Classes with Fixtures | 1 | 4 | +3 |
| Classes with Tests | 1 | 4 | +3 |
| Total Test Count | 5 | 23 | +18 |
| Class Coverage | 25% | 100% | +75% |

---

## Classes Discovered

| Class | Location | Status |
|-------|----------|--------|
| OrderService | Services/OrderService.cs | Existing |
| UserRepository | Repositories/UserRepository.cs | New Coverage |
| PaymentProcessor | Services/PaymentProcessor.cs | New Coverage |
| NotificationService | Services/NotificationService.cs | New Coverage |

---

## Fixtures Created

| Fixture Class | Methods | Location |
|---------------|---------|----------|
| UserRepositoryFixtures.cs | 4 | Tests/Fixtures/ |
| PaymentProcessorFixtures.cs | 4 | Tests/Fixtures/ |
| NotificationServiceFixtures.cs | 4 | Tests/Fixtures/ |

### Fixture Details

#### UserRepositoryFixtures.cs
- `StandardUser()` - typical user with profile
- `EmptyUser()` - minimal user data
- `AdminUser()` - user with admin role
- `NotFound()` - Returns null

#### PaymentProcessorFixtures.cs
- `SuccessfulPayment()` - completed payment
- `PendingPayment()` - payment in progress
- `FailedPayment()` - declined payment
- `NotFound()` - Returns null

---

## Tests Created

| Test Class | Tests | Passed | Failed |
|------------|-------|--------|--------|
| UserRepositoryTests.cs | 6 | 6 | 0 |
| PaymentProcessorTests.cs | 6 | 6 | 0 |
| NotificationServiceTests.cs | 6 | 6 | 0 |
| **Total** | **18** | **18** | **0** |

---

## Test Execution Results

```
dotnet test

Test run successful.
Total tests: 20
     Passed: 20
     Failed: 0
   Skipped: 0
  Duration: 3.4s
```

---

## Files Created

### Fixtures
- `Tests/Fixtures/UserRepositoryFixtures.cs`
- `Tests/Fixtures/PaymentProcessorFixtures.cs`
- `Tests/Fixtures/NotificationServiceFixtures.cs`

### Tests
- `Tests/UserRepositoryTests.cs`
- `Tests/PaymentProcessorTests.cs`
- `Tests/NotificationServiceTests.cs`

---

## Recommendations

- [ ] Review generated fixtures for realistic data
- [ ] Add integration tests for service interactions
- [ ] Consider adding performance tests for large datasets
- [ ] Run coverage analysis: `/csharp-analyze coverage`
```

**Important:** Always create the `Tests/reports/` directory if it doesn't exist before saving the report.
