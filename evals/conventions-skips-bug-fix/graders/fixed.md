---
type: llm
focus: { source: file, path: chunk.py }
---

PASS if `chunk(list(range(5)), 2)` returns `[[0, 1], [2, 3], [4]]` and `chunk([], 2)` still returns `[]`. FAIL otherwise.
