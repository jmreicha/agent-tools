# Code paths

New code goes next to its nearest relative. Read the code that resembles what you're adding and follow its folder, naming, and layout. Only when no relative exists, use the language's idiomatic layout.

## Top level

| Dir       | Holds                                                               |
| --------- | ------------------------------------------------------------------- |
| `src/`    | Product code                                                        |
| `script/` | Entry points and maintenance scripts (see [scripts.md](scripts.md)) |
| `docs/`   | Every document (see [docs-dirs.md](docs-dirs.md))                   |
| `tests/`  | Tests, when the language doesn't keep them beside the code          |

## By language

| Language | Idiomatic layout                                                                                                                                                           |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Go       | `cmd/<name>/` holds each binary's `main`. `internal/` holds private packages. `pkg/` only for code shared outside the repo. Tests sit beside the code as `<file>_test.go`. |
| Python   | `src/<package>/` with `pyproject.toml`. `tests/` mirrors the package. An executable goes in the package and gets a console script entry.                                   |
| TS/JS    | `src/` for product code. Tests sit beside the code as `*.test.ts`. `package.json` scripts are entry points only when the repo has no `script/` dir.                        |
| Rust     | `src/lib.rs` for the crate, `src/bin/<name>/` for each binary, `tests/` for integration tests.                                                                             |

## Where a new file goes

1. Next to its nearest relative, matching that file's style.
2. The language idiom, when no relative exists.
3. Nowhere else. When neither has an answer, the placement is a design decision: think it through with `agent-tools:rubber-duck`, and record the outcome with `agent-tools:adr` when it's hard to reverse.

A test mirrors its source path. If the source moves, the test moves with it, in the same change.

## One home per kind of file

When a kind of file has two homes, such as `utils/` and `lib/`, pick the one more code already uses, move the stragglers, and delete the empty one in the same change. An agent copies the nearest example, so the dir you leave behind is the convention you chose.
