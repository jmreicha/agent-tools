---
name: conventions
description: Where code lives and how the repo runs it. Matches the repo's existing dirs and entry points first. It introduces no Makefile, Taskfile, justfile, or other build system, and otherwise sets up the house defaults, which are language-idiomatic code paths, a canonical script/ dir of thin shell scripts with one verb per task (bootstrap, setup, test, server, cibuild), a docs/ tree with one home per document, tool versions pinned in mise.toml, a pre-commit gate, CI pipelines that call script/cibuild, and Conventional Commits with semver releases cut by cocogitto. Use when deciding where a new file, module, or script goes, adding build, run, test, or lint entry points, setting up a new repo, adopting mise, pre-commit, or Renovate, adding or editing CI pipelines, writing commit messages, or setting up versioning, changelogs, or releases, or when the user asks "where does this go" or mentions scripts to rule them all.
version: 1.0.0
tags: [structure, scripts, cicd, mise]
---

# Conventions

Where code lives and how the repo runs it: the canonical dirs, the `script/` shell scripts that run everything, the `docs/` tree, tool versions, the local gate, dependency updates, and the CI pipelines that call the scripts.

Placement that follows convention is not a design decision. When something already has a home, put it there and move on. Think through a genuinely new shape with `agent-tools:rubber-duck`, and record a decision that is hard to reverse with `agent-tools:adr`.

This skill owns placement, not content. Prose rules belong to `agent-tools:docs`, behavior contracts to `agent-tools:spec`, and test method to `agent-tools:testing`.

## Match the repo first

Find what the repo already does before you add anything:

```bash
git ls-files | rg --ignore-case '^(Makefile|makefile|justfile|Justfile|Taskfile\.yml|mise\.toml|\.mise\.toml)$|^\.(tool-versions|nvmrc|python-version|node-version)$|(^|/)(script|scripts|bin|tools)/|\.pre-commit-config\.ya?ml$|(^|/)renovate\.json5?$|\.github/dependabot\.yml$|\.github/workflows/|\.gitlab-ci\.yml$|^(cog\.toml|\.cz\.toml|\.releaserc.*|release\.config\.[cm]?js|release-please-config\.json|\.changeset/.*|\.goreleaser\.ya?ml|commitlint\.config\..*)$'
```

- A repo already running on `make`, `just`, a Taskfile, or mise tasks keeps its system. Add new entry points there, in its style, so the repo has one way to run things. Offer once to migrate its targets into `script/` verbs, and migrate only when the user agrees.
- Existing dirs win. New code goes next to the code it most resembles, in the nearest existing style.
- A script dir under another name (`scripts/`, `bin/`, `tools/`) is the repo's canonical dir. Add to it and keep its naming.
- When the repo has an answer for the piece you need, stop here. Restructure only when the user asks.

When the repo has no answer, set up the piece from the table below, and only the pieces the task needs.

## House defaults

| Piece                               | Home                           | Read                                                 |
| ----------------------------------- | ------------------------------ | ---------------------------------------------------- |
| New code whose home isn't obvious   | `src/<package>`, per language  | [references/layouts.md](references/layouts.md)       |
| A way to run, build, test, or ship  | `script/<verb>`                | [references/scripts.md](references/scripts.md)       |
| Any document                        | `docs/<mode>/`                 | [references/docs-dirs.md](references/docs-dirs.md)   |
| Language and CLI tool versions      | `mise.toml`                    | [references/mise.md](references/mise.md)             |
| CI pipelines                        | `.github/workflows/<name>.yml` | [references/cicd.md](references/cicd.md)             |
| Fast local checks                   | `.pre-commit-config.yaml`      | [references/pre-commit.md](references/pre-commit.md) |
| Dependency updates                  | `renovate.json`                | [references/renovate.md](references/renovate.md)     |
| Commit messages, versions, releases | `cog.toml`                     | [references/releases.md](references/releases.md)     |

## Entry points

Every way to run, build, test, or ship the repo is a thin executable in `script/`, named for its verb. One command per task, the same one for humans, agents, and CI.

| Verb      | Job                                                              |
| --------- | ---------------------------------------------------------------- |
| bootstrap | Install dependencies and tools. One command to a runnable repo.  |
| setup     | Prepare local state, such as seed data or config. Safe to rerun. |
| test      | Run the test suite, the command CI runs.                         |
| server    | Run the app locally.                                             |
| console   | Drop into a REPL with the app's context.                         |
| cibuild   | Everything CI must prove: test, lint, build.                     |
| release   | Cut and tag a release.                                           |

- Entry points are plain shell scripts, not build-system targets. The house introduces no `Makefile`, `Taskfile`, `justfile`, or mise tasks: everything a build system does ends up in a shell command anyway.
- Keep verbs thin. Each composes the real commands and implements no logic. When a verb grows logic, move the logic into the product and let the verb call it.
- Add a verb when a command is about to be documented twice. Then point every copy at the verb.
- Maintenance scripts that are not entry points also live in `script/`, named for what they do.

[references/scripts.md](references/scripts.md) has the full rules.

## Docs

Every document has exactly one home. `docs/` has one folder per Diátaxis mode, plus `docs/adrs/`:

```text
docs/
  adrs/          Decisions, via agent-tools:adr
  tutorials/     Learning-oriented
  how-to/        Task-oriented, including runbooks
  reference/     Lookup: API, CLI, config
  explanation/   Understanding: design docs, RFCs
```

README.md and CHANGELOG.md stay at the repo root. Specs follow `agent-tools:spec`, not this tree. [references/docs-dirs.md](references/docs-dirs.md) maps each kind of document to its folder.

## Tool versions

`mise.toml` at the repo root pins the languages and CLIs the repo needs, with a comment on every unusual entry. `script/bootstrap` runs `mise install`. Personal tools stay in the user's global config, out of the project file. [references/mise.md](references/mise.md) has the structure.

## CI

A pipeline is a thin wrapper. It calls `script/cibuild` and holds only what the platform owns: triggers, permissions, runners, caching, secrets, and deploy gates. Build logic never lives in two places. [references/cicd.md](references/cicd.md) has the patterns.

## Local gate

`.pre-commit-config.yaml` at the repo root runs the checks that guard every commit, in seconds: fixers, then read-only checks, then fast tests. Slower checks move to `stages: [manual]`, and CI runs them through `script/cibuild`. Local hooks call the tools mise pins, so the gate and CI run the same versions. [references/pre-commit.md](references/pre-commit.md)

## Dependency updates

`renovate.json` at the repo root. Pin everything, let the bot bump: package manifests, action digests, pre-commit hook revs, and the tools in `mise.toml`. Non major updates automerge overnight after a release-age wait. Major updates stay PRs. Use one update mechanism. A repo on Dependabot keeps it and doesn't add Renovate. [references/renovate.md](references/renovate.md)

## Commits and releases

Every commit is a [Conventional Commit](https://www.conventionalcommits.org/), and the version follows from the commits under semver: `feat` is a minor release, `fix` and `perf` a patch, and `!` or a `BREAKING CHANGE:` footer a major one. Cocogitto enforces it from `cog.toml`: the gate runs `cog verify` at the `commit-msg` stage, `script/cibuild` runs `cog check --from-latest-tag`, and `script/release` runs `cog bump --auto` to tag and write `CHANGELOG.md`. Cocogitto is for new setups. A repo already on semantic-release keeps it, and `script/release` runs `npx semantic-release`. So does a repo on release-please, commitizen, or changesets, with its own commands. [references/releases.md](references/releases.md)

## Check

- Run every script you added, from the repo root, and watch it exit 0. A script you didn't run is a draft, not an entry point.
- Run `mise install` after changing `mise.toml`.
- Run `cog check` and `cog bump --auto --dry-run` after changing `cog.toml`.
- Run the whole gate after changing it: `prek run --all-files`, or `pre-commit run --all-files`, and fix what it flags.
- Leave nothing with two homes. When you add `script/test`, point the README, CI, and done checks at it, and delete the inline command each used to carry.

## Report

The entry points added or changed, the conventions you matched instead of replaced, and any piece that ended up with two homes.
