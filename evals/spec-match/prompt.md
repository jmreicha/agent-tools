---
description: A repo with Gherkin features. Checks the new behavior is specified as a .feature file in the existing style, with no yass files.
tags: [spec]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Spec out password reset before we build it: a user asks for a reset link by email, the link works once and expires after 30 minutes, and we don't reveal whether an email has an account.
