---
type: regex
# A splat on a for_each resource fails, so the output must switch to values() or a for expression.
pattern: 'aws_subnet\.private\[\*\]'
match: not_contains
target: { source: file, path: outputs.tf }
---
