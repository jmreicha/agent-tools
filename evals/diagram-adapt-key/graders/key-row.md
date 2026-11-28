---
type: llm
weight: 3
focus: { source: file, path: orders.drawio }
---

The original key had a title "Key" and two rows. Each row was a short sample line followed by a label in `fontFamily=Verdana;fontSize=10;fontColor=#999999;`: "Request" for a solid line with `endArrow=classic`, and "Event" for a dashed line with `endArrow=open`.

PASS if every connection line for the nightly export either:

- reuses the Request or Event style exactly, so the existing key already explains it, or
- uses a new style that has its own key row in the same format: a short sample line in that style, and a Verdana 10 `#999999` label naming it.

FAIL if any export line uses a style the key doesn't show, or a new key row breaks the existing format.
