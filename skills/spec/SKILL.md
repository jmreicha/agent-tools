---
name: spec
description: Write, change, and implement behavior specs that drive tests and code. Matches the repo's existing spec format first (yass, Spec Kit, OpenSpec, Kiro, Gherkin, or a PRD folder), and otherwise uses yass. Use when starting a new feature or project that needs its behavior pinned down, when writing or changing a spec, acceptance criteria, or requirements, when implementing against an existing spec, or when the user mentions a spec, yass, or a .yass.yaml file.
version: 1.0.0
tags: [specs, requirements, tdd]
---

# Spec

A spec says what the system must do, as checks that code and tests can be held to. It's the contract: the user approves it before anyone builds, and when the code comes out wrong, the fix usually starts with a line in the spec.

A spec isn't a decision record or a build plan. Record a decision with `agent-tools:adr`. Explain how we plan to build something in a design doc with `agent-tools:docs`.

## Match the repo first

Look for an existing spec format before you write one:

```bash
git ls-files | rg --ignore-case '\.yass\.yaml$|^\.specify/|^specs/[0-9]+-[^/]+/spec\.md$|^openspec/|^\.kiro/specs/|\.feature$|(^|/)(prd|prds|specs|rfcs?)/'
```

| Found                                          | Format                       |
| ---------------------------------------------- | ---------------------------- |
| `root.yass.yaml`, `*.yass.yaml`                | yass                         |
| `.specify/`, `specs/NNN-name/spec.md`          | GitHub Spec Kit              |
| `openspec/`                                    | OpenSpec                     |
| `.kiro/specs/`                                 | Kiro                         |
| `*.feature`                                    | Gherkin, driven by BDD tests |
| A `prd`, `specs`, or `rfcs` folder of Markdown | The team's own format        |

- A `spec/` folder or `*_spec.rb` and `*.spec.ts` files are usually tests, not specs. Read one before you count it.
- When the repo has a format, read its two newest specs and its tool's docs, then follow that tool's workflow and shape.
- When it has none, use yass.

## Use yass

Run `yass` with no arguments before you write, change, or implement a spec. It prints the notation and the path of docs for each task. Read every doc on your path in full, in order:

| Task                       | Path                                                                        |
| -------------------------- | --------------------------------------------------------------------------- |
| New spec                   | `yass docs brainstorming`, then the write path                              |
| Write or change a spec     | `yass docs authoring`, `documents`, `obligations`, `references`, `coverage` |
| Implement an approved spec | `yass docs implementing`                                                    |

- The `yass` CLI only reads. You write the `.yass.yaml` files, starting with `root.yass.yaml` at the project root.
- Read a spec set through `yass list`, `yass query`, `yass find`, and `yass refs`, one document at a time, not whole files.
- For a new spec, propose answers for the user to correct instead of asking open questions. Build nothing until the user has read the spec and approved it.

## Implement against a spec

- Turn each obligation into a test first, with `agent-tools:testing`: a `MUST` gets a test that fails until the code meets it, and a `MUST-NOT` gets a test that proves the behavior can't happen.
- Build only what the spec says. When the code needs a behavior the spec doesn't cover, stop and propose a spec change instead of adding it.
- When a test and the spec disagree, the spec wins until the user changes it.

## Check

For yass, both commands must exit 0:

```bash
yass validate
yass lint
```

Run `yass explain <rule-id>` for any lint finding you don't understand. For other formats, run the tool's own check when it has one.

Report the spec files you wrote or changed, the obligations that still have no test, and any question the user must answer before you build.

When the repo uses yass and its `CLAUDE.md` doesn't mention it, suggest adding this line, and add it only when the user agrees: "Run `yass` with no arguments before writing, changing, or implementing a spec."
