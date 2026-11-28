# `agent-tools`

A curated collection of my various tools and configurations for AI coding agents.

## Plugin usage

This repo is a [Claude Code plugin](https://code.claude.com/docs/en/plugins).

### Test locally

```bash
claude --plugin-dir ./
```

### Install

```bash
claude plugin marketplace add jmreicha/agent-tools
claude plugin install agent-tools@agent-tools
```

## Skills

Skills live in `skills/<skill-name>/SKILL.md` and are invoked as `/agent-tools:<skill-name>`.

<!-- skills-table-start -->

| Skill       | Invocation                 | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| adr         | `/agent-tools:adr`         | Record architecture decisions as ADRs. Matches the repo's existing ADR folder, format, and numbering first, and otherwise sets up the adrs CLI with the house template (status, context, decision, alternatives, consequences) in docs/adrs. Use when making or recording a decision that is hard to reverse or that others may later ask "why" about, when superseding or changing the status of an ADR, or when the user mentions an ADR, a decision record, or adrs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| conventions | `/agent-tools:conventions` | Where code lives and how the repo runs it. Matches the repo's existing dirs and entry points first. It introduces no Makefile, Taskfile, justfile, or other build system, and otherwise sets up the house defaults, which are language-idiomatic code paths, a canonical script/ dir of thin shell scripts with one verb per task (bootstrap, setup, test, server, cibuild), a docs/ tree with one home per document, tool versions pinned in mise.toml, a pre-commit gate, CI pipelines that call script/cibuild, and Conventional Commits with semver releases cut by cocogitto. Use when deciding where a new file, module, or script goes, adding build, run, test, or lint entry points, setting up a new repo, adopting mise, pre-commit, or Renovate, adding or editing CI pipelines, writing commit messages, or setting up versioning, changelogs, or releases, or when the user asks "where does this go" or mentions scripts to rule them all. |
| diagram     | `/agent-tools:diagram`     | Use whenever the answer includes any diagram, including a short Mermaid flowchart or sequence diagram for a README or chat reply. Covers drawing, sketching, or visualizing architecture, infrastructure, network and traffic paths, request flows, pipelines, and systems as draw.io (.drawio), Excalidraw, or Mermaid, exporting a diagram to PNG, SVG, or PDF, and spotting when an existing doc would read better with a diagram.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| docs        | `/agent-tools:docs`        | Technical-writing standard for engineers, with Diátaxis page types, Google developer style, STE and Global English rules, and lint checks for Markdown and prose. Use whenever writing, editing, or reviewing prose for engineers, such as READMEs, docs pages and sites, tutorials, how-tos, reference, troubleshooting, runbooks, ADRs, RFCs, design docs, changelogs, PR descriptions, commit messages, issue bodies, or code comments.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| learn       | `/agent-tools:learn`       | Turn mistakes and corrections into lasting changes. Reflect mines the session transcript for lessons and routes each one to a skill, a `CLAUDE.md` rule, or memory. Correct finds mistakes agents repeat in a repo and makes them impossible with architecture, types, lints, or tests. Use for /learn, "reflect", "what did we learn", "make sure this never happens again", or when the user corrects the same mistake twice.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| optimize    | `/agent-tools:optimize`    | Use when code or infrastructure is slow and needs a performance fix. Measure first, find the bottleneck, change it, and measure again. Triggers on "/optimize", "make this faster", or "performance".                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| planning    | `/agent-tools:planning`    | Manage issues, milestones, and project tracking via GitHub CLI. Use when triaging bugs, planning sprints, updating issue status, or reporting on project progress.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| pr          | `/agent-tools:pr`          | Iterate on a PR until CI passes. Use when you need to fix CI failures, resolve review feedback, or continuously push fixes until all checks are green. Automates the feedback-fix-push-wait cycle.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| refactor    | `/agent-tools:refactor`    | Change the structure of code without changing its behavior. Pins current behavior with tests first, deletes before it adds, moves in small steps that keep the tests green, and reports any bug it finds instead of fixing it. Use when asked to refactor, clean up, restructure, simplify, deduplicate, extract, split, rename, or reorganize code, or to remove duplication or dead code.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| research    | `/agent-tools:research`    | Gather context before building, from current library docs and source (context7), real code on GitHub, and the web, then recommend one approach. Use when about to implement a feature, adopt or upgrade a library, choose between approaches or technologies, or see how other projects solved a similar problem.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| review      | `/agent-tools:review`      | Review a change before merge. Finds bugs and security issues that a run can prove, then grades merge risk (low, medium, or high) on alignment, impact, verification, rollback cost, and error detection. Use when reviewing a PR, a branch, or a diff, when asked whether a change is safe or ready to merge or ship, or before opening or merging a PR.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| rubber-duck | `/agent-tools:rubber-duck` | Use when thinking through system design, architecture, API shape, data modeling, or any design decision before building. A conversational thinking partner that asks questions and offers perspectives, and doesn't write code or make changes.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| sdlc        | `/agent-tools:sdlc`        | Entry point for software work. Sets a measurable goal with done checks, finds the lifecycle stage (design, spec, test, implement, security review, observe, refactor, docs, ship, learn), and routes to the matching agent-tools skill and any domain skill, such as Terraform. Use when starting any coding, infrastructure, or docs task, when asked "where do I start", "set a goal", or "what does done look like", or when invoked as /sdlc.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| spec        | `/agent-tools:spec`        | Write, change, and implement behavior specs that drive tests and code. Matches the repo's existing spec format first (yass, Spec Kit, OpenSpec, Kiro, Gherkin, or a PRD folder), and otherwise uses yass. Use when starting a new feature or project that needs its behavior pinned down, when writing or changing a spec, acceptance criteria, or requirements, when implementing against an existing spec, or when the user mentions a spec, yass, or a .yass.yaml file.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| terraform   | `/agent-tools:terraform`   | House standard for Terraform, OpenTofu, and Terragrunt, built around the ways IaC changes go wrong in production, such as recreated resources, secrets in state, oversize blast radius, and unreviewed applies. Matches the repo's existing layout, tool, and module style first. Use whenever writing, changing, reviewing, refactoring, testing, or debugging .tf, .tftest.hcl, Terragrunt files (terragrunt.hcl, root.hcl), creating modules, moving resources between addresses or state, upgrading providers, or setting up IaC checks and pipelines.                                                                                                                                                                                                                                                                                                                                                                                                |
| testing     | `/agent-tools:testing`     | Test first development that picks TDD or BDD for each change and runs a fast red, green, refactor loop. Use when adding a feature, fixing a bug or regression, changing behavior, refactoring, adding tests to untested code, or when the user mentions TDD, BDD, a failing test, a regression test, or Given-When-Then.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

<!-- skills-table-end -->

<!-- skills-details-start -->

### `adr`

**Invocation:** `/agent-tools:adr`

Record one decision and why we made it, so the next person doesn't relitigate it.

Write an ADR for a decision that's hard to reverse, crosses more than one component or team, or that someone may ask "why" about later. Don't write one for a routine choice. For how we plan to build something, write a design doc with `agent-tools:docs` instead.

---

### `conventions`

**Invocation:** `/agent-tools:conventions`

Where code lives and how the repo runs it: the canonical dirs, the `script/` shell scripts that run everything, the `docs/` tree, tool versions, the local gate, dependency updates, and the CI pipelines that call the scripts.

Placement that follows convention is not a design decision. When something already has a home, put it there and move on. Think through a genuinely new shape with `agent-tools:rubber-duck`, and record a decision that is hard to reverse with `agent-tools:adr`.

This skill owns placement, not content. Prose rules belong to `agent-tools:docs`, behavior contracts to `agent-tools:spec`, and test method to `agent-tools:testing`.

---

### `diagram`

**Invocation:** `/agent-tools:diagram`

Plain black and white boxes, right-angle arrows, real vendor icons, and terse free floating text.
The look stays close to draw.io defaults. Color is for vendor icons and the occasional emphasis.

---

### `docs`

**Invocation:** `/agent-tools:docs`

<!-- Forked from cursor/plugins pstack/skills/technical-writing (MIT, (c) 2026 Lauren Tan). -->

Write so a tired engineer understands on the first read.

- Cut every word that does no work.
- Use the short, everyday word: "use", not "utilize".
- When a rule makes a sentence worse, fix the sentence another way or leave it alone.
- Write the real symbol, file, flag, or command name, not a synonym or a description of it.
- Don't invent jargon. Use the words a developer would say out loud. Say what a named pattern means the first time.

Read [references/voice.md](skills/docs/references/voice.md) first, and write in that voice from the first draft. It's the author's own voice, and it overrides the rules below where they conflict. The rules and linters come after.

---

### `learn`

**Invocation:** `/agent-tools:learn`

Change something durable so the next agent doesn't repeat the mistake. A lesson that only lives in chat is lost at the end of the session.

Run **reflect** by default. Run **correct** when the user asks for it, or when reflect finds a mistake that has happened at least twice.

---

### `optimize`

**Invocation:** `/agent-tools:optimize`

Improve performance with evidence, not guesses.

<!-- TODO: flesh out the workflow. -->

---

### `planning`

**Invocation:** `/agent-tools:planning`

_No documentation yet._

---

### `pr`

**Invocation:** `/agent-tools:pr`

Keep fixing and pushing the current branch until every CI check passes and the review feedback is resolved.

This skill needs the GitHub CLI (`gh`), signed in.

---

### `refactor`

**Invocation:** `/agent-tools:refactor`

<!-- Adapted from cursor/plugins pstack refactoring playbook (MIT) and marekkirejczyk/skills refactor-tests (MIT). -->

The structure changes. The behavior doesn't. Every caller sees the same results, errors, writes, and calls as before.

A refactor that adds a feature or fixes a bug is two changes. Do the refactor first, against today's behavior, and ship the feature or fix after it with `agent-tools:testing`.

---

### `research`

**Invocation:** `/agent-tools:research`

Find out how the library and other projects actually work before you build, so the plan rests on facts instead of memory.

---

### `review`

**Invocation:** `/agent-tools:review`

<!-- Merge risk grading adapted from warpdotdev/common-skills merge-risk (MIT), which credits mattpocock/skills pr. -->

Tell the author what could break and how risky the merge is, with evidence. Report what you find. Don't fix it unless the user asks.

---

### `rubber-duck`

**Invocation:** `/agent-tools:rubber-duck`

A Socratic thinking partner for design decisions, adapted from [rubber duck debugging](https://rubberduckdebugging.com/). Rubber duck debugging works because explaining your code line by line to a duck exposes the assumptions you didn't know you made. This skill does the same for design. The person explains their system, their constraints, and their half formed architecture, and gets nudges that show what they're missing before they build the wrong thing.

---

### `sdlc`

**Invocation:** `/agent-tools:sdlc`

Set the goal, find the stage, and hand off to the skill that owns it. Every skill below also works on its own.

---

### `spec`

**Invocation:** `/agent-tools:spec`

A spec says what the system must do, as checks that code and tests can be held to. It's the contract: the user approves it before anyone builds, and when the code comes out wrong, the fix usually starts with a line in the spec.

A spec isn't a decision record or a build plan. Record a decision with `agent-tools:adr`. Explain how we plan to build something in a design doc with `agent-tools:docs`.

---

### `terraform`

**Invocation:** `/agent-tools:terraform`

Write infrastructure code whose plan a reviewer can trust. The costly Terraform bugs are changes that look small in the diff and destroy, expose, or drift something in the plan. Every rule here guards against one of them.

The rules cover Terraform and OpenTofu alike. Where they differ, use the repo's binary: `terraform` or `tofu`.

---

### `testing`

**Invocation:** `/agent-tools:testing`

Pick test driven development (TDD) or behavior driven development (BDD) for each change, and switch between them as the work moves.

Use TDD to design and verify internal behavior with fast feedback. Use BDD to define what users see: workflows and acceptance criteria. Choose by scope, not preference. Most features end up using both: BDD for the outside, TDD for the parts.

<!-- skills-details-end -->

To add a skill:

```bash
mkdir -p skills/my-skill
# create skills/my-skill/SKILL.md with YAML frontmatter + instructions
```

Run `/reload-plugins` inside Claude Code to pick up new skills.

## `arbiter`

A mod that turns the "always/never" lines in `CLAUDE.md` into rules Claude Code enforces at every
tool call: deny with a hint, ask first, or warn. Rules are YAML with inline tests, layered across
plugin, user, and project folders.

- [Guide](hooks/arbiter/README.md): what it is, why you'd use it, quick start, and recipes.
- [Examples](hooks/arbiter/examples/rules.yaml): commented, tested rules to copy from.
- [Rule reference](docs/arbiter/reference.md): every field, matcher, and command.

Requires Claude Code ≥ 2.1.287. Run `/arbiter init` in a session to get started.

## LSP servers

`.lsp.json` connects language servers for the languages Anthropic's official LSP plugins don't
cover. Claude gets diagnostics after each edit and an `LSP` tool for definitions and references.

| Server                 | Files            | Install the binary                               |
| ---------------------- | ---------------- | ------------------------------------------------ |
| `bash-language-server` | `.sh`, `.bash`   | `npm i -g bash-language-server` (+ `shellcheck`) |
| `yaml-language-server` | `.yaml`, `.yml`  | `npm i -g yaml-language-server`                  |
| `terraform-ls`         | `.tf`, `.tfvars` | `mise use -g aqua:hashicorp/terraform-ls`        |
| `docker-langserver`    | `.dockerfile`    | `npm i -g dockerfile-language-server-nodejs`     |

The plugin doesn't include the servers. Each binary must be on the `PATH` of the shell you start
`claude` from. A missing one shows up in the `/plugin` **Errors** tab, and the other servers
still work.

- `.zsh` isn't mapped, because shellcheck doesn't support zsh and reports false errors.
- YAML uses SchemaStore schemas (GitHub Actions, compose and so on). Kubernetes schemas apply to
  files under `k8s/`, `manifests/` or `kubernetes/` directories. Edit `settings` in `.lsp.json`
  to change that.
- Claude Code matches files by extension only, so a plain `Dockerfile` (no extension) isn't
  covered. Only names like `app.dockerfile` are.
- `terraform-ls` doesn't understand `terragrunt.hcl`.
