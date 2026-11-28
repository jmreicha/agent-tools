---
type: regex
weight: 2
# Defaults belong in the variable type, so main.tf reads values directly.
pattern: "lookup\\(|try\\(var\\.|coalesce\\(var\\."
match: not_contains
target: { source: file, path: main.tf }
---
