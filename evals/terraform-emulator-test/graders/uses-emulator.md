---
type: regex
weight: 3
# Anchored to a write, such as a test script, because the skill's own docs show the same endpoint.
pattern: '(?:","content"|"new_string"):"(?:[^"\\]|\\.)*AWS_ENDPOINT_URL=\S*127\.0\.0\.1:9297'
target: trace
---
