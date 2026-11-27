# Commits and releases

Every commit on the main branch is a [Conventional Commit](https://www.conventionalcommits.org/), and the version follows from them under [Semantic Versioning](https://semver.org/). [Cocogitto](https://docs.cocogitto.io/) (`cog`) checks the messages, bumps the version, tags it, and writes the changelog, so nobody picks a version number by hand.

## Commit messages

```text
<type>(<optional scope>): <summary>

<optional body: why, not what>

<optional footer: BREAKING CHANGE: ..., Refs: #123>
```

| Type                                                        | Release |
| ----------------------------------------------------------- | ------- |
| `feat`                                                      | Minor   |
| `fix`, `perf`                                               | Patch   |
| `!` after the type, or a `BREAKING CHANGE:` footer          | Major   |
| `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `style` | None    |

- Write the summary in the imperative, in lowercase, with no period: `fix(api): retry on 502`.
- One change per commit. A commit that needs `and` in its summary is two commits.
- With squash merges, the PR title becomes the commit, so the PR title follows the same format.

## Setup

1. Pin the tool in `mise.toml`: `cocogitto = "<version>"`. See [mise.md](mise.md).
2. Add `cog.toml` at the repo root:

```toml
tag_prefix = "v"
# Release only from main, so a stray branch can't cut a version.
branch_whitelist = ["main"]
pre_bump_hooks = ["script/cibuild"]
post_bump_hooks = ["git push", "git push origin {{version_tag}}"]

[changelog]
path = "CHANGELOG.md"
template = "remote"
remote = "github.com"
owner = "<owner>"
repository = "<repo>"
```

3. Tag the commit where the repo adopts the convention, such as `git tag v0.1.0`. `cog check --from-latest-tag` errors when the repo has no tag, and older commits that predate the convention would fail a full `cog check`.

## Enforce

- **Locally:** check each message in the gate, at the `commit-msg` stage. Add `commit-msg` to `default_install_hook_types`, so `prek install` installs that hook too:

```yaml
default_install_hook_types: [pre-commit, commit-msg]
repos:
  - repo: local
    hooks:
      - id: cog-verify
        name: check commit message (cocogitto)
        entry: mise exec cocogitto -- cog verify --file
        language: system
        stages: [commit-msg]
```

- **In CI:** `script/cibuild` runs `cog check --from-latest-tag`, so a commit made with `--no-verify` still fails the pipeline. The checkout needs the tags: `fetch-depth: 0` on `actions/checkout`.

Use the pre-commit hook, not `[git_hooks]` in `cog.toml` with `cog install-hook`, so the repo keeps one gate. See [pre-commit.md](pre-commit.md).

## Release

`script/release` runs `cog bump --auto`. It reads the commits since the last tag, picks the next version, runs the `pre_bump_hooks`, commits the changelog, tags, and runs the `post_bump_hooks`. Add the repo's publish step, such as a package upload, as the last `post_bump_hooks` entry.

- Preview the next version with `cog bump --auto --dry-run`.
- When there's nothing to release (only `docs` or `chore` commits), `cog bump` exits without a tag.
- A post-bump hook that fails doesn't roll back. Fix the cause and finish the remaining steps by hand.

To release from CI, run `script/release` in its own job on `main`, gated on the CI job, with `contents: write` for that job only. See [cicd.md](cicd.md).

## Match the repo first

Cocogitto is for new setups. A repo that already releases with another tool keeps it:

```bash
git ls-files | rg '^(\.releaserc.*|release\.config\.[cm]?js)$'; rg --files-with-matches '"semantic-release"' package.json
```

- **semantic-release:** keep it. Commits follow its preset, usually the same Conventional Commits types. `script/release` runs `npx semantic-release`, and `npx semantic-release --dry-run` previews the next version. When the repo has commitlint, the gate checks messages with it instead of `cog verify`.
- **release-please, commitizen, changesets, or goreleaser:** keep it, follow its commit rules, and use its own check.
- Offer once to move to cocogitto, and move only when the user agrees.

A repo with no versioning, such as a dotfiles repo, still gets Conventional Commits, and adds `cog.toml` only when it starts tagging releases.
