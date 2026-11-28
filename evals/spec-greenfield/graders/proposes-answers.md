---
type: llm
weight: 2
---

The user asked for rate limiting behavior to be pinned down: 100 requests per minute per API key, and a 429 with Retry-After over the limit.

PASS if the reply either shows a written spec, or lists the open decisions (such as how the minute is counted, what counts toward the limit, or what happens with no API key) with a proposed answer for each for the user to correct. FAIL if it only asks open questions with no proposed answers, or lists nothing left to decide.
