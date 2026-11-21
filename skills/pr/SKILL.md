---
name: pr
description: Iterate on a PR until CI passes. Use when you need to fix CI failures, resolve review feedback, or continuously push fixes until all checks are green. Automates the feedback-fix-push-wait cycle.
version: 1.1.0
tags: [git, ci, github]
---

# Iterate on a PR until CI passes

Keep fixing and pushing the current branch until every CI check passes and the review feedback is resolved.

This skill needs the GitHub CLI (`gh`), signed in.

## Workflow

### 1. Find the PR

```bash
gh pr view --json number,url,headRefName
```

Stop if the current branch has no PR. Keep the PR number, because every command after this needs it.

### 2. Gather review feedback

Use the `gh` CLI to fetch review comments and reviews. Feedback lives in several places, and no single command returns all of it. Inline threads and their resolved status only come from GraphQL:

```bash
# Get repo info (owner and repo name)
gh repo view --json owner,name

# Get PR info
gh pr view {number} --json number,url,headRefName,author,reviews,reviewDecision

# Get review threads (inline comments with resolved status - requires GraphQL)
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            isOutdated
            path
            line
            comments(first: 10) {
              nodes {
                id
                body
                author { login }
                createdAt
              }
            }
          }
        }
      }
    }
  }
' -F owner={owner} -F repo={repo} -F pr={number}

# Get review comments (inline code comments)
gh api repos/{owner}/{repo}/pulls/{number}/comments

# Get issue comments (PR conversation comments)
gh api repos/{owner}/{repo}/issues/{number}/comments
```

#### Sort feedback by priority

Sort feedback with the [LOGAF scale](https://develop.sentry.dev/engineering-practices/code-review/#logaf-scale):

Look for a LOGAF marker in the comment body:

- `h:` or `[h]` or `high:` → **high** priority
- `m:` or `[m]` or `medium:` → **medium** priority
- `l:` or `[l]` or `low:` → **low** priority

Without a marker, sort by keywords.

High priority:

- `must fix`, `must change`, `security`, `critical`, `blocker`, `will break`, `wrong`, `incorrect`

Low priority:

- `nit`, `nitpick`, `suggestion`, `consider`, `could also`, `optional`, `minor`, `style`, `prefer`, `what do you think`

Everything else is `medium`.

#### Sort bot comments

Some bots post feedback you should act on. Others only post information.

Review bots, which you sort by content like human feedback:

- Sentry, Warden, Cursor, Bugbot, Seer, CodeQL, Copilot, Claude

Information bots, which you skip without comment:

- Codecov, Dependabot, Renovate, GitHub Actions, Mergify, Snyk

Review bot feedback goes into the high, medium, and low buckets with a `review_bot: true` flag. Information bot comments go into the `bot` bucket, which you skip.

#### Categories

- `high` - Must fix before merge (explicit `h:`, blockers, changes requested, security issues)
- `medium` - Should fix (explicit `m:`, standard feedback without clear priority)
- `low` - Optional (explicit `l:`, nits, suggestions)
- `bot` - Information-only automated comments, such as Codecov and Dependabot. Skip them.
- `resolved` - Already resolved threads

### 3. Triage feedback by LOGAF priority

Fix these without asking:

- `high` - must fix (blockers, security, changes requested)
- `medium` - should fix (standard feedback)

Treat review bot feedback the same as human feedback. Check each finding:

- If it's a real issue, fix it.
- If it's a false positive, skip it, and reply with a short comment that says why.
- Don't skip review bot feedback without checking it.

Ask the user about these:

- `low` - present numbered list and ask which to fix:

```text
Found 3 low-priority suggestions:
1. [l] "Consider renaming this variable" - @reviewer in api.py:42
2. [nit] "Could use a list comprehension" - @reviewer in utils.py:18
3. [style] "Add a docstring" - @reviewer in models.py:55

Which would you like to address? (e.g., "1,3" or "all" or "none")
```

Skip these without comment:

- `resolved` threads
- `bot` comments, such as Codecov and Dependabot

### 4. Check CI status

Get the check status:

```bash
# Basic check status
gh pr checks {number}

# JSON output for parsing (includes run IDs)
gh pr checks {number} --json name,state,bucket,link,workflow
```

For failed checks, get the logs:

```bash
# Get run IDs from the JSON output, then view failed logs
gh run view {run-id} --log-failed
```

#### Find the error in the logs

Search the logs for these failure markers:

- `error:`, `failed:`, `failure:`, `traceback`, `exception`
- `FAILED`, `panic:`, `fatal:`
- `ModuleNotFoundError`, `ImportError`, `SyntaxError`, `TypeError`
- `=== FAILURES ===`, `___ ___` (pytest separators)
- `npm ERR!`, `yarn error`

Read 5 lines before each marker and up to 50 lines after it.

If review bot checks (Sentry, Warden, Cursor, Bugbot, Seer, CodeQL) are still running, wait for them. They post feedback you need to check. Don't wait for information bots like Codecov.

### 5. Fix CI failures

For each failed check:

1. Read the failure logs with `gh run view {run-id} --log-failed`.
2. Read the code involved before you change it.
3. Make the smallest change that fixes the failure.

Read the logs every time. A check's name doesn't tell you what failed.

### 6. Commit and push

```bash
git add <files>
git commit -m "fix: <descriptive message>"
git push
```

### 7. Wait for CI

```bash
gh pr checks --watch --interval 30
```

### 8. Check feedback again after CI

Review bots often post feedback seconds after CI finishes. Wait 10 seconds, then check again:

```bash
sleep 10
# Re-fetch review comments using gh api commands from step 2
```

Fix any new high and medium feedback the same way as step 3. If new feedback needs code changes, go back to step 6 to commit and push.

### 9. Repeat

Go back to step 2 if CI failed or step 8 found new feedback.

## When to stop

- Done: every check passes, the check after CI finds no new high or medium feedback (including from review bots), and the user has chosen which low-priority items to fix.
- Ask for help: the same failure happens 3 times, feedback needs clarifying, or the CI infrastructure is broken.
- Stop: the branch has no PR, or it needs a rebase.
