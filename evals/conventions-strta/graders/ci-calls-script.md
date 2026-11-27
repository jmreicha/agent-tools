---
type: llm
weight: 2
focus: trace
---

PASS if the agent wrote a GitHub Actions workflow under `.github/workflows/` whose test step runs `script/cibuild` or `script/test`, and the workflow doesn't call pytest directly. FAIL if there's no workflow, or the workflow runs pytest itself.
