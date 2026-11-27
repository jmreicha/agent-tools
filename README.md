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

| Skill       | Invocation                 | Description                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ----------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| diagram     | `/agent-tools:diagram`     | Use when asked to draw, diagram, sketch, or visualize architecture, infrastructure, network/traffic paths, request flows, or systems as a draw.io (.drawio), Excalidraw, or Mermaid diagram, to export a diagram to PNG/SVG/PDF, or when an existing doc would read better with a diagram.                                                                                                                                                        |
| docs        | `/agent-tools:docs`        | Technical-writing standard for engineers, with Diátaxis page types, Google developer style, STE and Global English rules, and lint checks for Markdown and prose. Use whenever writing, editing, or reviewing prose for engineers, such as READMEs, docs pages and sites, tutorials, how-tos, reference, troubleshooting, runbooks, ADRs, RFCs, design docs, changelogs, PR descriptions, commit messages, issue bodies, or code comments.        |
| learn       | `/agent-tools:learn`       | Turn mistakes and corrections into lasting changes. Reflect mines the session transcript for lessons and routes each one to a skill, a `CLAUDE.md` rule, or memory. Correct finds mistakes agents repeat in a repo and makes them impossible with architecture, types, lints, or tests. Use for /learn, "reflect", "what did we learn", "make sure this never happens again", or when the user corrects the same mistake twice.                   |
| optimize    | `/agent-tools:optimize`    | Use when code or infrastructure is slow and needs a performance fix. Measure first, find the bottleneck, change it, and measure again. Triggers on "/optimize", "make this faster", or "performance".                                                                                                                                                                                                                                             |
| planning    | `/agent-tools:planning`    | Manage issues, milestones, and project tracking via GitHub CLI. Use when triaging bugs, planning sprints, updating issue status, or reporting on project progress.                                                                                                                                                                                                                                                                                |
| pr          | `/agent-tools:pr`          | Iterate on a PR until CI passes. Use when you need to fix CI failures, resolve review feedback, or continuously push fixes until all checks are green. Automates the feedback-fix-push-wait cycle.                                                                                                                                                                                                                                                |
| research    | `/agent-tools:research`    | Gather context before building, from current library docs and source (context7), real code on GitHub, and the web, then recommend one approach. Use when about to implement a feature, adopt or upgrade a library, choose between approaches or technologies, or see how other projects solved a similar problem.                                                                                                                                 |
| review      | `/agent-tools:review`      | Performs structured code reviews that check correctness, security, style, and test coverage. Use when reviewing PRs, auditing unfamiliar code, or verifying a change before merge.                                                                                                                                                                                                                                                                |
| rubber-duck | `/agent-tools:rubber-duck` | Use when thinking through system design, architecture, API shape, data modeling, or any design decision before building. A conversational thinking partner that asks questions and offers perspectives, and doesn't write code or make changes.                                                                                                                                                                                                   |
| sdlc        | `/agent-tools:sdlc`        | Entry point for software work. Sets a measurable goal with done checks, finds the lifecycle stage (design, spec, test, implement, security review, observe, refactor, docs, ship, learn), and routes to the matching agent-tools skill and any domain skill, such as Terraform. Use when starting any coding, infrastructure, or docs task, when asked "where do I start", "set a goal", or "what does done look like", or when invoked as /sdlc. |
| terraform   | `/agent-tools:terraform`   | Use when working with Terraform or OpenTofu - creating modules, writing tests (native test framework), reviewing configurations, choosing between testing approaches, debugging state issues, implementing security scanning (trivy, checkov), or making infrastructure-as-code architecture decisions                                                                                                                                            |
| testing     | `/agent-tools:testing`     | Test first development that picks TDD or BDD for each change and runs a fast red, green, refactor loop. Use when adding a feature, fixing a bug or regression, changing behavior, refactoring, adding tests to untested code, or when the user mentions TDD, BDD, a failing test, a regression test, or Given-When-Then.                                                                                                                          |

<!-- skills-table-end -->

<!-- skills-details-start -->

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

### `research`

**Invocation:** `/agent-tools:research`

Find out how the library and other projects actually work before you build, so the plan rests on facts instead of memory.

---

### `review`

**Invocation:** `/agent-tools:review`

_No documentation yet._

---

### `rubber-duck`

**Invocation:** `/agent-tools:rubber-duck`

A Socratic thinking partner for design decisions, adapted from [rubber duck debugging](https://rubberduckdebugging.com/). Rubber duck debugging works because explaining your code line by line to a duck exposes the assumptions you didn't know you made. This skill does the same for design. The person explains their system, their constraints, and their half formed architecture, and gets nudges that show what they're missing before they build the wrong thing.

---

### `sdlc`

**Invocation:** `/agent-tools:sdlc`

Set the goal, find the stage, and hand off to the skill that owns it. Every skill below also works on its own.

---

### `terraform`

**Invocation:** `/agent-tools:terraform`

Write, test, and review Terraform and OpenTofu code that holds up in production. The rules come from [terraform-best-practices.com](https://www.terraform-best-practices.com/) and from running Terraform at work, so each one has a reason behind it.

**When to use:**

- Creating new Terraform or OpenTofu configurations or modules
- Setting up testing infrastructure for IaC code
- Deciding between testing approaches (validate, plan, frameworks)
- Structuring multi environment deployments
- Reviewing or refactoring existing Terraform/OpenTofu projects
- Choosing between module patterns or state management approaches

Don't use this skill for:

- Basic Terraform or OpenTofu syntax. You already know it.
- Provider API reference. Link the provider docs instead.
- Cloud platform questions unrelated to Terraform/OpenTofu

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
