---
description: A repo with no specs. Checks the skill starts the yass process with proposed answers, and builds nothing before the user approves.
tags: [spec]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

We're adding rate limiting to the public API: 100 requests per minute per API key, and a 429 with a Retry-After header when a key goes over. Pin down exactly how it should behave before anyone builds it.
