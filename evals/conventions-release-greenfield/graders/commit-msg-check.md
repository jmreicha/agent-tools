---
type: regex
# The eval sandbox blocks writes to .pre-commit-config.yaml, so grade the attempted write in the trace.
pattern: 'pre-commit-config\.yaml","content":"(?:[^"\\]|\\.)*cog verify(?:[^"\\]|\\.)*commit-msg'
target: trace
---
