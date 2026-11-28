---
description: Extend someone else's diagram with a nightly export. Checks Adapt mode keeps every line in the key, leaves the rest alone, and reports existing problems instead of fixing them.
tags: [diagram]
max_turns: 40
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Add the nightly export to orders.drawio: a batch job copies the orders database to an S3 bucket once a night.
