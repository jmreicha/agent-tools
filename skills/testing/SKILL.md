---
name: testing
description: Use to choose and apply TDD or BDD based on the change, enforcing fast Red-Green-Refactor and Given-When-Then loops.
version: 1.1.0
tags: [testing, tdd, bdd]
---

# Testing

Pick test driven development (TDD) or behavior driven development (BDD) for each change, and switch between them as the work moves.

Use TDD to design and verify internal behavior with fast feedback. Use BDD to define what users see: workflows and acceptance criteria. Choose by scope, not preference. Most features end up using both: BDD for the outside, TDD for the parts.

## When to use this skill

- Adding features, flows, or APIs.
- Fixing bugs or regressions.
- Refactoring behavior or changing requirements.
- Adding tests to untested code.

## Rules

- Write no production code until a test fails first.
- Watch the test fail, and confirm it fails for the reason you expect. A test you never saw fail might not test anything.
- Test behavior, not implementation. Tests tied to internals break on every refactor, and people stop trusting them.
- Use the smallest loop that proves the next behavior.

A test doesn't count as evidence when:

- It passed without ever failing.
- It failed because of a setup error.
- It checks mocks instead of behavior.

## Choose TDD or BDD

| Start with | When the behavior…                                              |
| ---------- | --------------------------------------------------------------- |
| TDD        | Is internal logic, a helper, or an algorithm                    |
| TDD        | Is a small rule or edge case with a precise input and output    |
| TDD        | Is a refactor that needs tight feedback                         |
| BDD        | Spans several components or layers                              |
| BDD        | Faces users, or follows a workflow                              |
| BDD        | Needs acceptance criteria that people outside the team can read |
| BDD        | Needs the team to agree on it before anyone builds it           |

Switch as the work changes:

- For a feature, write the BDD scenario first, then use TDD for each component that supports it.
- Switch from TDD to BDD when the behavior needs several modules to work together.
- Switch from BDD to TDD when a step needs precise edge-case rules.

## Loop

1. Pick one behavior.
2. Write a failing test: a TDD unit test or a BDD scenario.
3. Run the smallest test command, and watch it fail.
4. Write the least code that makes it pass.
5. Run the smallest test command again, and watch it pass.
6. Refactor while the tests stay green.

### TDD: red, green, refactor

Red: write one failing test for the next behavior.

```go
func TestRetryStopsAfterThreeFailures(t *testing.T) {
    attempts := 0
    err := Retry(func() error {
        attempts++
        return errors.New("fail")
    })

    if err == nil {
        t.Fatalf("expected error")
    }
    if attempts != 3 {
        t.Fatalf("expected 3 attempts, got %d", attempts)
    }
}
```

Green: write the smallest change that makes the test pass.

Refactor: clean up names, structure, and duplication while the tests stay green.

### BDD: given, when, then

Write the scenario in the terms users and the business use:

```gherkin
Scenario: lock account after failed logins
  Given a user account exists
  And the user has failed login attempts
  When the user fails login again
  Then the account is locked
```

Run the scenario and confirm it fails for the right reason. Then build each step definition with the TDD loop, and rerun the scenario to check the whole flow.

## Avoid

- Writing the code first and the tests later.
- Mocking so much that the test no longer checks real behavior.
- One test that covers several unrelated behaviors.
- Large BDD scenarios that hide missing unit tests.
- Refactoring before the tests pass.

## Done when

- Every new behavior had a test that you watched fail first.
- BDD scenarios use the same words as the acceptance criteria.
- TDD tests cover edge cases and error paths.
- All tests pass, with clean output.
