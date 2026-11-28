---
description: A stack that needs a database. Checks the master password stays out of Terraform state and the instance is locked down.
tags: [terraform]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Add a Postgres RDS instance for the orders service to this stack.
