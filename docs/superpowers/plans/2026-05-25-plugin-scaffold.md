# Plugin Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold `agent-tools` as a Claude Code plugin with a `skills/` directory and valid plugin manifest.

**Architecture:** Add `.claude-plugin/plugin.json` at the repo root to declare plugin identity, create an empty `skills/` directory for future skill additions, and update `README.md` with plugin usage instructions.

**Tech Stack:** Claude Code plugin format (plain directories + Markdown + JSON)

---

### Task 1: Create plugin manifest

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Create the `.claude-plugin` directory and `plugin.json`**

```bash
mkdir -p .claude-plugin
```

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "agent-tools",
  "description": "Curated collection of tools and configurations for AI coding agents",
  "version": "1.0.0",
  "author": {
    "name": "Josh Reichardt"
  }
}
```

- [ ] **Step 2: Verify the file exists and is valid JSON**

```bash
cat .claude-plugin/plugin.json | python3 -m json.tool
```

Expected: prints the formatted JSON with no errors.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add Claude Code plugin manifest"
```

---

### Task 2: Create skills directory

**Files:**
- Create: `skills/.gitkeep`

- [ ] **Step 1: Create the `skills/` directory with a placeholder**

```bash
mkdir -p skills && touch skills/.gitkeep
```

- [ ] **Step 2: Verify the directory is tracked**

```bash
git status skills/
```

Expected: `skills/.gitkeep` listed as an untracked file.

- [ ] **Step 3: Commit**

```bash
git add skills/.gitkeep
git commit -m "feat: add skills directory for future skill definitions"
```

---

### Task 3: Update README with plugin usage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace `README.md` content**

```markdown
# agent-tools

Curated collection of tools and configurations for AI coding agents.

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

To add a skill:

```bash
mkdir -p skills/my-skill
# create skills/my-skill/SKILL.md with YAML frontmatter + instructions
```

Run `/reload-plugins` inside Claude Code to pick up new skills.
```

- [ ] **Step 2: Verify the file looks correct**

```bash
cat README.md
```

Expected: shows the updated content with plugin usage section.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README with plugin usage instructions"
```
