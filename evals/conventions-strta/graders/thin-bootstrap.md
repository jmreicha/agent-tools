---
type: llm
focus: { source: file, path: script/bootstrap }
---

PASS if `script/bootstrap` starts with a shebang, does one job, and is a few lines that call the real commands (such as pip or pytest) with no application logic. FAIL otherwise.
