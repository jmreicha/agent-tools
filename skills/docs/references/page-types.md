# Page types

Use the outline for the mode you picked in [the main skill](../SKILL.md). Items marked (Vale) are checked by the `Docs` style. Check the rest yourself.

Adapted from the [Kubernetes page content types](https://kubernetes.io/docs/contribute/style/page-content-types/), the [Cloudflare content types](https://developers.cloudflare.com/style-guide/documentation-content-strategy/content-types/), and the [Nimbus recipes](https://nimbus-docs.com/) (MIT).

## How-to

Title it with the task as a verb phrase: "Rotate a signing key". No "How to" prefix and no gerund.

```markdown
# <Verb the thing>

<1-2 sentences: when and why you'd do this.>

## Prerequisites

- <Access, existing setup, decisions made, versions.>

## <Steps or phase name>

1. <One action per step. Say where, then what.>

## Verify

<A command and the output to expect. Say what to do if the output differs.>

## <Irreversible closing step, if any>

## Optional: <thing>

## Next steps

- <2-4 links: the next task, the concept behind it, the reference.>
```

- Keep the happy path unbroken. Put platform variants side by side. For alternative methods, document the recommended one and link the rest.
- Put a warning before each destructive step. A page full of warnings has the wrong happy path.
- Run Verify before any step that is expensive to undo, such as a delete or a cutover.
- Keep each phase to 10 steps or fewer. (Vale)
- Include a Verify section, and end with Next steps rather than the last step. (Vale)
- Leave out Prerequisites only when there are truly none.

## README

Use this outline only for a new README. Leave an existing README alone: don't restructure or restyle it, and change only what the user asks for.

```markdown
# <Project name>

<One sentence: what it is and who it's for.>

<Optional: one screenshot or demo, for a UI or CLI tool.>

## Highlights

- <Optional. 3-5 bullets, only when the reason to use it isn't obvious.>

## Quick start

<Copyable install commands, then a first run and the output to expect.>

## Usage

<1-3 common tasks.>

## <Whatever the project needs: Configuration, Docs, Plugins>

## Development

<Optional. How to run the tests and lint, or a link to CONTRIBUTING.md.>

## License

<Optional. One line that links to LICENSE.>
```

- Quick start is always the first heading. Readers decide from the first screen, then copy a command.
- No badges.
- Link to the changelog and to longer docs. Don't copy them in.
- Past about 300 lines, the README is turning into the manual. Move sections into `docs/`, or add a table of contents.

## Tutorial

Use the how-to outline, with two changes:

- Add an Objectives list after the intro: what the reader builds and learns.
- Add a Cleanup section before Next steps that removes what the tutorial created.

A tutorial must not fail. Pin versions, show the output of every step, and give explanation one clause and a link.

## Explanation

```markdown
# <Noun phrase naming the concept>

<One paragraph that defines it in checkable terms, such as "at least once" or "not ordered".>

## <One idea per section>

## Next steps
```

- Cover one bounded topic. Include design decisions, history, constraints, and alternatives. Recommendations and opinions belong here.
- No procedures. Code that shows the idea is fine. Code the reader follows along with belongs in a how-to.
- Say what the concept is not, as flat bullets.
- Use a comparison table when there is a real either-or.

## Design doc

A design doc is explanation mode for a system you plan to build or change. Use this outline only for a new design doc. Leave an existing design doc alone: don't restructure or restyle it, and change only what the user asks for.

```markdown
# <System or change name>

<1-2 paragraphs: what the doc covers and why now. End with what it doesn't cover: "X is not meant to replace Y.">

## Problem

<The current state and what it costs: toil, risk, incidents. Use real numbers, and name their source and date.>

## Goals and non-goals

**Must have:**

1. <Requirement with a literal value: "RPO 24 hours".>

**Nice to have:**

1. <Requirement.>

**Non-goals:**

- <What the design deliberately leaves out, and why.>

## Proposal

<The design, with a diagram of it.>

## Alternatives

<Each option with its tradeoffs. Use a comparison table when there are 3 or more options. Pair each downside with its mitigation in the same bullet.>

## Security

## Cost

## Observability

## <Whatever else the design needs>

## Rollout

### Phase 1: <name>

## Open questions

- <Question. When it's resolved, keep it and put the answer under it.>

## References

- <Links to the references page, tickets, and the full design in the repo.>
```

- Use these section names exactly, so every design doc reads the same. Leave out a section that has nothing in it, except Problem, Proposal, and Open questions.
- Security, Cost, and Observability go in that order, when they apply.
- Use diagrams liberally: one in each section that describes components, a flow, a boundary, or phases. Problem can show the current state, Proposal the design, Alternatives each option, and Rollout the phases. Draw them with the **diagram** skill (`agent-tools:diagram`), which also covers embedding.
- No status line, owner, or decision date at the top.

## Troubleshooting

Keep entries inline on the relevant page until there are about 5, then move them to a `Troubleshooting <area>` page.

```markdown
## <Exact error message, or the symptom in the reader's words>

**Cause:** <Why it happens.>

**Fix:** <A command or exact setting, not "check your configuration".>

**Verify:** <How to confirm it's fixed.>
```

- Give each entry bold Cause and Fix labels. (Vale)
- Quote the error verbatim in a code block, with real values.
- Order entries by how often they happen. Put anything that loses data first.
- Make each entry stand alone, because readers land on one entry from search.

## Runbook

Use the how-to outline. Match detail to how often it runs: give rare procedures every step and assume no prior knowledge. Add `lastVerified: <date>` to the frontmatter, and update it when someone runs every step of the procedure.

## PR description

<!-- The sketch, before and after evidence, and door wording come from mattpocock/skills pr (MIT), which credits humanlayer show-me. -->

A PR description is a briefing a reviewer reads in under a minute. Aim for about 150 words of prose, and stay under 200. Code blocks don't count. When the repo has a PR template (`.github/pull_request_template.md`), fill in that template instead, and keep each section to a few lines.

```markdown
<The problem, and why it matters now. One or two sentences.>

<What this change does about it, at the level of behavior. Name the main function, file, or flag.>

<Optional sketch: the smallest view that shows the change. See the list after this outline.>

**Evidence:** <before: the failing test, error, or screenshot. After: the same thing passing.>

**Merge risk:** <low, medium, or high>. <One-way or two-way door>. Blast radius: <one to three words>.
```

- Skip headings in a small PR. Add them only when the PR spans several areas.

- Describe what the change does, not every line it touches. The diff shows the lines.

- Add a sketch only when the change has a shape that prose describes badly. Pick one: pseudocode for logic, a call tree for control flow, a file tree for a layout change, or a Mermaid sequence for interaction between parts. Draw it as a `diff` block when the point is what changed in a shape that already exists:

  ```diff
   submitForm
     createSession
  +    expandSkillMention
       launchAgent
  ```

- Show evidence as before and after. A screenshot is best for a visual change. Test or command output is next best. Name the exact test.

- Take the merge risk line from `agent-tools:review`. A two-way door is undone by reverting the commit. A one-way door, such as dropping data, isn't.

- Don't review the change in its own description. Bugs, missing cleanup, or doubtful defaults you spot in the diff go to the author or into review comments. When you write the description for someone else's change, put those findings after it, clearly outside the description.

- Use the project's domain words from `GLOSSARY.md` when the repo has one.

- Link issues, logs, and benchmarks. Don't paste them.

For reference pages, see [reference.md](reference.md).
