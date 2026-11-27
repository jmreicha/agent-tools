# Tool versions with mise

`mise.toml` at the repo root is the source of truth for the tools the repo needs: language versions, and the CLIs no package manifest owns. Package managers own dependencies (`package.json`, `pyproject.toml`). mise owns the tools themselves.

## Project file

Group `[tools]` by backend, and comment every entry whose reason isn't obvious. Pin exact versions, so a local run and a CI run use the same tool:

```toml
[tools]
# Languages: pinned exact, so local and CI match.
node = "22.14.0"
python = "3.12.7"

# Project CLIs, by backend, with the reason wherever it isn't obvious.
"aqua:hashicorp/terraform" = "1.10.5" # State format needs this major.
"npm:oxlint" = "6.1.0"
"pipx:pre-commit" = "4.0.1"
```

## Split from the global config

| File                         | Holds                                                       | Version style                     |
| ---------------------------- | ----------------------------------------------------------- | --------------------------------- |
| Repo `mise.toml`             | What the repo can't build without: languages, project CLIs. | Pinned exact.                     |
| `~/.config/mise/config.toml` | Personal tools, every repo on the machine.                  | `latest` and `lts`, so they roll. |

A CLI goes in the project file only when the repo can't build without it. Everything else stays global.

## Workflow

- Add a tool with `mise use <tool>@<version>`, which writes `mise.toml`. Never `mise use -g` in a repo: that writes the global config.
- `script/bootstrap` runs `mise install` before the package manager steps.
- One off command with a tool the repo doesn't pin: `mise x <tool>@<version> -- <command>`.
- CI installs the pinned tools with the mise setup action, cached. See [cicd.md](cicd.md).

## Idiomatic version files

mise reads `.python-version`, `.nvmrc`, and `.tool-versions` only where `mise.toml` doesn't pin the tool. Keep one source of truth. When the repo adopts mise, move versions into `mise.toml` and delete the idiomatic files, unless another tool still needs them.

## Tasks stay in script/

mise can run tasks too. The house never uses that: entry points are shell scripts in `script/` (see [scripts.md](scripts.md)), so `mise.toml` holds tools only and no task has two homes. A repo that already uses mise tasks keeps them until the user agrees to migrate.
