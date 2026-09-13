---
name: test-audit
description: Sweep a test suite for low-value tests - ones that only re-assert the source, duplicate another test, or lock in implementation detail - remove them, then check whether the production code can lose seams the deleted tests were forcing. Use when the user says "audit the tests", "sweep the tests", "on nettoie les tests", or a suite has grown faster than the behavior it covers.
---

# test-audit

A test with each new unit of behavior (the `CLAUDE.md` rule) is right,
but the suite then accumulates tests that cost maintenance and prove
nothing. This skill removes them and simplifies what they were propping
up.

Pairs with `mattpocock-skills:tdd` (needs the `mattpocock-skills` plugin
installed globally; that one adds behavior-first tests, this one removes
the ones that stopped earning their place).

## What counts as low value

Flag a test when it is one of:

- **Re-asserts the source**: checks a constant equals itself, a getter
  returns what the constructor set, a mapping the test also hardcodes.
- **Implementation-locked**: breaks whenever the source is refactored
  without a behavior change - asserts call order, spy counts, private
  method names, exact log strings.
- **Duplicate**: another test already covers the same branch with
  different words.
- **Mock theater**: mocks the unit under test, or mocks so much that the
  assertion only proves the mock was configured.
- **Vacuous**: no meaningful assertion, or asserts `toBeDefined()` on
  something that cannot be undefined.

Keep a test if it pins observable behavior at a real boundary (HTTP
route, service contract, a pure function's input -> output), even if it
looks simple.

## Steps

1. List the test files in scope. For each test, classify: keep / low
   value (with which reason above) / unsure.
2. Show the user the "low value" list with the reason per test. Get an OK
   before deleting - do not delete unseen.
3. Remove the agreed tests.
4. Run the suite. It must still pass with the same behavior coverage
   (check a coverage diff if the project tracks one: line coverage may
   drop, branch coverage on real logic must not).
5. **Now simplify the source.** A deleted implementation-locked test
   often existed because the code exposed a seam only for that test - a
   constructor-injected dependency with one real caller, a `public`
   method that should be private, an interface with one implementation,
   an abstraction with one use. Collapse those.
6. Run the suite and typecheck again. Report: tests removed, lines of
   production code removed, seams collapsed.

## Guardrails

- One behavior can lose its test only if another test still covers it.
  When in doubt, keep.
- Do not delete a failing test to make the suite green - that is a
  separate problem, surface it.
- Security / auth / ownership tests are not "implementation detail" on a
  project with real users - keep them.

## Why a skill

- Runs only when asked - zero context cost otherwise.
- Step 5 (simplify the source the tests were forcing open) is the point,
  and the step that gets skipped when this is done ad hoc.
