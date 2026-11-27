---
type: llm
weight: 3
---

The diff makes an HTTP client's Get method retry transport errors and any status of 502 or higher, with exponential backoff, because an upstream gateway drops requests during deploys. Its code comment says 502, 503, and 504, but the check is `StatusCode < 502`, so a description that says "502 or higher" is accurate. It also adds a `maxRetries` field, makes Get use its context, and adds one test.

PASS if all of these hold:

- A reviewer can read it in under a minute: about 200 words of prose or fewer, not counting code blocks.
- It states why the change exists (requests dropped during deploys) before or alongside what changed.
- It mentions the test that covers it.
- It doesn't paste the diff, code listings, or long bullet lists of every line changed.
- It has no filler or hype words, such as "robust", "seamless", or "comprehensive".

FAIL if any of these is missing.
