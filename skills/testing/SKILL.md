---
name: testing
description: Test first development that picks TDD or BDD for each change and runs a fast red, green, refactor loop. Use when adding a feature, fixing a bug or regression, changing behavior, refactoring, adding tests to untested code, or when the user mentions TDD, BDD, a failing test, a regression test, or Given-When-Then.
version: 2.0.0
tags: [testing, tdd, bdd]
---

# Testing

Pick test driven development (TDD) or behavior driven development (BDD) for each change, and switch between them as the work moves.

Use TDD to design and verify internal behavior with fast feedback. Use BDD to define what users see: workflows and acceptance criteria. Choose by scope, not preference. Most features end up using both: BDD for the outside, TDD for the parts.

## Find the test setup first

Before you write a test, find how this repo already tests:

- The test command: `script/test` when the repo has one, else the command from the `Makefile`, `package.json`, CI config, or README.
- The framework, the helpers, and where tests live.
- The closest existing test for the code you're changing. Copy its style.

Run the smallest command that covers your test, not the whole suite.

## Rules

- Write no production code until a test fails first.
- Watch the test fail, and confirm it fails for the reason you expect. A test you never saw fail might not test anything.
- Test behavior through the public interface, not implementation. Tests tied to internals break on every refactor, and people stop trusting them.
- Take expected values from an independent source: a known-good literal, a worked example, or the spec. Never compute them the way the code does.
- Work in vertical slices: one test, then the code for it, then the next test. Don't write all the tests first.
- Never delete, skip, or weaken a test to make it pass.

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
2. Write a failing test: a TDD unit test, such as `TestRetryStopsAfterThreeFailures`, or a BDD scenario, such as `Given … When the user fails login again Then the account is locked`.
3. Run the smallest test command, and watch it fail for the expected reason.
4. Write the least code that makes it pass.
5. Run the command again, and watch it pass.
6. Refactor while the tests stay green.

For a bug fix, the failing test is the reproduction. When you commit, put the failing test in its own commit before the fix, so the history shows the bug and then the cure.

## Test at the fastest level that proves it

The levels, fastest first, are a pure function, a service with fakes, a route handler or component, and the whole app in a browser or e2e run. Write each test at the fastest level that can prove what it checks.

- Keep a slow test only for what only its level can prove, such as one journey per critical flow or real SQL behavior.
- When a slow test checks a decision (a branch, a calculation, a parse), pull that decision into a small pure function named for the domain, and test it there.
- One assertion per thing the test checks, in the order a reader asks: what came back, then each effect. Compare whole values. Match a value the test can't know, such as a generated ID, by its shape, not by "any string".

Before you delete or move a test, prove another test covers it: break that behavior in the code, confirm a remaining test goes red, then revert the break.

## When a test isn't worth it

Don't force a test that needs broad harness setup, brittle mocks, slow end-to-end infrastructure, production-only state, or a lot of unrelated fixtures. A bad test is worse than no test.

Use the closest executable check instead: a short script, a reproduction command, a log assertion, or a focused integration check. Run it before and after the fix, the same way you would run a test, and say why a test wasn't practical.

## Avoid

- Writing the code first and the tests later.
- Tautological tests, where the assertion repeats the code's own logic, such as `expect(add(a, b)).toBe(a + b)`. They can never fail.
- Mocking so much that the test no longer checks real behavior.
- One test that covers several unrelated behaviors.
- Large BDD scenarios that hide missing unit tests.
- Refactoring before the tests pass.

## Report

Paste the evidence, not a summary of it:

- The test or check, and the failing output it printed before the fix.
- The passing output after the fix, and any nearby tests you ran.
- If you couldn't show a failure first, why, and the check you used instead.
