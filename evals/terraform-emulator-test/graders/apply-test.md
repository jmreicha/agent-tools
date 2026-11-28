---
type: regex
weight: 2
# Anchored to a write (Write, Edit, or a Bash heredoc), because the skill's own docs also contain this text.
pattern: '(?:\.tftest\.hcl","content"|"new_string"|"command"):"(?:[^"\\]|\\.)*(?:\.tftest\.hcl(?:[^"\\]|\\.)*)?command\s*=\s*apply'
target: trace
---
