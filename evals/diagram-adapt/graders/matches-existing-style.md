---
type: llm
weight: 3
focus: { source: file, path: app.drawio }
---

The original diagram had Web, API, and Postgres nodes styled with `fillColor=#dae8fc;strokeColor=#6c8ebf;fontFamily=Helvetica;`, connected by curved edges with `endArrow=block`.

PASS if all of these hold:

- A Redis node exists in the same fill, stroke, and font as its siblings.
- A new edge connects API to Redis, styled like the existing edges (curved, `endArrow=block`, the same stroke color).
- Web, API, Postgres, and the two original edges keep their original style. Nothing was recolored or restyled.

FAIL if any of these is wrong.
