# Excalidraw and Mermaid

Both follow the same visual rules as draw.io: black strokes, no fills, terse labels, left-to-right flow,
dashed boundaries only for logical constructs.

## Excalidraw (only on request)

Write `<name>.excalidraw` wherever a `.drawio` file would go.
- **File:** `{"type":"excalidraw","version":2,"source":"https://excalidraw.com","elements":[...],"appState":{"viewBackgroundColor":"#ffffff","gridSize":20},"files":{}}`
- **Every element:** `id, type, x, y, width, height, angle:0, opacity:100, seed, version:1, versionNonce, isDeleted:false, groupIds:[], frameId:null, link:null, locked:false, updated:1, boundElements`.
- **Shapes:** `"strokeColor":"#1e1e1e","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":2,"roughness":1,"roundness":{"type":3}` at 160×80. A boundary adds `"strokeStyle":"dashed"`.
- **Text:**
  - Set `"fontFamily":5` at size 20, plus `text, originalText, fontSize, lineHeight:1.25, textAlign:"center", verticalAlign:"middle", autoResize:true`.
  - A label inside a shape sets `"containerId":"<shape id>"`, and the shape lists `{"type":"text","id":"<text id>"}` in its `boundElements`.
- **Arrows:**
  - Set `points:[[0,0],[dx,dy]]`, `startArrowhead:null`, and `"startBinding"`/`"endBinding"` of `{"elementId":"<id>","focus":0,"gap":4}`.
  - Each bound shape lists `{"type":"arrow","id":"<arrow id>"}`.
  - A note link adds `"strokeStyle":"dotted","endArrowhead":null`.
- **Logos:**
  - Add an element `{"type":"image","fileId":"<id>","status":"saved","scale":[1,1]}`, plus `"files":{"<id>":{"id":"<id>","mimeType":"image/svg+xml","dataURL":"<logo url>","created":1}}`.
  - Then run `scripts/embed-icons.py`, which also fixes SVG sizing.
- **Render:** `excalidraw render <name>.excalidraw --out /tmp/<name>.png --scale 2`, then Read the PNG. If the CLI is missing, install it with `npm i -g excalidraw-cli`.

## Mermaid (simple diagrams in repo markdown)

Use it for a flowchart or sequence diagram with about 8 nodes or fewer, no icons, no boundaries, and no emphasis. Anything more uses draw.io.
Write `flowchart LR` (or `TB` for topology) inline in a ```` ```mermaid ```` block. GitHub renders it, and it diffs as text.
