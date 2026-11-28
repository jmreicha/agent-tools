---
type: llm
weight: 2
---

The repo runs everything through Makefile targets, and the agent added a lint step.

PASS if the reply offers, once, to move the Makefile targets into standalone scripts (such as a `script/` folder of shell scripts), as a question for the user, and says it didn't make that move. FAIL if it makes no such offer, or says it already moved them.
