---
type: llm
focus: { source: file, path: script/test }
---

PASS if `script/test` starts with a shebang, does one job, and is a few lines that call the real commands (such as pip or pytest) with no application logic. FAIL otherwise.
