# C# XUnit Fixture Generation

Generate a C# fixture class for XUnit testing.

## Usage

```
/project:testing/fixture <class-name>
```

## Arguments

- `$ARGUMENTS` - The class or service name to generate fixtures for (e.g., `OrderService`, `UserRepository`, `PaymentProcessor`)

## Instructions

When invoked, follow these steps:

### Step 1: Analyze the Model/Class

1. Search for the corresponding class or model in the codebase:
   - Look in `Models/`, `src/Models/`, `Services/`, `Domain/`, or similar directories
   - Find `{ClassName}.cs`, `{ClassName}Response.cs`, `{ClassName}Dto.cs`, or related classes
2. Read and understand the class structure, properties, and types

### Step 2: Check Existing Patterns

1. Look for existing fixture classes in `Tests/Fixtures/` or `tests/Fixtures/`
2. Identify the naming conventions and patterns used
3. Check for any existing fixtures for the requested class

### Step 3: Generate the Fixture Class

Create a fixture class with the following structure:

```csharp
using System;
using System.Collections.Generic;

namespace {Namespace}.Tests.Fixtures
{
    /// <summary>
    /// Test fixtures for {ClassName} testing scenarios.
    /// </summary>
    public static class {ClassName}Fixtures
    {
        /// <summary>
        /// Returns a standard {scenario} for happy-path testing.
        /// </summary>
        public static {Type} Standard{Scenario}()
        {
            return new {Type}
            {
                // Properties with realistic test data
            };
        }

        /// <summary>
        /// Returns an empty/minimal instance for edge-case testing.
        /// </summary>
        public static {Type} Empty{Scenario}()
        {
            // Return empty/minimal instance
        }

        /// <summary>
        /// Returns null for not-found scenario testing.
        /// </summary>
        public static {Type}? NotFound()
        {
            return null;
        }
    }
}
```

### Step 4: Fixture Requirements

Include these fixture methods:

1. **Standard/Happy Path**: Realistic data with typical values
2. **Empty**: Empty collections, minimal data
3. **Large Dataset**: Many items (10-50+) for stress testing
4. **Not Found/Error**: Null or error responses
5. **Invalid State**: Data that should trigger validation errors

### Step 5: Data Guidelines

- Use `DateTime.Today`-relative dates (avoid hardcoded dates)
- Use realistic IDs: `USR-2026-00001`, `ORD-2026-00123`
- Include XML documentation for each method
- Match the exact class structure and property types
- Use domain-appropriate naming for the project context

### Step 6: Save Location

Save the fixture class to:
- `Tests/Fixtures/{ClassName}Fixtures.cs`
- Or follow the existing project structure

## Example

For `$ARGUMENTS = Order`:

```csharp
public static class OrderFixtures
{
    public static Order StandardOrder()
    {
        return new Order
        {
            Id = "ORD-2026-00001",
            CustomerId = "CUST-2026-00001",
            CreatedAt = DateTime.Today.AddDays(-1),
            Status = OrderStatus.Confirmed,
            Items = new List<OrderItem>
            {
                new OrderItem
                {
                    ProductId = "PROD-001",
                    ProductName = "Widget Pro",
                    Quantity = 2,
                    UnitPrice = 29.99m
                }
            },
            TotalAmount = 59.98m
        };
    }

    public static Order EmptyOrder()
    {
        return new Order
        {
            Id = "ORD-2026-00002",
            CustomerId = "CUST-2026-00001",
            CreatedAt = DateTime.Today,
            Status = OrderStatus.Pending,
            Items = new List<OrderItem>(),
            TotalAmount = 0m
        };
    }

    public static Order LargeOrder()
    {
        var items = Enumerable.Range(1, 50)
            .Select(i => new OrderItem
            {
                ProductId = $"PROD-{i:D3}",
                ProductName = $"Product {i}",
                Quantity = i,
                UnitPrice = 10.00m * i
            }).ToList();

        return new Order
        {
            Id = "ORD-2026-00003",
            CustomerId = "CUST-2026-00001",
            CreatedAt = DateTime.Today,
            Status = OrderStatus.Processing,
            Items = items,
            TotalAmount = items.Sum(x => x.Quantity * x.UnitPrice)
        };
    }
}

## After Generation

1. Generate the report file
2. Report what was created
3. Ask if additional fixture scenarios are needed
4. Offer to create the corresponding test class

### Step 7: Generate Report

Create a markdown report file in `Tests/reports/`:

**Filename format:** `fixture-{ClassName}-{timestamp}.md`

**Example:** `Tests/reports/fixture-Order-2026-01-20-143052.md`

```markdown
# Fixture Generation Report

**Generated:** 2026-01-20 14:30:52
**Command:** /fixture Order
**Class:** Order

---

## Summary

| Metric | Value |
|--------|-------|
| Fixture Class | OrderFixtures.cs |
| Methods Created | 4 |
| Location | Tests/Fixtures/OrderFixtures.cs |

---

## Class Analysis

**Source Class:** Models/Order.cs

### Properties Found:
| Property | Type | Nullable |
|----------|------|----------|
| Id | string | No |
| CustomerId | string | No |
| Items | List<OrderItem> | Yes |
| TotalAmount | decimal | No |
| Status | OrderStatus | No |

---

## Fixtures Created

### 1. StandardOrder()
- **Purpose:** Happy path with typical order data
- **Data:** 2 items, confirmed status

### 2. EmptyOrder()
- **Purpose:** Edge case - order with no items
- **Data:** Empty items list, pending status

### 3. LargeOrder()
- **Purpose:** Large dataset / stress testing
- **Data:** 50 items, high total amount

### 4. NotFound()
- **Purpose:** Error case
- **Data:** Returns null

---

## Files Created

- `Tests/Fixtures/OrderFixtures.cs`

---

## Next Steps

- [ ] Generate tests with `/csharp-test Order`
- [ ] Review fixture data for accuracy
- [ ] Add additional scenarios if needed
```

**Important:** Always create the `Tests/reports/` directory if it doesn't exist before saving the report.
