---
type: regex
pattern: "\\b(simply|easily|seamless(ly)?|robust|utilize|powerful|effortless(ly)?)\\b"
flags: i
match: not_contains
target: { source: file, path: README.md }
---
