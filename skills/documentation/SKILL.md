---
name: documentation
description: Layered technical-writing standard (Diátaxis structure, Google developer style, STE instruction rules, Global English syntax). Use whenever writing, editing, or reviewing prose for engineers — READMEs, docs pages, tutorials, how-tos, reference, ADRs, RFCs, design docs, runbooks, changelogs, PR descriptions, commit messages, issue bodies, or code comments.
version: 2.0.0
tags: [documentation, writing, style]
---

# Technical writing

<!-- Forked from cursor/plugins pstack/skills/technical-writing (MIT, (c) 2026 Lauren Tan). See LICENSE in this directory. -->

Write so a tired engineer understands on the first read.

- Cut every word that does no work.
- Use the short, everyday word: "use", not "utilize".
- When a rule makes a sentence worse, fix the sentence another way or leave it alone.
- Write the real symbol, file, flag, or command name, not a synonym or a description of it.
- Don't invent jargon. Use the words a developer would say out loud. Say what a named pattern means the first time.

## Vary the rhythm

- Mix sentence lengths. Split the sentence that carries two thoughts. Keep the long sentence that carries one.
- Have a view in explanation. Keep reference dry.
- Be specific. Not "schema changes can cause issues" but "a column rename fails the build".

## Pick the mode first (Diátaxis)

One document, one mode. Don't mix modes. Split and link instead.

- **Tutorial: learning by doing.** Say what the learner will build. Every step produces a visible result, and you say what they should see. Explanation gets one clause and a link.
- **How-to: steps to a goal.** Solve the reader's problem. Assume competence. Action only. Allow forks. Name the guide by the task.
- **Reference: facts for lookup.** Only describe. Be dry, complete, and sure. Mirror the structure of the thing described.
- **Explanation: understanding and why.** One bounded topic. Give context: design decisions, history, constraints, alternatives. Opinion is allowed here and nowhere else.

## Write sentences to the reader (Google developer style)

- Talk to the reader as "you", in the present tense.
- Say who does what. Passive is fine only when the actor is unknown or beside the point.
- Write instructions as commands. Put the condition before the instruction and the common case first.
- No buzzwords, no figurative language, no "please", and never "simply", "easy", or "quickly" in a procedure.
- Don't pre-announce, and don't start consecutive sentences with the same phrase.
- Link with words that say where the link goes.
- Headings carry the point, in sentence case. One h1 per page, no skipped levels.
- Numbered lists for sequences, bullets for everything else. Introduce a list with a complete sentence. Keep items parallel.
- Code goes in code font. UI elements go in bold. Use serial commas. Drop "etc.".

## Make statements load one at a time (STE rules)

- One instruction per sentence. One thought per sentence everywhere else.
- Split instructions longer than about 20 words and other sentences longer than about 25.
- Put the warning or condition before the step it guards.
- Keep "the" and "a".
- Give each word one meaning, and pick one word per action.
- Write procedures as direct commands, never as narration and never in the passive.
- Avoid "-ing" words where you can.

## Leave no sentence open to two readings (Global English)

- Keep words like "only" and "not" next to the word they change.
- Break up long noun strings.
- Make every "it", "they", and "this" point at one obvious thing. Never use "this" or "which" to point at a whole clause.
- Don't drop verbs, or the small words that show structure, such as "that".
- Repeat the article in a series when it prevents a misread. Say which parts "and" or "or" joins.
- Use periods, not semicolons or em dashes. No slashes, and no "(s)". Make text in parentheses a full grammatical unit.
- Call each thing by one name, everywhere.
- Skip idioms, colloquialisms, Latin abbreviations, and metaphors.

## Voice and specifics

- If the **humanizer** skill is available, run it on every doc this skill touches. It owns the AI-slop catalog: AI vocabulary, filler, hedging, formatting tells.
- PR descriptions and commit messages are writing too. Every layer except Diátaxis applies to them. A PR body is a briefing that a reviewer can read in under a minute. Don't paste agent logs, SHA lists, or metric tables. Link them.
- Code comments: 1-2 lines, say why, not what.
- Product UI strings are not documentation. Use the product's copy guidelines for those.
- Match the repo's existing code snippet indentation. Write real paths. Make every count or tree claim true at the commit that lands it, and include the command that regenerates it.

## Check the prose with Vale and lychee

Run both tools on the prose files you changed. Skip a tool that isn't installed, and don't install it yourself.

- Run `vale <files>`. Treat each alert as advice. Fix the clear errors, and leave a sentence alone when the fix makes it worse.
- Run `lychee --offline --include-fragments --no-progress <files>`. Fix every broken local link and anchor.
- To lint a commit message, pipe it in: `vale --path=COMMIT_EDITMSG < msg.txt`.

With no `.vale.ini` in the repo, Vale uses the global config at `~/Library/Application Support/vale/.vale.ini` (macOS).

## Set up Vale and lychee in a repo

Do this only when the user asks for it. Each repo owns its config so that local runs and CI agree.

1. Add a `.vale.ini` that lists `StylesPath`, `Packages`, and `BasedOnStyles`. Start with `Google` and `proselint`. Add `Diataxis` only when the docs live in one folder per kind. Add `Commits` with a `[COMMIT_EDITMSG]` section to lint commit messages.
2. Add the `StylesPath` folder to `.gitignore`, and keep the project vocabulary in `<StylesPath>/config/vocabularies/<Name>/accept.txt`. Commit that file with `git add -f`. Vale also enforces the case of each accepted term, so prefix lowercase tool names with `(?i)`. Otherwise `aws` flags every `AWS`.
3. Add a `lychee.toml` with URL exclusions and accepted status codes.
4. Add the hooks to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/vale-cli/vale
  rev: v3.28.1
  hooks:
    - id: vale
      args: [--no-global]
      types_or: [markdown, rst]
    - id: vale-commit-msg
- repo: https://github.com/lycheeverse/lychee
  rev: lychee-v0.24.2
  hooks:
    - id: lychee
      args: [--offline, --include-fragments, --no-progress]
      types_or: [markdown, rst]
```

5. In CI, run `vale sync` before the hooks. Check external URLs in a separate scheduled or PR job with `lycheeverse/lychee-action`, because network checks fail for reasons unrelated to the commit.
