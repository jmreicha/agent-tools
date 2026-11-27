---
name: research
description: Gather context before building, from current library docs and source (context7), real code on GitHub, and the web, then recommend one approach. Use when about to implement a feature, adopt or upgrade a library, choose between approaches or technologies, or see how other projects solved a similar problem.
version: 2.0.0
tags: [research, planning, documentation]
---

# Research

Find out how the library and other projects actually work before you build, so the plan rests on facts instead of memory.

## Ask what you can't look up

Ask the user only for what the repo and the request don't tell you:

- Requirements and constraints.
- Preferred libraries or approaches.
- Docs or links they trust.
- What matters most: performance, simplicity, or maintainability.

Skip the questions the user already answered.

## Read current docs and source

Use the `ctx7` CLI for every library, even ones you know. Your memory may predate the version the repo uses.

```bash
ctx7 library "<official name>" "<the question>"
ctx7 docs </org/project> "<the question>"
ctx7 code </org/project> "<regex or symbol>"
ctx7 get-upgrade-guide </org/project> <from-version> <to-version>
```

- Pin the version the repo uses: `/org/project/<version>`.
- Use `ctx7 code` when the docs are thin and the source holds the answer, such as a default value or an error path.
- Use `ctx7 get-upgrade-guide` for any upgrade or migration.

## Find real code

Search GitHub for code that would appear in a file, not prose:

```bash
gh search code "oauth2.Config{" --language go --limit 20
```

- Good queries: `oauth2.Config{`, `rate.NewLimiter`, `runs-on: ubuntu-latest`.
- Bad queries: `oauth tutorial`, `best practices`.
- Run one search for the main pattern and one for its error handling: retries, timeouts, and empty results.
- Prefer maintained repos with recent commits. Check that the version matches.
- Search issues for known bugs and workarounds before you trust a pattern: `gh search issues "<error or symbol>" --repo <org/repo>`.
- To read one repo in depth, clone it shallow into the scratchpad and search it with `rg`, or with `ast-grep` for code structure, such as every call to a function.

## Read the web last

Use `WebSearch` and `WebFetch` for tradeoffs, design discussions, and anything the docs don't cover. Prefer official blogs and pages from the last year. Fetch the links the user gave first.

- Use `WebSearch` with `mode: "extended"` when a standard search comes back thin or stale, or for releases from the last few weeks.
- When `WebFetch` fails or returns an empty shell, the page likely renders with JavaScript or blocks bots. Read it with `agent-browser read <url>` instead. Run `agent-browser skills get core` first if you haven't used it this session.

## Match depth to risk

| Scenario                | Goal                                    | Queries                   |
| ----------------------- | --------------------------------------- | ------------------------- |
| Well known pattern      | Confirm the recommended pattern         | 1 doc, 1 code             |
| Standard feature        | Confirm the common approaches           | 1 doc, 1-2 code           |
| New kind of feature     | Compare alternatives and tradeoffs      | 2-3 doc, 3-4 code         |
| Critical infrastructure | Understand failure modes and edge cases | Several from every source |

Default to a quick scan. Go deeper when the user doesn't know the technology, the risk is high (security, data integrity, performance), or the codebase has no pattern to copy.

## When a source fails

Record the exact error, keep going with the other sources, and say what's missing and what you assumed because of it. If `ctx7` fails with a quota error, tell the user to run `ctx7 login` or set `CONTEXT7_API_KEY`. Don't fall back to memory without saying so.

## Report

```markdown
## Research: <feature>

**Recommendation:** <one approach, and why it fits the requirements>

**Patterns found:**

- <pattern> (<source>)

**Tradeoffs:**

- <approach A>: <when it wins, what it costs>
- <approach B>: <when it wins, what it costs>

**Implementation notes:**

- <a finding that changes the code, a pitfall, a config detail, how to test it>

**Open decisions:** <what the user must choose, and why>

**Sources:** <docs pages, repo/file links, articles>
```

Label a guess as a guess: "My best guess is…". Don't start implementing until the user approves the approach.
