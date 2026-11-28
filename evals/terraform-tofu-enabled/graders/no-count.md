---
type: regex
pattern: "count\\s*="
match: not_contains
target: { source: file, path: main.tf }
---
