---
name: sdlc
description: Entry point for software work. Sets a measurable goal with done checks, finds the lifecycle stage (design, spec, test, implement, security review, observe, refactor, docs, ship, learn), and routes to the matching agent-tools skill and any domain skill, such as Terraform. Use when starting any coding, infrastructure, or docs task, when asked "where do I start", "set a goal", or "what does done look like", or when invoked as /sdlc.
version: 2.0.0
tags: [workflow, planning, routing]
---

# SDLC

Set the goal, find the stage, and hand off to the skill that owns it. Every skill below also works on its own.

## Size the task first

- Trivial (a typo, a fix of one line, a question): skip this skill. Answer or do it, and apply any domain skill that matches.
- Small (one file, one behavior): write the goal in one line, then go straight to the stage.
- Larger: write the full goal contract, then walk the stages in order. Skip a stage only when it doesn't apply, and say which one you skipped and why.

## Write the goal contract

Write this before any code. Keep it under 10 lines.

```markdown
**Goal:** <one outcome, with a number when there is one>
**Read first:** <files, issue, design doc>
**Out of scope:** <what must not change>
**Done when:** <exact command> shows <expected output>
```

- Write every done check so the transcript proves it: a command and the output it must print. "Tests pass" is vague. "`go test ./retry/...` exits 0" is a check.
- Never delete, skip, or weaken a test to meet a check.
- After 3 failed attempts at the same check, stop. Report the root cause and the decision you need.
- For long, mechanical work with a clear stop (a migration, a coverage lift), give the user a line to paste into the `/goal` command: `/goal <done check>, without weakening tests`. The `/goal` evaluator reads only the transcript, so the check must print its result.

## Route by stage

The lifecycle runs in this order. Most tasks enter partway through.

| Stage              | Skill                                                                                                             | Stage is done when                                |
| ------------------ | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Issue, design, ADR | `agent-tools:rubber-duck` to think, `agent-tools:research` for docs and prior art, `agent-tools:docs` to write it | The decision and its reason are written down      |
| Specs              | `agent-tools:docs` (design doc outline)                                                                           | Each acceptance criterion is a pass or fail check |
| Failing tests      | `agent-tools:testing`                                                                                             | A test failed for the expected reason             |
| Implement          | `agent-tools:testing` loop, plus the domain skill                                                                 | The done checks pass                              |
| Security review    | `agent-tools:review`, the `/security-review` command                                                              | Every finding is fixed or recorded                |
| Observe            | Run the real artifact. Use the Honeycomb skills when the service sends traces there.                              | Evidence from the running system, not a proxy     |
| Refactor           | The `/simplify` command, then `/code-review`                                                                      | Tests still pass                                  |
| Docs and diagrams  | `agent-tools:docs`, `agent-tools:diagram`                                                                         | The prose checks in the docs skill pass           |
| Ship               | `agent-tools:pr`                                                                                                  | CI is green                                       |
| Learn              | `agent-tools:learn`                                                                                               | Accepted lessons are in a skill, rule, or check   |

## Add the domain skill

Apply a domain skill alongside the stage skill whenever its trigger matches. Don't wait to be asked.

| Trigger                                                        | Skill                   |
| -------------------------------------------------------------- | ----------------------- |
| `.tf`, `.tfvars`, `.hcl`, Terraform, OpenTofu, or Terragrunt   | `agent-tools:terraform` |
| Any diagram, or a doc that would read better with one          | `agent-tools:diagram`   |
| Any prose: docs, READMEs, PR bodies, commit messages, comments | `agent-tools:docs`      |
| Slow code or infrastructure                                    | `agent-tools:optimize`  |
| Issues, milestones, or project status                          | `agent-tools:planning`  |

For anything else, check the full skill list and use the one whose description matches.

## Report

End with the goal contract, each done check with its real output, the stages you skipped and why, and what's left.
