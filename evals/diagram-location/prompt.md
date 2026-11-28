---
description: A repo with existing diagrams in docs/architecture. Checks the new diagram goes next to them, kebab-case, with no Page-1.
tags: [diagram]
max_turns: 40
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Draw how a job moves through our worker system: the API puts it on the jobs queue, a worker picks it up, writes the result to Postgres, and sends a webhook to the customer.
