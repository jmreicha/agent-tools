---
type: llm
weight: 2
focus: trace
---

The repo specifies behavior as Gherkin `.feature` files, like `features/login.feature`, with a one-line description under `Feature:` and Given, When, Then steps.

Judge only the new `.feature` file the agent wrote. PASS if it follows that style and has scenarios for: a link that works once, a link that expires after 30 minutes, and the same response whether or not the email has an account. FAIL if a scenario is missing or the file isn't Gherkin.
