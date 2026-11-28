---
description: A deployed module that uses count over AZs. Checks the switch to for_each keeps every subnet with moved blocks and no state commands.
tags: [terraform]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

This module is deployed in prod. Switch the private subnets to for_each, so taking an AZ out later doesn't recreate the other subnets.
