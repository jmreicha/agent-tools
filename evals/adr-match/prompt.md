---
description: A repo with MADR records in docs/decisions. Checks the new ADR follows their numbering, folder, and sections instead of the house template.
tags: [adr]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Record that we're moving background jobs from cron on the app servers to a managed queue (SQS), so jobs survive a server restart and we can retry failures. We looked at keeping cron with a lock file, and at Sidekiq.
