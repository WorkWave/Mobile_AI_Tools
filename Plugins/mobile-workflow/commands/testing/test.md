# C# XUnit Test Scaffolding

Generate an XUnit test class for a C# class or service.

## Usage

```
/project:testing/test <class-name>
```

## Arguments

- `$ARGUMENTS` - The class or service name to generate tests for (e.g., `OrderService`, `UserRepository`, `PaymentProcessor`)

## Instructions

When invoked, follow these steps:

### Step 1: Gather Context

1. Read the class under test in `Services/`, `src/`, or relevant directory
2. Read the fixture class in `Tests/Fixtures/` (or generate one if missing)
3. Check existing test patterns in `Tests/` or `Tests/Unit/`
4. Identify the mocking framework used (Moq, NSubstitute, etc.)
5. Identify dependencies that need to be mocked
6. Use the TECHNICAL_GUIDE.md in docs/TinyIoC as a context pack

### Step 2: Generate the Test Class

Create a comprehensive XUnit test class:

```csharp
using FluentAssertions;
using Moq;
using Xunit;
using System.Threading.Tasks;

namespace {Namespace}.Tests
{
    /// <summary>
    /// Unit tests for the {ClassName} class.
    /// </summary>
    public class {ClassName}Tests
    {
        private readonly Mock<I{Dependency}> _mock{Dependency};
        private readonly {ClassName} _sut;

        public {ClassName}Tests()
        {
            _mock{Dependency} = new Mock<I{Dependency}>();
            _sut = new {ClassName}(_mock{Dependency}.Object);
        }

        #region Happy Path Tests

        [Fact]
        public async Task {MethodName}_WithValidInput_ReturnsExpectedResult()
        {
            // Arrange
            var input = {ClassName}Fixtures.StandardInput();
            var expected = {ClassName}Fixtures.StandardResult();

            _mock{Dependency}
                .Setup(x => x.{DependencyMethod}(It.IsAny<{ParamType}>()))
                .ReturnsAsync(expected);

            // Act
            var result = await _sut.{MethodName}(input);

            // Assert
            result.Should().NotBeNull();
            result.Should().BeEquivalentTo(expected);
            _mock{Dependency}.Verify(
                x => x.{DependencyMethod}(It.IsAny<{ParamType}>()),
                Times.Once);
        }

        #endregion

        #region Edge Case Tests

        [Fact]
        public async Task {MethodName}_WithEmptyInput_HandlesGracefully()
        {
            // Arrange
            var input = {ClassName}Fixtures.EmptyInput();

            // Act
            var result = await _sut.{MethodName}(input);

            // Assert
            result.Should().NotBeNull();
        }

        [Fact]
        public async Task {MethodName}_WithNotFound_ReturnsNull()
        {
            // Arrange
            var input = {ClassName}Fixtures.StandardInput();

            _mock{Dependency}
                .Setup(x => x.{DependencyMethod}(It.IsAny<{ParamType}>()))
                .ReturnsAsync((ResultType?)null);

            // Act
            var result = await _sut.{MethodName}(input);

            // Assert
            result.Should().BeNull();
        }

        #endregion

        #region Parameterized Tests

        [Theory]
        [InlineData("value1")]
        [InlineData("value2")]
        [InlineData("value3")]
        public async Task {MethodName}_WithVariousInputs_ProcessesCorrectly(string inputValue)
        {
            // Arrange
            var input = new InputType { Value = inputValue };

            _mock{Dependency}
                .Setup(x => x.{DependencyMethod}(It.IsAny<{ParamType}>()))
                .ReturnsAsync({ClassName}Fixtures.StandardResult());

            // Act
            var result = await _sut.{MethodName}(input);

            // Assert
            result.Should().NotBeNull();
            _mock{Dependency}.Verify(
                x => x.{DependencyMethod}(It.IsAny<{ParamType}>()),
                Times.Once);
        }

        #endregion

        #region Exception Tests

        [Fact]
        public async Task {MethodName}_WhenDependencyThrows_PropagatesException()
        {
            // Arrange
            var input = {ClassName}Fixtures.StandardInput();

            _mock{Dependency}
                .Setup(x => x.{DependencyMethod}(It.IsAny<{ParamType}>()))
                .ThrowsAsync(new InvalidOperationException("Dependency failed"));

            // Act
            var act = () => _sut.{MethodName}(input);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Dependency failed");
        }

        #endregion
    }
}
```

### Step 3: Test Categories

Include tests for:

1. **Happy Path**: Valid input returns expected result
2. **Empty/Null Input**: Handles empty or null input gracefully
3. **Not Found**: Handles missing data scenarios
4. **Parameterized**: Theory tests for input variations
5. **Exception Handling**: Verify exception propagation and handling
6. **Mock Verification**: Verify correct dependency calls and parameters

### Step 4: Best Practices

- Use FluentAssertions for readable assertions
- Follow `MethodName_Scenario_ExpectedResult` naming
- Include XML documentation
- Use Arrange-Act-Assert pattern
- Mock all external dependencies
- Verify mock interactions
- Test both sync and async methods appropriately

### Step 5: Run Tests

After generating, run the tests:

```bash
dotnet test --filter "FullyQualifiedName~{ClassName}Tests"
```

### Step 6: Save Location

Save to:
- `Tests/{ClassName}Tests.cs`
- Or `Tests/Unit/{ClassName}Tests.cs`
- Or follow existing project structure

## After Generation

1. Generate the report file
2. Report the tests created
3. Run the tests and show results
4. If any fail, offer to debug and fix
5. Ask if additional test scenarios are needed

### Step 7: Generate Report

Create a markdown report file in `Tests/reports/`:

**Filename format:** `test-{ClassName}-{timestamp}.md`

**Example:** `Tests/reports/test-OrderService-2026-01-20-143215.md`

```markdown
# Test Generation Report

**Generated:** 2026-01-20 14:32:15
**Command:** /test OrderService
**Class:** OrderService

---

## Summary

| Metric | Value |
|--------|-------|
| Test Class | OrderServiceTests.cs |
| Tests Created | 6 |
| Tests Passed | 6 |
| Tests Failed | 0 |
| Location | Tests/OrderServiceTests.cs |

---

## Tests Created

| # | Test Name | Category | Status |
|---|-----------|----------|--------|
| 1 | CreateOrder_WithValidInput_ReturnsCreatedOrder | Happy Path | Passed |
| 2 | CreateOrder_WithEmptyItems_HandlesGracefully | Edge Case | Passed |
| 3 | GetOrder_WithNotFound_ReturnsNull | Edge Case | Passed |
| 4 | CreateOrder_WithVariousInputs_ProcessesCorrectly | Parameterized | Passed |
| 5 | CreateOrder_WhenRepositoryThrows_PropagatesException | Exception | Passed |
| 6 | CreateOrder_VerifiesRepositoryCalled | Verification | Passed |

---

## Test Details

### Happy Path Tests
- `CreateOrder_WithValidInput_ReturnsCreatedOrder`
  - Verifies standard order creation works correctly
  - Uses `OrderServiceFixtures.StandardOrder()`

### Edge Case Tests
- `CreateOrder_WithEmptyItems_HandlesGracefully`
  - Verifies empty order items are handled
- `GetOrder_WithNotFound_ReturnsNull`
  - Verifies null response when order not found

### Parameterized Tests
- `CreateOrder_WithVariousInputs_ProcessesCorrectly`
  - Input variations tested: 3

### Exception Tests
- `CreateOrder_WhenRepositoryThrows_PropagatesException`
  - Verifies exception handling behavior

---

## Test Execution

```
dotnet test --filter "FullyQualifiedName~OrderServiceTests"

Test run successful.
Total tests: 6
     Passed: 6
     Failed: 0
   Duration: 1.2s
```

---

## Files Created

- `Tests/OrderServiceTests.cs`

---

## Next Steps

- [ ] Review test assertions for completeness
- [ ] Add additional edge cases if needed
- [ ] Run full test suite: `dotnet test`
```

**Important:** Always create the `Tests/reports/` directory if it doesn't exist before saving the report.
