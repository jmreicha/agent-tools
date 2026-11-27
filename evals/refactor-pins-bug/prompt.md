---
description: A refactor that uncovers an inconsistency. The behavior must stay, the bug gets pinned and reported, not silently fixed.
tags: [refactor]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Skill]
---

The discount logic in pricing.py is copy-pasted three times. Clean it up.
