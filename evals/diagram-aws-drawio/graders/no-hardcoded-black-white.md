---
type: regex
pattern: "(fillColor|strokeColor|fontColor)=#(000000|1e1e1e|ffffff)"
match: not_contains
flags: i
target: { source: file, path: architecture.drawio }
---
