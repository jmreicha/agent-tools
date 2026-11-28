---
type: regex
# The existing targets are listed in .PHONY and have a ## comment above them.
pattern: '\.PHONY:[^\n]*\blint\b[\s\S]*## [^\n]+\nlint:'
target: { source: file, path: Makefile }
---
