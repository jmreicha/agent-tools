---
type: regex
weight: 3
# A moved block maps old index 0 to its AZ key, written to a .tf file, so no subnet is destroyed.
pattern: '(?:\.tf","content"|"new_string"):"(?:[^"\\]|\\.)*moved \{(?:[^"\\]|\\.)*private\[0\](?:[^"\\]|\\.)*us-east-1a'
target: trace
---
