# agent-tools

A curated collection of my various tools and configurations for AI coding agents.

## Plugin Usage

This repo is a [Claude Code plugin](https://code.claude.com/docs/en/plugins).

### Test locally

```bash
claude --plugin-dir ./
```

### Install from a marketplace

```
/plugin install agent-tools@<marketplace>
```

## Skills

Skills live in `skills/<skill-name>/SKILL.md` and are invoked as `/agent-tools:<skill-name>`.

<!-- skills-table-start -->

| Skill              | Invocation                        | Description                                                                                                                                                                                                                                                                                                                                              |
| ------------------ | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| documentation      | `/agent-tools:documentation`      | Generate and maintain project documentation — READMEs, API docs, changelogs, and inline comments. Use when adding new features, onboarding to an unfamiliar codebase, or ensuring docs stay in sync with code.                                                                                                                                           |
| findings           | `/agent-tools:findings`           | Maintain a per-repo finding file that tracks mistakes, corrections, and what works. Activates EVERY session, unconditionally. Read the finding before doing anything. Write to it continuously as you work — not just at session boundaries. Log your own mistakes, not just user corrections. The finding lives in the repo at `./context/findings.md`. |
| pr                 | `/agent-tools:pr`                 | Iterate on a PR until CI passes. Use when you need to fix CI failures, address review feedback, or continuously push fixes until all checks are green. Automates the feedback-fix-push-wait cycle.                                                                                                                                                       |
| project-management | `/agent-tools:project-management` | Manage issues, milestones, and project tracking via GitHub CLI. Use when triaging bugs, planning sprints, updating issue status, or reporting on project progress.                                                                                                                                                                                       |
| research           | `/agent-tools:research`           | Use before implementing new features to gather context from documentation, real-world code examples, and web resources. Provides structured findings to inform implementation decisions.                                                                                                                                                                 |
| review             | `/agent-tools:review`             | Perform structured code reviews — check correctness, security, style, and test coverage. Use when reviewing PRs, auditing unfamiliar code, or verifying a change before merge.                                                                                                                                                                           |
| terraform-skill    | `/agent-tools:terraform`          | Use when working with Terraform or OpenTofu - creating modules, writing tests (native test framework), reviewing configurations, choosing between testing approaches, debugging state issues, implementing security scanning (trivy, checkov), or making infrastructure-as-code architecture decisions                                                   |
| testing            | `/agent-tools:testing`            | Use to choose and apply TDD or BDD based on the change, enforcing fast Red-Green-Refactor and Given-When-Then loops.                                                                                                                                                                                                                                     |

<!-- skills-table-end -->

<!-- skills-details-start -->

### documentation

**Invocation:** `/agent-tools:documentation`

_No documentation yet._

---

### findings

**Invocation:** `/agent-tools:findings`

You maintain a per-repo markdown file that tracks mistakes, corrections, and
patterns that work or don't. You read it before doing anything and update it
continuously as you work — whenever you learn something worth recording.

**This skill is always active. Every session. No trigger required.**

---

### pr

**Invocation:** `/agent-tools:pr`

Continuously iterate on the current branch until all CI checks pass and review feedback is addressed.

**Requires**: GitHub CLI (`gh`) authenticated.

---

### project-management

**Invocation:** `/agent-tools:project-management`

_No documentation yet._

---

### research

**Invocation:** `/agent-tools:research`

This skill provides systematic multi-source research for gathering context before implementing new functionality.

**When to use:**

Use this skill when:

- Planning or immplementing new features (try to use whenever possible)
- Working with unfamiliar libraries or frameworks
- Evaluating architectural approaches or design patterns
- Understanding how others solved similar problems
- Making technology selection decisions

---

### review

**Invocation:** `/agent-tools:review`

_No documentation yet._

---

### terraform-skill

**Invocation:** `/agent-tools:terraform`

Comprehensive Terraform and OpenTofu guidance covering testing, modules, and production patterns. Based on terraform-best-practices.com and enterprise experience.

**When to use:**

**Activate this skill when:**

- Creating new Terraform or OpenTofu configurations or modules
- Setting up testing infrastructure for IaC code
- Deciding between testing approaches (validate, plan, frameworks)
- Structuring multi-environment deployments
- Reviewing or refactoring existing Terraform/OpenTofu projects
- Choosing between module patterns or state management approaches

**Don't use this skill for:**

- Basic Terraform/OpenTofu syntax questions (Claude knows this)
- Provider-specific API reference (link to docs instead)
- Cloud platform questions unrelated to Terraform/OpenTofu

---

### testing

**Invocation:** `/agent-tools:testing`

This skill guides when and how to use Test Driven Development (TDD) and Behavior Driven Development (BDD), and how to switch between them while iterating quickly.

**When to use:**

Use this skill when:

- Adding new features, flows, or APIs
- Fixing bugs or regressions
- Refactoring behavior or changing requirements
- Adding tests to untested code

<!-- skills-details-end -->

To add a skill:

```bash
mkdir -p skills/my-skill
# create skills/my-skill/SKILL.md with YAML frontmatter + instructions
```

Run `/reload-plugins` inside Claude Code to pick up new skills.
