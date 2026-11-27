# Dependency updates

`renovate.json` at the repo root is the one mechanism that keeps every pin fresh: package manifests, GitHub Action digests, pre-commit hook revs, and the tools in `mise.toml`. Pin everything, let the bot bump.

## Base config

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "helpers:pinGitHubActionDigests"],
  "labels": ["dependencies"],
  "minimumReleaseAge": "14 days",
  "prConcurrentLimit": 5,
  "recreateClosed": true,
  "vulnerabilityAlerts": { "labels": ["security"] },
  "pre-commit": { "enabled": true }
}
```

## Rules

- Wait for a release to prove stable: `minimumReleaseAge` holds minor and patch updates. Digest and pin updates skip the wait, because a digest points at a ref that already shipped.
- Automerge non major updates overnight, grouped as one branch: `automergeType: "branch"`, `automergeSchedule: ["before 3:00am"]`, and `ignoreTests: true`, because a branch automerge can't wait for CI. Major updates stay PRs a human reads.
- Updates a human must gate, such as versions that trigger heavy integration runs, get `automerge: false` and their own group.
- One update mechanism. A repo on Dependabot keeps Dependabot. Never both: they race and double the PR noise.
- The built in managers read `mise.toml`, `.pre-commit-config.yaml` hook revs, and the package manifests. A version pinned inline in a script gets a `customManagers` entry with a description, driven by a comment on the line above:

```yaml
# renovate: datasource=github-releases depName=j178/prek extractVersion=v(?<version>.*)
PREK_VERSION="2025.9.2"
```

- When one dependency is pinned in two places, group the bumps so they land in one PR: `matchPackageNames` with a shared `groupName`.
- Validate the config from the local gate, with the `renovate-config-validator` pre-commit hook. See [pre-commit.md](pre-commit.md).

## Where the pins live

Renovate bumps what the other references pin. Actions pinned by SHA in pipelines get fresh digests (see [cicd.md](cicd.md)), tools in `mise.toml` follow [mise.md](mise.md), and hook revs follow the gate itself. Exact pins plus automated bumps beat loose ranges that drift silently.
