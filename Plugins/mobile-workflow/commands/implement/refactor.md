# /refactor — Software Architect Refactoring Review

Assume the role of a senior software architect conducting a design review on the provided
class. Work through the following five phases in order. Do not skip ahead — complete each
phase fully before moving to the next.

---

## Phase 1: Responsibility Audit

Read the class and list every distinct responsibility it currently owns. For each one:
- Name it clearly (one line)
- Point to the specific methods or fields that implement it
- State whether it belongs in this class or not, and why

At the end of Phase 1, give a one-sentence verdict on the class's overall cohesion.

---

## Phase 2: Unhappy Path Analysis

Before looking at tests, run `/adversarial-check` against the class using the Skill tool.
Use the class file from Phase 1 as the input.

The adversarial-check output becomes the Phase 2 record. Do not duplicate or summarize it —
reference findings by number (e.g., "Finding #3") in later phases.

Phase 3 and Phase 5 must address every 🔴 finding before any refactoring begins. ⚠️ findings
must be accounted for in the test plan. 💡 findings are at the refactoring author's discretion.

---

## Phase 3: Unit Test Plan

Based on Phases 1 and 2, write a prioritized test plan covering both the current behavior
that must be preserved through the refactor and any gaps found in Phase 2.

Divide tests into two groups:

**Group A — Characterization Tests (preserve current behavior)**
These lock in what the class does today before any code moves. They are the safety net
for the refactor. For each test:
- Name it: [MethodOrBehavior]_[Condition]_[ExpectedOutcome]
- Describe what it asserts about existing behavior
- Mark it as: Logic, Integration, or UIKit
- Note: these tests should be written and passing BEFORE the refactor begins, and
  should continue passing unchanged AFTER the refactor completes

**Group B — New Tests (cover gaps and unhappy paths)**
These are the tests that should exist but don't. For each test:
- Name it: [MethodOrBehavior]_[Condition]_[ExpectedOutcome]
- State what needs to be mocked or stubbed to make it runnable in isolation
- Mark it as: Logic, Integration, or UIKit
- Note: these tests may require the refactor to complete before they are writable —
  flag these explicitly

Prioritize Logic tests first, then Integration, then UIKit. Flag any behavior that is
currently untestable without refactoring and explain why.

---

## Phase 4: Standards Check

Before proposing any new structure, run `/standards-check` against the current class.
List every violation found. These must be corrected in the refactored output — the
refactor is not complete if it moves violations from one class to another without
fixing them.

---

## Phase 5: Refactoring Plan

Before proposing any new structure, invoke `superpowers:brainstorming` using the
Skill tool to explore design alternatives. Do not commit to the first structural
idea — brainstorming should surface at least two candidate approaches so the
tradeoffs can be evaluated explicitly.

Then propose a refactored structure that resolves the problems found in Phases 1–4.

Rules:
- Apply the Single Responsibility Principle, but do not over-split. If two
  responsibilities are always triggered together and share the same dependencies,
  keeping them in one class is acceptable — say so explicitly.
- Prefer fewer, well-named classes over many thin wrappers.
- Every new class must have a stated single responsibility, a list of its dependencies,
  and an explanation of what becomes testable that wasn't before.
- Show how the classes relate to each other in a simple dependency diagram.
- Identify any responsibilities that should be deleted rather than moved.
- Flag any refactoring that is high-risk (touches shared state, changes async behavior,
  affects lifecycle) and explain what must be verified before merging.
- All new classes must pass `/standards-check` — call this out explicitly for any class
  where a standards decision is non-obvious.

End with a prioritized implementation order:
1. Which characterization tests to write first
2. Which class to extract first and why
3. Which new tests become writable after each extraction step
