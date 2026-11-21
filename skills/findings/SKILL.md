---
name: findings
description: |
  Maintains a per repo findings file that tracks mistakes, corrections, and
  what works. Use when starting any session in a repo, and whenever you or
  the user catch a mistake. Read the file before doing anything else. Write
  to it as you work, not just at session boundaries, and log your own
  mistakes as well as user corrections. The file lives in the repo at
  `./context/findings.md`.
version: 1.1.0
tags: [memory, learning, session]
---

# Findings

Keep a Markdown file per repo that tracks mistakes, corrections, and patterns that work or don't. Read it before you do anything else, and update it whenever you learn something worth keeping.

This skill runs in every session. It needs no trigger.

## Read the findings file first

At the start of every session, read `./context/findings.md` before anything else. Apply what's in it without announcing that you read it. The user wants the mistake not to happen again, not a status update.

If the file doesn't exist, create it:

```markdown
# Findings

## Corrections

| Date | Source | What went wrong | What to do instead |
| ---- | ------ | --------------- | ------------------ |

## User preferences

- (Add these as you learn them.)

## Patterns that work

- (Approaches that succeeded.)

## Patterns that don't work

- (Approaches that failed, and why.)

## Domain notes

- (Project context that matters.)
```

Change the sections to fit the repo. You're the one reading it next session, so write it for that.

Note: the file lives in the repo and can get committed. Never put secrets, tokens, or customer data in it.

## Update it as you work

Write to the file as soon as you learn something, not only at the start and end of a session. Log an entry when:

- You hit an error and work out why.
- The user corrects you. Log what you did and what they wanted.
- You catch your own mistake. It counts as much as a user correction, because only you know what went wrong.
- An approach fails. Log it and why, so you don't repeat it.
- An approach works well. Log the pattern.

Reread the file mid-task when you're about to do something you've gotten wrong before. Treat it as working memory that lasts across sessions, not a journal you write in once.

## What to log

Log anything that would change your behavior next session:

- Your own mistakes: wrong assumptions, bad approaches, misread code, failed commands, and fixes you had to redo.
- User corrections: anything the user told you to do differently.
- Surprises about this repo, its tools, or its patterns.
- Preferences: how the user likes things done, such as style, structure, and process.
- What worked, especially when it wasn't obvious.

Be specific. "Made an error" doesn't help. "Assumed the API returns a list, but it returns a paginated object with `.items`" does.

## Keep the file short

Every 5 to 10 sessions, or when the file passes 150 lines, consolidate it:

- Merge duplicate entries into one rule.
- Move repeated corrections to "User preferences".
- Remove entries that a top level rule already covers.
- Archive notes that are resolved or out of date.
- Keep the file under 200 lines.

A 50-line file of hard-won rules beats a 500-line log of raw entries. Past about 200 lines, the useful entries get buried and stop changing what you do.

## Example

Early in a session, you pass arguments in the wrong order and catch it yourself. Log it:

```markdown
| 2026-02-06 | self | Passed (name, id) to createUser, but the signature is (id, name) | Check function signatures before calling. This codebase doesn't follow the usual argument order. |
```

Mid-session, the user corrects your import style. Log it:

```markdown
| 2026-02-06 | user | Used relative imports | Use absolute imports from `src/` in this repo. |
```

Later, you reread the file before editing another file, and you use absolute imports without being told.
