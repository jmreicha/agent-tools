---
description: A module that takes loose settings. Checks new settings become an object variable with optional() defaults, read directly in main.tf.
tags: [terraform]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Let callers of this module turn on access logging for the bucket, with a log prefix and how many days to keep the logs. Logging should default to off.
