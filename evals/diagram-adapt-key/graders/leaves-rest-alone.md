---
type: llm
weight: 2
focus: { source: file, path: orders.drawio }
---

The original diagram had four nodes (Shop, Orders service, Orders DB, Mailer) styled `rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#999999;fontFamily=Verdana;`, three edges between them, and a key with two rows. The light grey label color `#999999` is low contrast, but it's the owner's choice.

PASS if all of these hold:

- The four original nodes keep that exact style, including `fontColor=#999999`, and keep their positions.
- Any new node, such as a batch job or an S3 bucket, uses the same node style as the originals.

FAIL if an original node was recolored, restyled, or moved, or a new node uses a different style.
