---
type: regex
# file_exists globs skip dotfiles, so check the trace for a write to a semantic-release config.
pattern: '"file_path":"[^"]*(\.releaserc|release\.config\.)'
match: not_contains
target: trace
---
