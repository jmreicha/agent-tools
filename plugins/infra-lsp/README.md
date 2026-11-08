# infra-lsp

Language server (LSP) plugin for infrastructure files. It gives Claude diagnostics after each edit
and an `LSP` tool for definitions and references. It covers the languages that have no official
Anthropic LSP plugin.

| Server                 | Files            | Install the binary                               |
| ---------------------- | ---------------- | ------------------------------------------------ |
| `bash-language-server` | `.sh`, `.bash`   | `npm i -g bash-language-server` (+ `shellcheck`) |
| `yaml-language-server` | `.yaml`, `.yml`  | `npm i -g yaml-language-server`                  |
| `terraform-ls`         | `.tf`, `.tfvars` | `mise use -g aqua:hashicorp/terraform-ls`        |
| `docker-langserver`    | `.dockerfile`    | `npm i -g dockerfile-language-server-nodejs`     |

The plugin only tells Claude Code which server to start for which file types. The binaries must
be on the `PATH` of the shell you start `claude` from. A missing binary shows up in the
`/plugin` **Errors** tab.

## Notes

- `.zsh` isn't mapped, because shellcheck doesn't support zsh and reports false errors.
- YAML uses SchemaStore schemas (GitHub Actions, compose and so on). Kubernetes schemas apply to
  files under `k8s/`, `manifests/` or `kubernetes/` directories. Edit `settings` in `.lsp.json`
  to change that.
- Claude Code matches files by extension only, so a plain `Dockerfile` (no extension) isn't
  covered. Only names like `app.dockerfile` are.
- `terraform-ls` doesn't understand `terragrunt.hcl`.

## Install

```bash
claude plugin marketplace add jmreicha/agent-tools
claude plugin install infra-lsp@agent-tools
```

Test a local checkout with `claude --plugin-dir ./plugins/infra-lsp`.
