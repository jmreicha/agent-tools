# The local gate

`.pre-commit-config.yaml` at the repo root runs the checks that guard every commit. The default stage is fast, seconds per commit, or people bypass the gate.

## Runner

prek is the house runner: a drop in for pre-commit configs that runs hooks concurrently, lower `priority` first, equal priorities together. Pin it in `mise.toml` with the other tools. Plain `pre-commit` runs the same config where prek isn't installed.

## Tiers

State the tiers in a comment at the top of the config, and give every hook its tier as `priority`:

| Priority | Tier                                              | Examples                                   |
| -------- | ------------------------------------------------- | ------------------------------------------ |
| 0-9      | Fixers, sequential when they touch the same files | whitespace, formatters                     |
| 10       | Read-only checks                                  | linters, syntax, config validators         |
| 20       | Fast tests                                        | unit suites for the changed files          |
| 30+      | Slow checks, `stages: [manual]`                   | renders, integration, anything with Docker |

CI runs the manual tiers. Locally, `prek run --hook-stage manual --all-files`.

## Rules

- Local hooks call the tools mise pins, so the gate and CI run the same versions. Each hook asks mise only for the tools it uses:

```yaml
- id: oxfmt
  name: format yaml and markdown (oxfmt)
  entry: mise exec npm:oxfmt -- oxfmt
  language: system
  types_or: [yaml, markdown]
  priority: 2
```

- A fixer rewrites files, and its rewrites stay mechanical, so no human reviews its diffs. A check fails.
- Scope every hook: `files:` for the paths it owns, `pass_filenames: false` for repo wide scripts, `types_or` for file kinds, and one top level `exclude:` for archive dirs.
- Name a hook for what it does, with the tool in parentheses: `lint shell scripts (shellcheck)`.
- Anything slower than about 5 seconds moves to `stages: [manual]`. So does anything that costs money, such as evals.
- `script/bootstrap` runs `prek install`, or `pre-commit install`, so a fresh clone gets the git hooks.
- When the repo has a `renovate.json`, validate it from the gate too, with the `renovate-config-validator` hook.

## Parity with CI

`script/cibuild` runs the whole gate, `prek run --all-files` or `pre-commit run --all-files`, before the tests. The local gate and the CI gate are one gate: no check exists only in the pipeline, and no pipeline step reimplements a check the gate already runs. See [cicd.md](cicd.md).
