---
name: diagram
description: Use when asked to draw, diagram, sketch, or visualize architecture, infrastructure, network/traffic paths, request flows, or systems as a draw.io (.drawio) or Excalidraw (.excalidraw) file, or to export a diagram to PNG/SVG/PDF.
version: 1.0.0
tags: [diagrams, drawio, excalidraw, architecture]
---

# Diagram

Make diagrams that look hand-made in draw.io: plain black-and-white
boxes, left-to-right arrows with right-angle bends, real vendor icons, and lots of free-floating
annotation text. The look is deliberately close to draw.io defaults. Color is reserved
for vendor icons and an occasional emphasis accent.

## Text is terse

Every label is 1–3 words: `ALB`, `API pod`, `Reads`. Annotations are one short line
(6–8 words max). Leave an edge unlabeled when the arrow's meaning is obvious. If a
diagram is getting crowded, cut nodes and text before shrinking anything. A sparse
diagram that reads at a glance beats a complete one.

Edge labels are a verb, plus the protocol when it matters: `Reads (SQL)`, `Pushes (OTLP)`, `Calls`.

## Scope (borrowed from the C4 model)

- **One zoom level per diagram.** Pick one:
  - **Context:** the system, its users, and external systems
  - **Containers:** apps and data stores inside one system
  - **Components:** the parts inside one container

  Never mix levels. If a node needs its insides shown, make a second diagram at the next level down.
- **Diagram sets stay consistent.** When several diagrams cover the same system, reuse the same node names, icons, and relative positions, so the reader can move between them. Read the existing diagrams in the set first.
- **Mini key, only when needed.** If a diagram uses notation a reader can't guess (dashed = planned, red = the emphasized path), add a one-line key as free text in a corner: `dashed = planned`. Never add a full legend.

## Wabi-sabi

Technical diagrams should look hand-made: balanced, but not machine-perfect. A slightly uneven
gap, a long route, or a crossing that can't be avoided is fine. Stop polishing once the diagram
reads clearly. Only fix real defects: overlaps, lines through labels, edges that end in mid-air.

## Two modes

- **Technical** (architecture, infra, flows, systems): everything below. This is the default.
- **Styled** (company products, customer-facing content, anything that has to look polished):
  find the brand or design guide in this order:
  1. a guide the user pointed to in this conversation
  2. a design guide location saved in memory (check that the file still exists)
  3. ask the user, then offer to save the location to memory for next time

  Apply it lightly, using only:
  - its palette, as a fill or accent on a few key nodes instead of black and white
  - its typeface, if draw.io has it (otherwise keep the default)
  - any hard "never" rules it states

  Everything else in this skill stays the same. Don't copy the guide's content into this skill or into notes.

## When to suggest a diagram

When editing an existing doc, suggest a diagram if the text makes the reader hold a picture in their head:
- 3+ components talking to each other
- a sequence of steps where order matters, especially with branches or loops
- a boundary (accounts, clusters, trust zones)
- the same flow already explained in 2+ paragraphs

Skip it for a single component, a linear list the text already covers, or anything that changes faster than anyone will update a picture.
Suggest first. Draw only when the user says yes. Place one diagram per section, directly under the paragraph that introduces it.

## 1. Pick the tool

- **draw.io**: the default for everything.
- **Excalidraw**: only when the user says excalidraw, sketch, whiteboard, or brainstorm.

## 2. Pick the location

- The diagram is about the repo you're working in: `docs/diagrams/<name>.drawio` if `docs/` exists, otherwise `<repo>/<name>.drawio`.
- Otherwise (not repo-specific, or no repo): `~/Documents/<name>.drawio`.
- Names are kebab-case and describe the subject (`waf-ingress.drawio`). One page per file.
- Write uncompressed XML so diffs stay readable.

## 3. draw.io style contract

Every diagram is built from these style strings, copied exactly.

| Element | Style | Size |
|---|---|---|
| Box (service, step, actor) | `rounded=1;whiteSpace=wrap;html=1;` | 120×60 |
| Boundary (logical construct only: cluster, account, VPC, env) | `rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=none;absoluteArcSize=1;arcSize=24;` + a sibling free-text label inside the top-left corner | fit contents |
| Edge label | set `value` on the flow arrow: verb, plus protocol if it matters (`Reads (SQL)`) | — |
| Free text / annotation | `text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;` | ~120–360×30 |
| Flow arrow | `edgeStyle=orthogonalEdgeStyle;endArrow=classic;html=1;rounded=0;curved=0;` | — |
| Emphasis arrow (planned, async, optional) | flow arrow + `dashed=1;` | — |
| Annotation link (note → thing) | `endArrow=none;dashed=1;html=1;dashPattern=1 3;strokeWidth=2;rounded=0;` | — |
| Sticky note (callout, caveat) | `strokeWidth=1;shadow=0;dashed=0;align=center;html=1;shape=mxgraph.mockup.text.stickyNote2;fontColor=#666666;mainText=;fontSize=17;whiteSpace=wrap;fillColor=#ffffcc;strokeColor=#F62E00;` | 140×100 (170×160 for multi-line) |
| Section header bar | `text;html=1;strokeColor=none;fillColor=#A9C4EB;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;` | width of section ×30 |
| Internet / CDN / "the cloud" | `ellipse;shape=cloud;whiteSpace=wrap;html=1;` | 160×90 |
| Title | free-text style + `fontSize=36;` (48 for a big multi-section page) | — |

**Layout rules**
- Flow runs left to right. Arrows leave the source at its right-middle (`exitX=1;exitY=0.5`) and enter the target at its left-middle (`entryX=0;entryY=0.5`), with `source`/`target` set on the edge.
- Arrows are horizontal or vertical, with sharp right-angle bends where they turn. Never draw a diagonal or a curve. Orthogonal routing with `rounded=0` takes care of this. Add `Array as="points"` waypoints only to steer a route around shapes.
- **Symmetry**: center and balance the layout.
  - The main flow runs along one center line.
  - Branches fan out evenly above and below it.
  - Nodes in a row share the same size and spacing.
  - A boundary is centered on its contents, with equal padding on all sides.
  - Center a title over the diagram.
  - If one side is heavier, move nodes until it balances.
- Side inputs (Terraform, a template repo) sit directly above or below the node they feed and connect vertically, using the top or bottom ports.
- Every edge gets its own entry and exit port. Edges never merge into or run along another edge, or a dashed edge will look like it ends in mid-air.
- When a node has several edges on one side, spread them across ports (`exitX=0.25`/`0.75`). Icon labels sit below the icon, so connect icons on their left, right, or top. Never connect through a label.
- Align on a 10px grid. Leave ~100px gaps between boxes in a row and ~60px between rows.
- Put an explanation next to the thing it explains, as free text. Add a dotted annotation link only when the text has to sit far away.
- Default font size is 12. For presentation diagrams (many nodes, shown on a screen), set `fontSize=24` on every box, text, and edge.

**Step numbers**: number the steps when order matters and the layout doesn't make it obvious. That covers request or deploy sequences, flows that branch or loop back, and anything with roughly 4+ steps.
- Use a badge per step: `ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#1e1e1e;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=11;` at 22×22.
- Place each badge on the top-left corner of the node that performs that step (offset about 14px up and left). If a step has no node of its own, such as a return trip or a hand-off, put its badge on that arrow instead, centered just above the line. Never put a badge on top of a line or a label.
- Count in reading order. A return trip keeps counting (a response is step 5, not 1b). Parallel steps share a number with a letter (3a, 3b).
- The badge replaces the edge label when the step is self-explanatory. Otherwise keep a 1–2 word label next to it.
- If steps need explaining, add one numbered key as free text in a corner (`1 Client calls edge`…), one short line per step. Don't add per-step notes.
- With emphasis active, the emphasized path's badges take the accent color.

**Dashed and dotted lines are rare.** Use them only for:
- **A boundary** around a real logical construct (cluster, account, VPC, environment, trust zone), or to set apart the one area the diagram is about.
- **A dashed arrow**, only to make an edge stand out from the rest (planned, async, optional).

Everything else is solid. Group related nodes by placing them close together. Don't box them in. One diagram rarely needs more than 1–2 boundaries.
A boundary's own `value` is empty. Its label is a separate sibling text cell.

**Emphasis color**: when a diagram is busy and one detail matters most (the request path, the
failing component, what's changing), color just that detail so it stands out.
- Use one accent color, `#F62E00` (the sticky-note red), with a second accent only when two details are being contrasted.
- For boxes, set `strokeColor=#F62E00;strokeWidth=2;`. Add `fillColor=#FDECEA;` only if the stroke alone doesn't stand out.
- For arrows, set `strokeColor=#F62E00;strokeWidth=2;fontColor=#F62E00;` so the label matches. Color a whole path end to end, not one segment.
- Keep it to a few elements. If most of the diagram is colored, nothing stands out, so remove it.
- Always pair emphasis with a sticky note next to the colored path saying what it shows: a bold 1–3 word title plus one short line. Color without an explanation just looks like decoration. The sticky note's red tab already matches the accent.
- In styled mode, use the guide's accent color instead.

**Never add**: color to categorize or decorate (only for emphasis, as above), `shadow=1`, gradients, `sketch=1`, swimlanes, or a colored legend.

### Vendor icons

Use an icon for anything that has one: K8s, AWS, GCP, Azure, Cisco, network gear,
databases, users, SaaS logos. The label goes below the icon. Fall back to a plain
box only when none of the sources below has a match. Find the style string in this order:
1. Reuse styles from existing `.drawio` files in the repo or the output directory: `grep -ho 'style="[^"]*shape=mxgraph\.[^"]*"' <dir>/*.drawio | sort -u`.
2. The drawio MCP `search_shapes` tool, if it's connected.
3. A draw.io library name pattern:
   - AWS: `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<service>;` with `fillColor=<category color>;strokeColor=#ffffff;`
   - GCP: `shape=mxgraph.gcp2.hexIcon;prIcon=<service>;fillColor=#5184F3;strokeColor=none;` (for example `prIcon=cloud_run`)
   - Azure: `image=img/lib/azure2/<category>/<Service>.svg;` on `shape=image;`
   - Cisco: `shape=mxgraph.cisco.<category>.<device>;fillColor=#036897;strokeColor=#ffffff;` (for example `routers.router`, `security.firewall`, `people.man_woman`)
   - K8s: see below.

   Look up real names in the draw.io app bundle instead of guessing them. A wrong name renders as a solid square:
   `grep -aoE 'mxgraph\.cisco\.[a-z_]+\.[a-z_]+' /Applications/draw.io.app/Contents/Resources/app.asar | sort -u | grep <term>`
   Swap in `aws4`, `gcp2`, `azure2` or `kubernetes` as needed.

   Every icon also gets `verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;aspect=fixed;`. Size icons 60×60, and use about 48×48 for K8s objects inside a boundary.

A thing that contains other things (cluster, VPC, account) is a boundary, not an icon.
Put a small vendor icon (EKS, GKE) at 30×30 next to the boundary's label, if one exists.
Look up a real logo for any known product or brand that has no library icon (Argo CD, Terraform, Honeycomb, PagerDuty, Okta).
Try these sources in order, and `curl -sL -o /dev/null -w '%{http_code}'` each URL before using it:
1. Simple Icons: `https://cdn.simpleicons.org/<slug>` (slug is the lowercase brand name: `argo`, `terraform`, `github`, `pagerduty`)
2. CNCF artwork: `https://raw.githubusercontent.com/cncf/artwork/main/projects/<name>/icon/color/<name>-icon-color.svg` (for example `crossplane`, `opentelemetry`)
3. The vendor's GitHub org avatar: `https://github.com/<org>.png?size=128` (for example `honeycombio`)
4. The vendor's press kit or brand page, found by web search

Use the URL as `shape=image;imageAspect=0;image=<url>;`, then **embed it so the diagram works offline**:
`python3 <this skill dir>/scripts/embed-icons.py <name>.drawio`
The script swaps every web URL for a data URI, works on `.drawio` and `.excalidraw` files, and exits non-zero if any fetch fails or a URL doesn't return an image.
Never ship a diagram that still contains `image=https`.

If no source has a logo, use a cloud shape for an edge or CDN service and a plain box for anything else.

Run the render step (section 4) after adding icons. A guessed shape name renders blank or as a
plain box. If it does, look up the correct name or fall back to a plain box.

Known-good styles:
- **K8s object**: `shape=mxgraph.kubernetes.icon;prIcon=pod;fillColor=#2875E2;strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;` (set `prIcon` to `api`, `svc`, `deploy`, `ing`, `crd`, `secret`, `cm`, `job`, `ns`, `node`, etc.)
- **EKS**: `shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.eks;fillColor=#232F3E;strokeColor=#ffffff;fontColor=#232F3E;verticalLabelPosition=middle;verticalAlign=bottom;align=center;html=1;fontSize=10;fontStyle=1;` at 80×100
- **AWS account boundary**: `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fontColor=#CD2264;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;container=1;collapsible=0;html=1;whiteSpace=wrap;`
- **AWS cloud boundary**: the same group style with `grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fontColor=#232F3E;`
- **Route 53 / ALB / RDS / S3**: `outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;gradientColor=none;shape=mxgraph.aws3.<route_53|application_load_balancer|rds|s3>;fillColor=<#F58536|#F58534|#2E73B8|#E05243>;`

Children of a container set `parent="<container id>"` and use coordinates relative to it.
Never change cells `0` and `1`: every other cell hangs off `parent="1"`.

### Skeleton

```xml
<mxfile host="Electron">
  <diagram name="Page-1" id="p1">
    <mxGraphModel grid="1" gridSize="10" guides="1" connect="1" arrows="1" page="1" pageWidth="1100" pageHeight="850" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="client" value="Client" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="200" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="api" value="API" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="260" y="200" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;html=1;rounded=0;curved=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="client" target="api">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="n1" value="Client/Device initiates request" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="1">
          <mxGeometry x="20" y="270" width="160" height="30" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Escape `&`, `<`, and `"` in `value` attributes. Use `<br>` (escaped as `&lt;br&gt;`) for line breaks.

## 4. Verify, then export

Render the diagram and look at it before you report back. Overlaps, crossing arrows, and labels sitting on lines are the usual faults:

```bash
drawio -x -f png -b 10 -o /tmp/<name>.png <name>.drawio   # then Read the PNG
```

Export only when the user asks for it. Keep the diagram embedded so the export stays editable:
`drawio -x -e -f <png|svg|pdf> -b 10 -o <name>.drawio.<ext> <name>.drawio`.
If the `drawio` CLI is missing (on macOS: `brew install --cask drawio`), skip the render and say that you skipped it.

## Embedding

- **Markdown in a repo:** export `name.drawio.svg` with `drawio -x -e -f svg -o name.drawio.svg name.drawio` and reference it with `![Alt text](name.drawio.svg)`. GitHub renders it, and draw.io (or the VS Code extension) still opens it for editing, so you keep one file and no stale PNG.
- **Confluence (draw.io app):** uploading a new attachment version does not update the page. Each diagram on the page is pinned to a version (its `revision`/`contentVer` macro params). Repoint it after uploading: open the diagram in the page editor and save, or update those params through the API. Then confirm the page shows the new version.
- **Anything else:** export a PNG or SVG and paste it in.

## 5. Excalidraw (on request only)

Excalidraw gets the same visual rules: black strokes, no fills, left-to-right flow, dotted
annotation links, dashed boundaries. Write `<name>.excalidraw` in the same location as a draw.io file would go.

- Shapes: `"strokeColor":"#1e1e1e","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":2,"roughness":1,"roundness":{"type":3}`, at 160×80.
- Boundary: a rectangle with `"strokeStyle":"dashed"`. Annotation link: an arrow with `"strokeStyle":"dotted","endArrowhead":null`.
- Text uses `"fontFamily":5` (Excalifont), at size 20.
- To put a label inside a shape, the text gets `"containerId":"<shape id>"` and the shape lists it in `"boundElements":[{"type":"text","id":"<text id>"}]`.
- An arrow gets `"startBinding":{"elementId":"<id>","focus":0,"gap":4}` and the matching `endBinding`. Each bound shape lists `{"type":"arrow","id":"<arrow id>"}` in its `boundElements`.
- The file wrapper is `{"type":"excalidraw","version":2,"source":"https://excalidraw.com","elements":[...],"appState":{"viewBackgroundColor":"#ffffff","gridSize":20},"files":{}}`.

- Logos use the same lookup sources as draw.io. Add an element `{"type":"image","fileId":"<id>","status":"saved","scale":[1,1]}` and a matching `"files":{"<id>":{"id":"<id>","mimeType":"image/svg+xml","dataURL":"<logo url>","created":1}}`. Then run `python3 <this skill dir>/scripts/embed-icons.py <name>.excalidraw`. It embeds the URL and fixes SVG sizing, which Excalidraw otherwise gets wrong.

Every element also needs `id, type, x, y, width, height, angle:0, opacity:100, seed, version:1, versionNonce, isDeleted:false, groupIds:[], frameId:null, link:null, locked:false, updated:1, boundElements`. Text also needs `text, originalText, fontSize, lineHeight:1.25, textAlign:"center", verticalAlign:"middle", autoResize:true`. Arrows need `points:[[0,0],[dx,dy]]` and `startArrowhead:null`.

Render it and look at the result, the same as for draw.io:
`excalidraw render <name>.excalidraw --out /tmp/<name>.png --scale 2`. Then Read the PNG.
If the CLI is missing, install it with `npm i -g excalidraw-cli`, or tell the user to open the file at excalidraw.com.

## Common mistakes

| Mistake | Fix |
|---|---|
| Pastel fills to tell services apart | Plain boxes. The vendor icon or label already identifies the service. |
| Unclear order in a multi-step flow | Number the steps with badges on the nodes that perform them. |
| Context, containers, and internals all on one page | One zoom level per diagram. Split the rest into a second diagram. |
| Color on half the diagram | Accent only the one detail the viewer must see. |
| Diagonal or curved arrows | Orthogonal routing with sharp corners: `edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0`. |
| Dashed boxes around every group | Group by proximity. Use a boundary only for a real logical construct. |
| Lopsided layout | Center the main flow and balance the branches around it. |
| Linked `image=https://` icons | Run `scripts/embed-icons.py`. |
| A generic box for AWS/K8s services | Use the vendor icon (see Vendor icons). |
| Swimlanes or filled containers for groups | A dashed boundary with a corner label, or an AWS group. |
| `endArrow=block` or rounded edge corners | `endArrow=classic;rounded=0`. |
| A dashed note connector | Dotted: `dashPattern=1 3;strokeWidth=2;endArrow=none`. |
| Sentences in labels or on edges | 1–3 words. Cut the rest. |
| Shipping without looking at the render | Export a PNG and Read it. |
