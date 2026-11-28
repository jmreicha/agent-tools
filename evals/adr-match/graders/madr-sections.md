---
type: llm
weight: 2
focus: trace
---

The repo's existing decision records use MADR: frontmatter with `status`, `date`, and `deciders`, then the sections "Context and Problem Statement", "Considered Options", "Decision Outcome", and "Consequences" with "Good, because" and "Bad, because" bullets.

Judge only the new record the agent wrote. PASS if it uses the same frontmatter keys and the same section headings, and lists cron with a lock file and Sidekiq as considered options. FAIL if it uses other sections, such as "Alternatives", or drops the frontmatter.
