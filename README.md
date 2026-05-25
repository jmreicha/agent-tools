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
