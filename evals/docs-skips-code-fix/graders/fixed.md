---
type: llm
focus: { source: file, path: paginate.py }
---

PASS if `pages(list(range(5)), 2)` would return three pages, `[[0, 1], [2, 3], [4]]`, and an empty list still returns no pages. FAIL otherwise.
