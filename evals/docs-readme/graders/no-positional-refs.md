---
type: regex
pattern: "\\b(see|as mentioned|shown|described) (above|below)\\b"
flags: i
match: not_contains
target: { source: file, path: README.md }
---
