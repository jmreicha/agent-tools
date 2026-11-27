---
name: refactor
description: Change the structure of code without changing its behavior. Pins current behavior with tests first, deletes before it adds, moves in small steps that keep the tests green, and reports any bug it finds instead of fixing it. Use when asked to refactor, clean up, restructure, simplify, deduplicate, extract, split, rename, or reorganize code, or to remove duplication or dead code.
version: 1.0.0
tags: [refactoring, quality, tdd]
---

# Refactor

<!-- Adapted from cursor/plugins pstack refactoring playbook (MIT) and marekkirejczyk/skills refactor-tests (MIT). -->

The structure changes. The behavior doesn't. Every caller sees the same results, errors, writes, and calls as before.

A refactor that adds a feature or fixes a bug is two changes. Do the refactor first, against today's behavior, and ship the feature or fix after it with `agent-tools:testing`.

## Pin the behavior

Before you move anything, make sure tests catch a change in what the code does.

- Read the existing tests for the code in scope, and run them.
- Where behavior has no test, write one that asserts what the code does today: a characterization test, a snapshot, or a script that diffs old and new output. A type check or lint isn't a pin.
- Cover the edges: boundaries, empty input, errors, and anything that differs between copies of code you plan to merge.

## Name the target

Say in two or three sentences what the module layout, types, and call graph should be if you built them today. Name the structure the code is missing, such as one shared function, a table instead of branches, or a type instead of repeated checks.

Keep boring code that's already clear and local. A reshape must remove branches, duplication, or invalid states. If it only adds indirection, don't do it.

## Change it in rounds

1. **Delete first.** Remove dead code, one-caller wrappers, redundant checks, and stale references before you build the new shape.
2. **One change per round.** Make it, then run the tests. Go on only when they're green.
3. **A red test means the round changed behavior.** Undo the round and take a smaller step. Don't edit the test to match.
4. **Change an API in one wave.** Migrate every caller and delete the old API in the same change. Leave no compatibility shims or parallel paths.
5. **Check every rename** with a search of the whole repo. Renames miss strings, docs, config, and back references.

## When you find a bug

Don't fix it inside the refactor. Keep today's behavior, and leave the fix ready for the user:

1. Pin today's behavior with a test named for what it does now.
2. Next to it, write the test for the right behavior, mark it skipped, and name it for the bug.
3. Report the bug, and leave the decision to fix it to the user.

```python
def test_format_pounds_negative_today():
    assert format_pounds(-500) == "£-5"


@pytest.mark.skip(reason="bug: a negative amount should read -£5")
def test_format_pounds_negative():
    assert format_pounds(-500) == "-£5"
```

The fix is then to delete the first test and remove the skip from the second.

## Keep it only if it helps

The measure of a refactor is that the code is easier to read and change: fewer layers between a question and its answer, less duplication, and less state to keep in your head. If the diff doesn't make some part easier to read, revert it.

## Check

- The full test suite passes, with no test weakened or deleted to make it pass.
- For a larger reshape, an equivalence check passes: the same inputs give the same outputs before and after.
- Lint and type checks pass.

Then run the `simplify` skill on the diff for leftover cleanups.

## Report

- The structure that changed, and the target shape.
- The tests that pinned the behavior, and the output that shows them passing.
- Each bug you found, with its pinned test and its skipped test.
- What you reverted, and why.

When you commit, put the deletions first, then the reshape, then any cleanup, so each commit stays green.
