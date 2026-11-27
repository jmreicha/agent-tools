---
type: regex
pattern: '"branches"'
match: contains
target: { source: file, path: .releaserc.json }
---
