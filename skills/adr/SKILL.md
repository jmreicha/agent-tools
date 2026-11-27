---
name: adr
description: Record architecture decisions as ADRs. Matches the repo's existing ADR folder, format, and numbering first, and otherwise sets up the adrs CLI with the house template (status, context, decision, alternatives, consequences) in docs/adrs. Use when making or recording a decision that is hard to reverse or that others may later ask "why" about, when superseding or changing the status of an ADR, or when the user mentions an ADR, a decision record, or adrs.
version: 1.0.0
tags: [adr, decisions, documentation]
---

# ADR

Record one decision and why we made it, so the next person doesn't relitigate it.

Write an ADR for a decision that's hard to reverse, crosses more than one component or team, or that someone may ask "why" about later. Don't write one for a routine choice. For how we plan to build something, write a design doc with `agent-tools:docs` instead.

## Match the repo first

Find the existing ADRs before you write anything:

```bash
adrs config
git ls-files | rg --ignore-case '(^|/)(adrs?|decisions)/|\.adr-dir$|adrs\.toml$|\.log4brains\.yml$'
```

Common places are `doc/adr`, `docs/adr`, `docs/adrs`, `docs/decisions`, and `docs/architecture/decisions`.

When the repo has ADRs:

- Read the two newest. Match their format, sections, filename pattern, numbering, status words, and frontmatter.
- Use `adrs` when the set follows the adr-tools or MADR layout (`.adr-dir`, `adrs.toml`, or `NNNN-title.md` files). Pass `--format madr` for MADR. Leave out the house template when the repo already has its own format.
- When you use `adrs` and the repo root has no `adrs.toml`, add one with `adr_dir` set to the existing folder and `no_edit = true`. When the file exists, add only the keys it's missing and keep the rest.
- When `adrs` can't produce the repo's format (log4brains, a wiki export, another numbering scheme), copy the newest ADR by hand and keep its shape.

## Set up when there are none

Put ADRs in `docs/adrs`. When the repo keeps docs somewhere else, use a folder under that instead.

```bash
adrs init docs/adrs
cp <this skill dir>/templates/adr.md docs/adrs/template.md
```

Then write `adrs.toml` at the repo root, so `adrs` uses the template and never opens an editor:

```toml
adr_dir = "docs/adrs"
no_edit = true

[templates]
custom = "docs/adrs/template.md"
```

`adrs init` also writes `0001-record-architecture-decisions.md`. Keep it. It records the choice to use ADRs.

## Write the ADR

```bash
adrs new "<the decision, as an action>"
```

- Pass `--no-edit` when the repo has no `adrs.toml` with `no_edit = true`. Without it, `adrs` opens an editor and the command hangs.
- Name the ADR with the decision, not the question: "Use Postgres for persistence", not "Database choice".
- Keep one decision per ADR.
- **Context:** the forces and facts that make a decision necessary now. Give numbers and constraints, not background history.
- **Decision:** what we do, as an action: "We use X for Y."
- **Alternatives:** every option we considered, with the reason we rejected it in one line. An ADR with no alternatives isn't a decision.
- **Consequences:** what gets easier, what gets harder, and what we now have to do or watch. Include the bad ones.
- Write in "we", and follow `agent-tools:docs` for the prose. An ADR is explanation mode.

## Change an ADR

- Leave an accepted ADR's decision alone. To change it, write a new ADR with `adrs new --supersedes <number> "<new decision>"`, which marks the old one superseded.
- Relate two ADRs with `adrs link <from> "<kind>" <to>`, such as `adrs link 5 Amends 2`.
- New ADRs start as Proposed. Run `adrs status <number> accepted` only when the user says the decision is accepted.
- Fix typos and broken links in place.

## Check

```bash
adrs doctor
```

Fix every error it reports. Then run the prose checks in `agent-tools:docs` on the new file.

Report the ADR's path, its status, and any ADR it supersedes or links to.
