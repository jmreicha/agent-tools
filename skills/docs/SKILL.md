---
name: docs
description: Technical-writing standard for engineers, with Diátaxis page types, Google developer style, STE and Global English rules, and lint checks for Markdown and prose. Use whenever writing, editing, or reviewing prose for engineers, such as READMEs, docs pages and sites, tutorials, how-tos, reference, troubleshooting, runbooks, ADRs, RFCs, design docs, changelogs, PR descriptions, commit messages, issue bodies, or code comments.
version: 3.0.0
tags: [documentation, writing, style]
---

# Technical writing

<!-- Forked from cursor/plugins pstack/skills/technical-writing (MIT, (c) 2026 Lauren Tan). -->

Write so a tired engineer understands on the first read.

- Cut every word that does no work.
- Use the short, everyday word: "use", not "utilize".
- When a rule makes a sentence worse, fix the sentence another way or leave it alone.
- Write the real symbol, file, flag, or command name, not a synonym or a description of it.
- Don't invent jargon. Use the words a developer would say out loud. Say what a named pattern means the first time.

Read [references/voice.md](references/voice.md) first, and write in that voice from the first draft. It's the author's own voice, and it overrides the rules below where they conflict. The rules and linters come after.

## Before you write

- Read the repo first: existing docs, their folder layout, frontmatter, and naming. Match them.
- Ask the user for the real specifics: commands, UI labels, endpoints, and expected output. Never invent product behavior.
- If the page already exists, don't overwrite it. Review it against this skill and suggest edits.

## Vary the rhythm

- Mix sentence lengths. Split the sentence that carries two thoughts. Keep the long sentence that carries one.
- Have a view. Recommend one path in any mode, with its reason in a sentence. Keep the full argument and the opinions for explanation, and keep reference dry.
- Be specific. Not "schema changes can cause issues" but "a column rename fails the build".

## Pick the mode first (Diátaxis)

One document, one mode. Don't mix modes. Split and link instead.

Ask two questions to pick the mode:

| The doc is about… | The reader is… | Mode        |
| ----------------- | -------------- | ----------- |
| Doing             | Learning       | Tutorial    |
| Doing             | Working        | How-to      |
| Understanding     | Working        | Reference   |
| Understanding     | Learning       | Explanation |

Map common docs to a mode:

- Runbook: how-to.
- ADR, RFC, design doc: explanation.
- API, CLI, and config docs: reference.
- Onboarding guide: tutorial.
- README: a short how-to (install, first run) that links to the other modes. Use the README outline in [references/page-types.md](references/page-types.md) for new READMEs only.

Ask the questions again at the section and paragraph level. A "why" paragraph in a how-to, or a step list in an explanation, means the doc mixes modes. Move it out and link to it.

What each mode looks like:

- **Tutorial: learning by doing.** Say what the learner builds. Every step produces a visible result, and you say what they should see. Explanation gets one clause and a link.
- **How-to: steps to a goal.** Solve the reader's problem. Assume competence. Action only. Allow forks. Name the guide by the task.
- **Reference: facts for lookup.** Only describe. Be dry and complete. Mirror the structure of the thing described. When a fact isn't confirmed, say so in the entry, such as "Not verified on Windows."
- **Explanation: understanding and why.** One bounded topic. Give context: design decisions, history, constraints, alternatives. This is where opinions and the full case for a recommendation go.

Use the outline for the mode in [references/page-types.md](references/page-types.md). For API, CLI, config, and module docs, use [references/reference.md](references/reference.md).

## Write sentences to the reader (Google developer style)

- Talk to the reader as "you", in the present tense. Use "I" for your own experience, guesses, and choices ("My best guess is…", "I picked X because…"), and "we" in docs the team owns.
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
- Write procedures as direct, active commands. Don't narrate them.
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

## Write sections that stand alone

Readers land on one section from search, and agents retrieve one chunk at a time.

- Never point by position, such as `as mentioned above` or `see below`. Link to the section by name.
- Write full names in headings, such as `retry.max_attempts`, not `max_attempts` under a "Retry" heading.
- Give literal values: numbers, defaults, ranges, and limits. Not `a reasonable number`.
- Name the version or date instead of `currently`, `new`, or `latest`. Put version requirements in the prerequisites, not in code comments.
- Don't hide steps or entries in tabs or collapsed sections.

## Write code blocks to copy

- Name the language on every code block.
- Leave out the `$` prompt. Put output in its own block after "The output is similar to this:".
- Write placeholders as `<angle-brackets>`, and use one name per value everywhere on the page.
- Use long flags in examples: `--header`, not `-H`.
- Show realistic, complete output. Agents and readers match on the literal text.
- Don't pipe examples through tools the reader may not have, such as `jq`, unless the doc is about that tool.

## Voice and specifics

- PR descriptions and commit messages are writing too. Every layer except Diátaxis applies to them. A PR body is a briefing that a reviewer can read in under a minute. Don't paste agent logs, SHA lists, or metric tables. Link them.
- Code comments: 1-2 lines, say why, not what.
- Product UI strings are not documentation. Use the product's copy guidelines for those.
- Match the repo's existing code snippet indentation. Write real paths. Make every count or tree claim true at the commit that lands it, and include the command that regenerates it.

## Check the prose

Run these steps in order on the prose files you changed. Skip a step whose skill or tool isn't installed, and don't install it yourself.

1. Run the **humanizer** skill. It owns the AI-slop catalog: AI vocabulary, filler, hedging, and formatting tells.
2. Run `oxfmt <files>` to format Markdown, YAML, and JSON. Use the repo's `oxfmt` config when there is one. Skip this step when the repo formats with another tool, such as Prettier, so the two don't fight over the same files.
3. Run `rumdl check <files>` for Markdown structure: heading levels, code block languages, bare URLs, and `$` prompts. Use the repo's `rumdl` or `markdownlint` config when there is one. Without one, add `--disable MD013`, because prose isn't wrapped at 80 characters.
4. Run `vale <files>`. Treat each alert as advice. Fix the clear errors, and leave a sentence alone when the fix makes it worse. The `Docs*` styles in [vale/](vale/) check the rules in this skill.
5. Run `lychee --offline --include-fragments --no-progress <files>`. Fix every broken local link and anchor.

With no `.vale.ini` in the repo, Vale uses the global config at `~/Library/Application Support/vale/.vale.ini` (macOS). It uses the same settings as the repo config in [references/docs-site.md](references/docs-site.md).

When Vale is installed with the global config, check that `<StylesPath>/Docs` exists. Vale skips a missing style without warning. If it's missing, link this skill's styles into the folder that `vale ls-dirs` prints as `StylesPath`.

```bash
for s in Docs DocsHowTo DocsTroubleshooting DocsReference; do ln -sfn "<this-skill>/vale/$s" "<StylesPath>/$s"; done
```

To set up a docs folder or site, or to add these checks to a repo, follow [references/docs-site.md](references/docs-site.md). Do this only when the user asks.
