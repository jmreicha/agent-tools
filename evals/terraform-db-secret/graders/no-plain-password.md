---
type: regex
weight: 2
# A plain password argument or a random_password resource stores the secret in state.
pattern: '(?:\.tf","content"|"new_string"):"(?:[^"\\]|\\.)*(?:\bpassword\s*=|resource \\"random_password\\")'
match: not_contains
target: trace
---
