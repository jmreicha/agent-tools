# Entry points

The scripts-to-rule-them-all pattern: every way to run, build, test, or ship the repo lives in `script/` as a thin executable named for its verb. One command per task. Humans, agents, and CI run the same command, so an answer that works locally works in the pipeline, and the README documents one line instead of ten steps.

## No build systems

Entry points are shell scripts. The house never introduces a `Makefile`, `Taskfile`, `justfile`, or mise tasks, and doesn't extend one that already exists.

- Shell runs anywhere the repo runs, and a script reads top to bottom. A build system is another syntax with its own quirks: Make's tabs, Taskfile's YAML, and the expression syntax in `just`.
- Every build system calls shell commands eventually. Skip the middle layer.
- A repo already on `make`, `just`, or mise tasks keeps its system: never run a second one alongside it. Propose migrating its targets into `script/` verbs, and migrate only when the user agrees.

## Verbs

| Verb      | Job                                                                         |
| --------- | --------------------------------------------------------------------------- |
| bootstrap | Install dependencies and tool versions. Ends at a repo that builds.         |
| setup     | Prepare local state after bootstrap: seed data, config, env. Safe to rerun. |
| test      | Run the test suite. The command CI runs, nothing shorter.                   |
| server    | Run the app locally, on the dev port.                                       |
| console   | Drop into a REPL or shell with the app's context loaded.                    |
| cibuild   | Everything CI must prove: test, lint, build. Composes the other verbs.      |
| release   | Cut a version: bump, tag, artifact.                                         |

Drop the verbs the repo doesn't need. A library has `bootstrap` and `test`, and needs no `server`.

## Rules

- One job per verb. A verb that needs a flag for a second job is two verbs.
- Thin. A verb composes the real commands and implements no logic. When a verb grows logic, move the logic into the product, such as a CLI subcommand or a lib function, and let the verb call it.
- Executable, with a shebang. In Bash, `set -euo pipefail`, and echo each step before it runs, so a failure names the step it died in.
- Write it in the repo's stack, whatever that is. The calling convention is what stays fixed: `script/<verb>` from the repo root.
- Add a verb when a command is about to be documented twice, in the README, CI, or a done check. Then point every copy at the verb.

A short `script/test` is enough to show the shape:

```bash
#!/usr/bin/env bash
set -euo pipefail
pytest -q
```

## Maintenance scripts

Scripts that keep the repo itself running, and aren't entry points for the product, also live in `script/`, named for what they do: `gen-docs.py`, `check-layout.py`. A script that carries logic gets a `test_<name>` companion beside it. Run the companion when you change the script.

## What calling them looks like

- The README documents verbs, not the commands inside them: getting started is `script/bootstrap` then `script/server`.
- Done checks quote the verb, `script/test` exits 0, so the check survives a tool change.
- CI runs `script/cibuild`. See [cicd.md](cicd.md).
- `script/bootstrap` runs `mise install` first when the repo pins tools. See [mise.md](mise.md).

## What doesn't belong in script/

Product code (`src/`), libraries, one off migrations, and documents. If a caller needs the logic inside a script, the logic belongs in the product, with the script as its thin caller.
