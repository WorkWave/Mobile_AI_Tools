# C# XUnit Test Debugging

Debug and fix failing XUnit tests.

## Usage

```
/project:testing/debug <test-name-or-error>
```

## Arguments

- `$ARGUMENTS` - The failing test name, error message, or "all" to debug all failures

## Instructions

When invoked, follow this debugging workflow:

### Step 1: Identify the Failure

If a specific test name is provided:
1. Find the test file containing the test
2. Read the test implementation

If "all" is specified or an error message is provided:
1. Run `dotnet test` to identify all failures
2. Parse the error output to identify failing tests

### Step 2: Analyze the Test

For each failing test:

1. **Read the test code** - Understand what's being tested
2. **Read the fixture** - Check the mock data being used
3. **Identify the error** - Parse the exception/assertion failure
4. **Trace the cause** - Follow the code path to find the root cause

### Step 3: Common Issues Checklist

Check for these common problems:

```
[ ] Null reference - Missing null checks or fixture returning null
[ ] Type mismatch - Model changed but fixture not updated
[ ] Mock setup - Mock not configured for the actual call being made
[ ] Async issue - Missing await or incorrect async pattern
[ ] Assertion - Assertion checking wrong property or value
[ ] Date issue - Hardcoded dates that have expired
[ ] Missing dependency - Required service not mocked
```

### Step 4: Debug Output

Provide analysis:

```
## Debug Analysis: {TestName}

### Error:
System.NullReferenceException at line 45

### Root Cause:
The fixture `StandardCustomer()` returns a response with null `ServiceHistory`,
but the test expects it to contain items.

### Location:
- Test: Tests/Tools/CustomerHistoryTests.cs:45
- Fixture: Tests/Fixtures/CustomerHistoryFixtures.cs:23

### Fix Required:
Update the fixture to include a non-null ServiceHistory list.
```

### Step 5: Implement Fix

1. Make the necessary code changes
2. Explain what was changed and why
3. Run the test again to verify the fix

### Step 6: Verify Fix

```bash
dotnet test --filter "FullyQualifiedName~{TestName}"
```

Report:
- Test result (pass/fail)
- If still failing, continue debugging
- If passing, summarize the fix

## Example Session

```
User: /project:debug CreateOrder_WithLargeOrder_HandlesCorrectly

Claude:
Analyzing failing test...

## Debug Analysis: CreateOrder_WithLargeOrder_HandlesCorrectly

### Error:
System.NullReferenceException: Object reference not set
  at OrderServiceTests.CreateOrder_WithLargeOrder_HandlesCorrectly() line 67

### Investigation:
1. Reading test at Tests/OrderServiceTests.cs:67
2. Test calls OrderFixtures.LargeOrder()
3. Reading fixture at Tests/Fixtures/OrderFixtures.cs:45

### Root Cause:
The `LargeOrder()` fixture initializes `Items` but sets `ShippingAddress` to null.
The test on line 67 accesses `order.ShippingAddress.City` without null check.

### Fix Options:
1. Update fixture to include ShippingAddress (recommended)
2. Add null check in test assertion

Implementing fix #1...

Updated OrderFixtures.cs:
- LargeOrder() now returns ShippingAddress = new Address { ... }

Running test...
Test passed!

### Summary:
Fixed by initializing ShippingAddress in LargeOrder() fixture.
```

## Batch Debugging

For `$ARGUMENTS = all`:

```bash
dotnet test
```

Then for each failure:
1. Group failures by root cause if similar
2. Fix systematically
3. Re-run after each fix
4. Report final status

## After Debugging

1. Generate the report file
2. Summarize all fixes made
3. Run full test suite to ensure no regressions
4. Suggest preventive measures (e.g., fixture validation)

### Step 7: Generate Report

Create a markdown report file in `Tests/reports/`:

**Filename format:** `debug-{TestName}-{timestamp}.md`

**Example:** `Tests/reports/debug-CreateOrder-2026-01-20-145830.md`

```markdown
# Debug Report

**Generated:** 2026-01-20 14:58:30
**Command:** /debug CreateOrder_WithLargeOrder_HandlesCorrectly
**Test:** CreateOrder_WithLargeOrder_HandlesCorrectly

---

## Summary

| Metric | Value |
|--------|-------|
| Tests Debugged | 1 |
| Issues Found | 1 |
| Issues Fixed | 1 |
| Final Status | Passing |

---

## Initial Error

```
System.NullReferenceException: Object reference not set
  at OrderServiceTests.CreateOrder_WithLargeOrder_HandlesCorrectly() line 67
```

---

## Root Cause Analysis

| # | Finding | Location |
|---|---------|----------|
| 1 | `LargeOrder()` fixture sets `ShippingAddress` to null | Tests/Fixtures/OrderFixtures.cs:45 |
| 2 | Test accesses `order.ShippingAddress.City` without null check | Tests/OrderServiceTests.cs:67 |

### Investigation Path
1. Read test at Tests/OrderServiceTests.cs:67
2. Test calls OrderFixtures.LargeOrder()
3. Read fixture at Tests/Fixtures/OrderFixtures.cs:45
4. Found `ShippingAddress` property is null

---

## Fix Applied

### File Modified
`Tests/Fixtures/OrderFixtures.cs`

### Change
```csharp
// Before
ShippingAddress = null

// After
ShippingAddress = new Address { City = "Portland", State = "OR" }
```

### Rationale
Initialize ShippingAddress to prevent NullReferenceException. Default address is valid for testing.

---

## Verification

```
dotnet test --filter "FullyQualifiedName~CreateOrder_WithLargeOrder_HandlesCorrectly"

Test run successful.
Total tests: 1
     Passed: 1
     Failed: 0
  Duration: 0.8s
```

---

## Full Test Suite Check

```
dotnet test

Test run successful.
Total tests: 15
     Passed: 15
     Failed: 0
  Duration: 3.2s
```

No regressions introduced.

---

## Files Modified

- `Tests/Fixtures/DailySummaryFixtures.cs` - Added Timers initialization

---

## Recommendations

- [ ] Add null-safety checks to other fixtures
- [ ] Consider adding fixture validation tests
- [ ] Review similar patterns in other tests
```

**For batch debugging (`all`):**

**Filename format:** `debug-batch-{timestamp}.md`

```markdown
# Batch Debug Report

**Generated:** 2026-01-20 15:10:45
**Command:** /debug all
**Scope:** All failing tests

---

## Summary

| Metric | Before | After |
|--------|--------|-------|
| Total Tests | 15 | 15 |
| Passing | 12 | 15 |
| Failing | 3 | 0 |
| Fixed | - | 3 |

---

## Failures Analyzed

| # | Test | Error | Root Cause | Status |
|---|------|-------|------------|--------|
| 1 | CreateOrder_WithLargeOrder_HandlesCorrectly | NullReferenceException | Null ShippingAddress in fixture | Fixed |
| 2 | GetUsers_WithNoUsers_ReturnsEmpty | AssertionException | Wrong fixture used | Fixed |
| 3 | ProcessPayment_WithValidRequest_ReturnsSuccess | MockException | Mock not configured | Fixed |

---

## Fixes Applied

### Fix 1: OrderFixtures.cs
- Issue: `LargeOrder()` returned null ShippingAddress
- Fix: Initialize `ShippingAddress = new Address { ... }`

### Fix 2: UserServiceTests.cs
- Issue: Test used `StandardUsers()` instead of `NoUsers()`
- Fix: Changed fixture call to `UserFixtures.NoUsers()`

### Fix 3: PaymentProcessorTests.cs
- Issue: Mock setup missing parameter match
- Fix: Updated mock setup to use `It.IsAny<string>()`

---

## Files Modified

- `Tests/Fixtures/OrderFixtures.cs`
- `Tests/UserServiceTests.cs`
- `Tests/PaymentProcessorTests.cs`
```

**Important:** Always create the `Tests/reports/` directory if it doesn't exist before saving the report.
