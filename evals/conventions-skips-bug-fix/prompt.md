---
description: A code-only bug fix. The conventions skill must not fire.
tags: [conventions, negative]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill]
---

chunk.py drops the last partial chunk when the size doesn't divide evenly. Fix it.
