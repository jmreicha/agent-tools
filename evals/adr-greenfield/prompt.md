---
description: A repo with no ADRs. Checks a first ADR lands in docs/adrs with adrs.toml, and records the rejected option and the downsides.
tags: [adr]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

We're going with Postgres instead of DynamoDB for the orders service, because reporting needs joins across orders, customers, and refunds, and we'd end up duplicating data in Dynamo to fake them. The catch is we now have to run schema migrations and size the instance ourselves. Write this decision down so people know why later.
