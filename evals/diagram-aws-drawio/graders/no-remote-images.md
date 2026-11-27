---
type: regex
pattern: "image=https"
match: not_contains
target: { source: file, path: architecture.drawio }
---
