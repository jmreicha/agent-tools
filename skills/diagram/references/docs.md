# Diagrams in docs

## When to suggest one

When editing a doc, suggest a diagram if the text makes the reader hold a picture in their head:

- 3+ connected components
- an order that matters
- a boundary
- a flow already explained in 2+ paragraphs

Skip it for a single component, a list the text already covers, or anything that changes faster than anyone updates a picture.
Suggest first, and draw only on a yes. Place one diagram per section, under the paragraph that introduces it.

## Embedding

- **Repo markdown:** run `drawio -x -e -f svg -o name.drawio.svg name.drawio`, then reference it with `![<one sentence on what it shows>](name.drawio.svg)`. GitHub renders it, and draw.io still edits it.
- **Confluence (draw.io app):** uploading a new attachment version does not update the page, because each macro is pinned to its `revision`/`contentVer`. Repoint it: open the diagram in the editor and save, or update those params through the API. Then confirm the page shows the new version.
- **Two-page files:** embed the Brief page (`-p 1` on export, or the page picker in the Confluence macro) and link to the `.drawio` file for Full.
- **Anything else:** export a PNG or SVG.
- **Always:** add a one line caption, plus alt text wherever the format supports it.
