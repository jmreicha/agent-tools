---
name: review
description: Review a change before merge. Finds bugs and security issues that a run can prove, then grades merge risk (low, medium, or high) on alignment, impact, verification, rollback cost, and error detection. Use when reviewing a PR, a branch, or a diff, when asked whether a change is safe or ready to merge or ship, or before opening or merging a PR.
version: 2.0.0
tags: [code-review, quality, security, risk]
---

# Review

<!-- Merge risk grading adapted from warpdotdev/common-skills merge-risk (MIT), which credits mattpocock/skills pr. -->

Tell the author what could break and how risky the merge is, with evidence. Report what you find. Don't fix it unless the user asks.

## Frame the change

- **Scope:** what the user names. Otherwise, the branch diff from its merge base with the default branch, plus uncommitted changes.
- **Intent:** the goal contract from `agent-tools:sdlc`, the spec, the linked issue, and the PR description (`gh pr view`), in that order. Restate it in one sentence. Ask the user when you can't find it.

## Find defects

1. Run the `code-review` skill on the scope for correctness bugs.
2. When the change touches a sensitive area (auth, permissions, payments, PII, secrets, data migrations, dependency bumps, infrastructure, or config), also run the `security-review` skill.
3. Prove each finding with a run against the real code: a failing test, a repro command, or output that shows the wrong behavior. Keep proven findings. List the rest as unverified, with what would prove them, or drop them.

Merge findings that share a root cause.

## Grade merge risk

Grade each criterion. The verdicts run from worst to best, and the last column says what the best verdict means.

| Criterion       | Verdicts                | Weight | Low risk means                                                                                                                                                                                                                                                     |
| --------------- | ----------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Alignment       | poor, decent, good      | 1      | The code does what the intent says. Assumptions and drive-by changes are written down.                                                                                                                                                                             |
| Impact          | large, medium, small    | 2      | The scope is contained and away from sensitive areas. Find callers and consumers (`rg`, the LSP) before you judge it. A sensitive area raises the risk whatever the diff size, especially a change that widens access, weakens validation, or logs sensitive data. |
| Verification    | poor, decent, good      | 2      | Tests cover the behavior and its edge cases, and you've seen them run. A change users can see has before and after screenshots or output. A change that could affect performance has a before and after number.                                                    |
| Rollback cost   | high, medium, low       | 1.5    | It's a two-way door: reverting the commit undoes it. Dropping data, a migration without a down path, removing a public API, or a published release is a one-way door. A one-way door needs an ADR or a backup plan.                                                |
| Error detection | poor, decent, good, n/a | 1      | If it breaks in production, logs, metrics, or alerts show it before users report it. Swallowed errors and silent fallbacks count against it.                                                                                                                       |

Score the worst verdict 3, the middle one 2, and the best one, or n/a, 1. The weighted mean gives the grade: below 1.5 is **low**, 1.5 up to 2.25 is **medium**, and 2.25 or above is **high**. Keep the numbers to yourself. Report the grade.

Grade in proportion. A docs or comment change is small, two-way, and needs no monitoring. Don't invent risk.

## Gate

- **Low:** ready to merge.
- **Medium:** mergeable once the author accepts every criterion that isn't at its best verdict. Name the weakest criterion.
- **High:** not ready. List what would improve each criterion at its worst verdict, or get the user's explicit approval to merge anyway.

## Report

```markdown
**Merge risk: <low | medium | high>**

<One line: what to do before merge, or "Ready to merge.">

**Alignment:** <verdict>
**Impact:** <verdict>
**Verification:** <verdict>
**Rollback cost:** <verdict>
**Error detection:** <verdict>

<Under each verdict that isn't the best, one short bullet per gap, with a link to the file and line.>

**Findings:** <each proven finding with its command and output, then any unverified ones, labeled. Or "No proven findings.">
```

Put the first two lines in the PR description. They're the merge risk line in the PR outline in `agent-tools:docs`.
