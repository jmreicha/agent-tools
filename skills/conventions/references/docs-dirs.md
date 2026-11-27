# The docs tree

One home per document, one folder per Diátaxis mode. The docs skill (`agent-tools:docs`) owns the prose rules and the mode definitions. This page owns placement.

```text
docs/
  adrs/          Architecture decision records (agent-tools:adr owns them)
  tutorials/     Learning-oriented: onboarding, first project
  how-to/        Task-oriented: runbooks, setup and fix guides
  reference/     Lookup: API, CLI, config, module docs
  explanation/   Understanding: design docs, RFCs, architecture
```

## Where each document goes

| Document              | Home                                                                          | Owned by           |
| --------------------- | ----------------------------------------------------------------------------- | ------------------ |
| README                | Repo root. A short how-to: install and first run, linking into `docs/`.       | `agent-tools:docs` |
| CHANGELOG             | Repo root, Keep a Changelog format.                                           | `agent-tools:docs` |
| ADR                   | `docs/adrs/`                                                                  | `agent-tools:adr`  |
| Design doc            | `docs/explanation/`                                                           | `agent-tools:docs` |
| RFC                   | `docs/explanation/`                                                           | `agent-tools:docs` |
| Runbook               | `docs/how-to/`                                                                | `agent-tools:docs` |
| Tutorial              | `docs/tutorials/`                                                             | `agent-tools:docs` |
| API, CLI, config docs | `docs/reference/`                                                             | `agent-tools:docs` |
| Spec                  | The spec skill's home (`yass`, Spec Kit, or the repo's own), outside `docs/`. | `agent-tools:spec` |

## Rules

- Match the repo first: existing folders, frontmatter, and naming win. A repo with `docs/guides/` keeps `docs/guides/`, and new guides go there.
- A document with no row in the table above gets the mode's folder, not a new top level one. The folder set stays closed: `adrs/`, `tutorials/`, `how-to/`, `reference/`, `explanation/`.
- Link, don't copy. When a doc needs another's content, link to the one home of that content.
- To set up the folders with Vale checks and frontmatter, follow `references/docs-site.md` in the docs skill. Do this only when the user asks.
