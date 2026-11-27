---
type: llm
weight: 2
focus: trace
---

The repo already runs its tests with `scripts/test.sh`.

PASS if the agent wrote a GitHub Actions workflow that runs the tests and the lint through scripts in `scripts/`, such as `scripts/test.sh` and `scripts/lint.sh`, and the workflow doesn't call pytest or the linter directly. FAIL if the workflow inlines either command or bypasses the scripts.
