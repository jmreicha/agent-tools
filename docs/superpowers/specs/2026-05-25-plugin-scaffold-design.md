# agent-tools Plugin Scaffold Design

## Overview

Scaffold the `agent-tools` repo as a Claude Code plugin following the official plugin structure.

## Structure

```
agent-tools/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── .gitkeep
└── README.md  (updated with plugin usage)
```

## plugin.json

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

## Usage

Skills are added under `skills/<skill-name>/SKILL.md` and invoked as `/agent-tools:<skill-name>`.

Test locally with:

```bash
claude --plugin-dir ./
```
