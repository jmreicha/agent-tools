---
type: regex
weight: 2
# Matches the path in a Write or a Bash command, since the skill may build the file with its Python helper.
pattern: '(?:"file_path"|"command"):"(?:[^"\\]|\\.)*docs/architecture/[a-z0-9]+(?:-[a-z0-9]+)*\.drawio'
target: trace
---
