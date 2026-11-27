# CI pipelines

The contract: a pipeline calls `script/cibuild` and holds only what the platform owns. Test and build commands live in the verbs, so CI and humans run the same commands, and a pipeline change is a workflow review, not a build review.

`script/cibuild` runs the local gate too, `pre-commit run --all-files` or `prek run --all-files`, so the commit gate and the pipeline gate are one gate. See [pre-commit.md](pre-commit.md).

## What stays in the pipeline

| Piece       | Rule                                                           |
| ----------- | -------------------------------------------------------------- |
| Triggers    | Push and pull request, nothing fancier until needed.           |
| Permissions | Least privilege: `contents: read` until a job needs more.      |
| Runners     | The platform default, pinned by label when fleet drift bites.  |
| Concurrency | Cancel the superseded run of the same branch.                  |
| Caching     | Keyed on the lockfiles and tool files, such as `mise.toml`.    |
| Secrets     | Referenced by name. The values stay out of the file.           |
| Deploy      | A separate job, gated on the CI job, calling `script/release`. |

<!-- vale Google.Headings = NO -->

## GitHub Actions

<!-- vale Google.Headings = YES -->

`.github/workflows/ci.yml`:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<pin>
      - uses: jdx/mise-action@<pin> # Installs the versions in mise.toml, cached.
      - run: script/cibuild
```

- Pin third party actions to a full commit SHA, not a tag. Renovate keeps the pins fresh: see [renovate.md](renovate.md).
- Lint the pipeline with `actionlint`, and run a security pass with `zizmor`.
- Run `actionlint` locally before pushing. A workflow that fails on syntax wasted a CI run.

<!-- vale Google.Headings = NO -->

## GitLab

<!-- vale Google.Headings = YES -->

`.gitlab-ci.yml`:

```yaml
ci:
  script:
    - script/cibuild
```

## The drift rule

When a pipeline grows a command, an inline `pytest`, a build step, a curl, move the lines into a verb and call the verb from both places. Two copies of one command drift apart, and then CI proves something local never runs.
