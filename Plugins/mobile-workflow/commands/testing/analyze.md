# C# XUnit Coverage Analysis

Analyze test coverage and identify gaps.

## Usage

```
/project:testing/analyze [options]
```

## Arguments

- `$ARGUMENTS` - Options: `coverage`, `gaps`, `quality`, or empty for full analysis

## Instructions

When invoked, perform comprehensive test analysis:

### Step 1: Run Coverage Analysis

Execute code coverage:

```bash
dotnet test --collect:"XPlat Code Coverage"
```

Or with specific coverage tool:

```bash
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura
```

### Step 2: Analyze Coverage Report

Parse the coverage output and generate a report:

```
## Coverage Report

### Overall Coverage:
- Line Coverage: 75%
- Branch Coverage: 68%
- Method Coverage: 82%

### By Namespace:
| Namespace | Line % | Branch % |
|-----------|--------|----------|
| Services | 85% | 78% |
| Models | 90% | 85% |
| Repositories | 65% | 55% |

### Uncovered Areas:
- Services/OrderService.cs: Lines 45-67 (error handling)
- Repositories/UserRepository.cs: Lines 120-145 (retry logic)
```

### Step 3: Identify Test Quality Issues

Analyze existing tests for:

1. **Weak Assertions**
   - Tests with no assertions
   - Tests that only check for non-null
   - Missing mock verifications

2. **Missing Edge Cases**
   - No empty/null input tests
   - No error handling tests
   - No boundary condition tests

3. **Test Organization**
   - Tests without proper naming
   - Missing XML documentation
   - Mixed unit/integration tests

### Step 4: Gap Analysis

```
## Test Gap Analysis

### Missing Tests:
| Class/Feature | Gap | Priority |
|---------------|-----|----------|
| OrderService | No error handling tests | High |
| PaymentProcessor | No timeout test | Medium |
| UserRepository | Missing edge cases | Low |

### Recommended Tests to Add:
1. OrderService_WhenRepositoryThrows_HandlesGracefully
2. PaymentProcessor_WhenTimeout_ReturnsAppropriateError
3. UserRepository_WithMalformedData_HandlesGracefully
```

### Step 5: Quality Recommendations

```
## Quality Improvements

### High Priority:
1. Add error handling tests for OrderService
2. Strengthen assertions in UserServiceTests
3. Add mock verifications to all tests

### Medium Priority:
1. Add timeout tests for async operations
2. Increase branch coverage in Services/
3. Add parameterized tests for input variations

### Low Priority:
1. Add XML documentation to test methods
2. Refactor test setup into shared fixtures
3. Add integration test suite
```

### Step 6: Generate Improvement Tests

If `gaps` option specified, generate tests for identified gaps:

1. Create test methods for uncovered code paths
2. Add edge case tests for each tool
3. Strengthen weak assertions

## Analysis Options

### `coverage`
Run and report code coverage metrics only.

### `gaps`
Identify missing tests and offer to generate them.

### `quality`
Analyze test quality (assertions, organization, documentation).

### (empty)
Full analysis: coverage + gaps + quality.

## Example Output

```
Running coverage analysis...

## Coverage Summary
- Line: 78% (+3% from last run)
- Branch: 72%
- Class Coverage: 100%

## Gaps Identified
3 high-priority gaps found:

1. OrderService error handling (0% covered)
   - Lines 45-67 handle repository errors
   - No tests verify error behavior

2. PaymentProcessor retry logic (0% covered)
   - Lines 120-145 implement retry
   - No tests for retry scenarios

3. UserRepository null handling
   - Null user returns not tested

## Quality Issues
- 2 tests have weak assertions (only null checks)
- 5 tests missing mock verifications
- 3 test methods lack XML documentation

## Recommendations
Would you like me to:
1. Generate tests for the 3 high-priority gaps?
2. Strengthen the weak assertions?
3. Add mock verifications to existing tests?
```

## After Analysis

1. Generate the report file
2. Present coverage metrics
3. List identified gaps with priorities
4. Offer to generate missing tests
5. Offer to improve existing test quality

### Step 7: Generate Report

Create a markdown report file in `Tests/reports/`:

**Filename format:** `analyze-{option}-{timestamp}.md`

**Examples:**
- `Tests/reports/analyze-full-2026-01-20-151530.md`
- `Tests/reports/analyze-coverage-2026-01-20-151530.md`
- `Tests/reports/analyze-gaps-2026-01-20-151530.md`
- `Tests/reports/analyze-quality-2026-01-20-151530.md`

```markdown
# Test Analysis Report

**Generated:** 2026-01-20 15:15:30
**Command:** /analyze
**Analysis Type:** Full (coverage + gaps + quality)

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Line Coverage | 78% | ⚠️ Below 80% target |
| Branch Coverage | 72% | ⚠️ Below 75% target |
| Method Coverage | 85% | ✅ Good |
| Class Coverage | 100% | ✅ Complete |
| High Priority Gaps | 3 | ⚠️ Needs attention |
| Quality Issues | 10 | ⚠️ Needs attention |

---

## Coverage Analysis

### Overall Metrics

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| Line Coverage | 78% | 80% | -2% |
| Branch Coverage | 72% | 75% | -3% |
| Method Coverage | 85% | 80% | +5% |

### Coverage by Namespace

| Namespace | Lines | Branches | Methods |
|-----------|-------|----------|---------|
| Services | 85% | 78% | 92% |
| Models | 90% | 85% | 95% |
| Repositories | 65% | 55% | 75% |
| Fixtures | 100% | 100% | 100% |

### Uncovered Code

| File | Lines | Description |
|------|-------|-------------|
| Services/OrderService.cs | 45-67 | Error handling paths |
| Services/PaymentProcessor.cs | 120-145 | Retry logic |
| Repositories/UserRepository.cs | 200-215 | Timeout handling |

---

## Gap Analysis

### High Priority Gaps

| # | Class/Feature | Gap | Impact |
|---|---------------|-----|--------|
| 1 | OrderService | No error handling tests | Critical path untested |
| 2 | PaymentProcessor | No retry logic tests | Failure scenarios untested |
| 3 | UserRepository | No timeout tests | Edge case untested |

### Medium Priority Gaps

| # | Class/Feature | Gap | Impact |
|---|---------------|-----|--------|
| 4 | CacheService | No concurrent access test | Race conditions untested |
| 5 | DataValidator | No malformed data test | Input validation untested |

### Recommended Tests to Add

1. `OrderService_WhenRepositoryThrows_HandlesGracefully`
2. `PaymentProcessor_WhenRetryExceeded_ThrowsException`
3. `UserRepository_WhenTimeout_ReturnsAppropriateError`
4. `CacheService_WithConcurrentAccess_HandlesCorrectly`
5. `DataValidator_WithMalformedData_HandlesGracefully`

---

## Quality Analysis

### Weak Assertions Found

| Test | Issue | Recommendation |
|------|-------|----------------|
| GetOrder_Basic | Only checks non-null | Add property assertions |
| GetUsers_Empty | No verification | Add mock verification |

### Missing Mock Verifications

| Test Class | Tests Missing Verify |
|------------|---------------------|
| OrderServiceTests.cs | 2 tests |
| UserServiceTests.cs | 3 tests |

### Documentation Issues

| Issue | Count | Files |
|-------|-------|-------|
| Missing XML docs | 5 | OrderServiceTests.cs, UserServiceTests.cs |
| Inconsistent naming | 2 | PaymentProcessorTests.cs |

### Test Organization

| Issue | Description |
|-------|-------------|
| Mixed concerns | Some tests mix unit and integration patterns |
| Setup duplication | Similar setup code in multiple test classes |

---

## Recommendations

### High Priority
- [ ] Add error handling tests for OrderService (Lines 45-67)
- [ ] Add retry logic tests for PaymentProcessor (Lines 120-145)
- [ ] Strengthen assertions in OrderServiceTests

### Medium Priority
- [ ] Add timeout tests for async operations
- [ ] Increase branch coverage in Services/ namespace
- [ ] Add mock verifications to all tests

### Low Priority
- [ ] Add XML documentation to test methods
- [ ] Refactor test setup into shared fixtures
- [ ] Consider integration test suite

---

## Action Items

Would you like me to:
1. Generate tests for the 3 high-priority gaps? → `/csharp-test OrderService`
2. Strengthen the weak assertions?
3. Add mock verifications to existing tests?
4. Run `/csharp-coverage` to generate missing fixtures and tests?

---

## Trend (if historical data available)

| Metric | Last Run | Current | Change |
|--------|----------|---------|--------|
| Line Coverage | 75% | 78% | +3% |
| Failing Tests | 2 | 0 | -2 |
| Gap Count | 5 | 3 | -2 |
```

**Important:** Always create the `Tests/reports/` directory if it doesn't exist before saving the report.
