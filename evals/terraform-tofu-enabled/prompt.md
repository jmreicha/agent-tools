---
description: An OpenTofu 1.11 stack. Checks an on/off resource uses lifecycle enabled, not count.
tags: [terraform]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Make the NAT gateway optional, so dev environments can skip it to save money. Prod keeps it.
