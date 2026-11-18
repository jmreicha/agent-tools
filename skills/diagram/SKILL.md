---
name: diagram
description: Use when asked to draw, diagram, sketch, or visualize architecture, infrastructure, network/traffic paths, request flows, or systems as a draw.io (.drawio), Excalidraw, or Mermaid diagram, to export a diagram to PNG/SVG/PDF, or when an existing doc would read better with a diagram.
version: 1.0.0
tags: [diagrams, drawio, excalidraw, architecture]
---

# Diagram

Plain black-and-white boxes, right-angle arrows, real vendor icons, and terse free-floating text.
The look stays close to draw.io defaults. Color is for vendor icons and the occasional emphasis.

## Principles

- **Terse.** Labels are 1–3 words (`ALB`, `API pod`). Notes are one line. Edge labels are a verb, plus the protocol when it matters (`Reads (SQL)`). Leave obvious edges unlabeled. When a diagram is crowded, cut before shrinking.
- **One zoom level per diagram** (from the C4 model):
  - **context:** the system, its users, and external systems
  - **containers:** apps and data stores inside the system
  - **components:** the parts inside one container

  Show more detail in a second diagram.
- **Consistent sets.** Diagrams of the same system reuse names, icons, and relative positions. Read the existing diagrams first.
- **Symmetric.** The main flow runs on one center line, and branches fan out evenly on both sides. Nodes in a row share the same size and spacing. Titles and boundaries are centered.
- **Accurate.** Put each thing where it actually lives. Use a vendor icon only for the real product, and a plain box for a generic concept.

## Wabi-sabi

Technical diagrams should look hand-made: balanced, but not machine-perfect. A slightly uneven
gap, a long route, or a crossing that can't be avoided is fine. Stop polishing once the diagram
reads clearly. Only fix real defects: overlaps, lines through labels, edges that end in mid-air.

## Modes

- **Technical** (the default): everything in this skill.
- **Styled** (company products, customer-facing content, anything that must look polished): find a brand guide, checking in this order:
  1. the conversation
  2. a location saved in memory (check that the file still exists)
  3. ask the user, then offer to save the location

  Apply only its palette (as accents on key nodes), its typeface (if draw.io has it), and its hard "never" rules. Don't copy the guide's content anywhere.

## Detail level

Pick the level by what the reader will do with the diagram:

| Reader's job | Level | Examples |
|---|---|---|
| Understand it | Brief | design proposals, onboarding, presentations, overview sections, leadership |
| Operate or change it | Full | troubleshooting, runbooks, change or security reviews, as-built, inventory |

Would someone copy an ID, CIDR, IP, or rule from it? Then it needs Full. Will it be shown in a meeting? Then it needs Brief.
- **Network and infrastructure diagrams:** one file with two pages, `Brief` first, then `Full`. Use the same names, icons, and positions on both. Docs embed Brief and link to Full.
- **Everything else:** Brief only, unless the request says detailed, full, inventory, or as-built.
- **Purpose unclear:** ask once: "Is this for explaining or for operating?"

- **Brief:** shortened IDs, collapsed repeats, terse labels.
- **Full:** keep every ID, CIDR, rule, and member from the source.
  - The name stays 12pt. Facts go below it at `fontSize=10;fontColor=light-dark(#666666,#BBBBBB);align=left;`, one fact per line.
  - List repeats one per line instead of collapsing them, and keep full IDs.
  - Still no prose: explanations go in a "How to read" key or in the doc.
  - Grow boxes and the page to fit. Split into two diagrams only when links start crossing.
  - Show the data source and date in the subtitle.

## Tool and location

- **draw.io** is the default. **Excalidraw** only when the user says excalidraw, sketch, whiteboard, or brainstorm. **Mermaid** inline is for simple flowcharts or sequences in repo markdown (about 8 nodes or fewer, no icons). For either of those, see [references/excalidraw-mermaid.md](references/excalidraw-mermaid.md).
- **Location:**
  - a diagram about the current repo goes in `docs/diagrams/<name>.drawio`, or in the repo root if there's no `docs/`
  - anything else goes in `~/Documents/<name>.drawio`

  Use kebab-case names, one page per file, and uncompressed XML.

## Style contract

| Element | Style | Size |
|---|---|---|
| Box | `rounded=1;whiteSpace=wrap;html=1;` | 120×60 |
| Free text | `text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;` | ~120–360×30 |
| Arrow | `edgeStyle=orthogonalEdgeStyle;endArrow=classic;html=1;rounded=0;curved=0;` | — |
| Boundary | `rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=none;absoluteArcSize=1;arcSize=24;`, with an empty `value` and a separate free-text label inside the top-left | fit |
| Note link | `endArrow=none;dashed=1;html=1;dashPattern=1 3;strokeWidth=2;rounded=0;` | — |
| Sticky note | `shape=mxgraph.mockup.text.stickyNote2;html=1;whiteSpace=wrap;align=center;fontSize=14;mainText=;fontColor=#666666;fillColor=#ffffcc;strokeColor=#F62E00;` | 140×100 |
| Internet / CDN | `ellipse;shape=cloud;whiteSpace=wrap;html=1;` | 160×90 |
| Title | free text + `fontSize=36;`, centered on top | — |
| Updated date | free text + `fontSize=10;fontColor=light-dark(#666666,#BBBBBB);align=right;`, reading `Updated YYYY-MM-DD`, in the bottom-right corner | 160×20 |

**Arrows**
- Flow runs left to right, out of the source's right-middle (`exitX=1;exitY=0.5`) and into the target's left-middle (`entryX=0;entryY=0.5`), with `source`/`target` set.
- Use horizontal and vertical segments with sharp right-angle bends. Never draw diagonals, curves, or double heads. Draw a request and its response as two arrows.
- Every edge gets its own ports (`exitX=0.25`/`0.75` when several share a side). Never merge edges, and never route through a label. Icon labels sit below the icon, so connect icons on the left, right, or top.
- Side inputs (Terraform, a template repo) sit directly above or below the node they feed.

**Lines and color**
- Everything is solid by default. A dashed boundary goes only around a real logical construct (cluster, environment, trust zone), and a diagram rarely needs more than 1–2. Accounts and VPCs are always solid (use the AWS groups in aws-network.md). A dashed arrow is only for emphasis: planned, async, or optional.
- Group by proximity, not boxes. Never use fills, shadows, gradients, `sketch=1`, swimlanes, or color for decoration.
- Any notation a reader can't guess gets a one-line text key in a corner (`dashed = planned`).
- Put an explanation as free text next to the thing it explains. Use a note link only when the text has to sit far away, and line up the note's center with its target so the link is straight.

**Layout**
- Use a 10px grid, ~100px gaps between columns, and ~60px between rows. Sibling groups of the same kind (regions, subnets, boundaries) use the same inside padding on every side; check-layout.py flags any that differ. Text is 12pt, or 24pt on every element for presentation diagrams.
- Children of a container use `parent="<container id>"` and coordinates relative to it. Never change cells `0` and `1`.
- **Dark mode:** draw.io flips default colors in dark mode, but keeps explicit ones.
  - Never set `background` on `mxGraphModel`.
  - Never hardcode black or white (`#000000`, `#1e1e1e`, `#ffffff`) on fills, strokes, or text. Leave them at the default.
  - Any text on an explicit light fill (AWS subnets, emphasis fill, sticky note) gets an explicit `fontColor`.
  - Gray text uses `light-dark(#666666,#BBBBBB)`, because a fixed gray is unreadable on a dark or semi-transparent fill.
  - Check with `--theme dark`. It doesn't match the desktop app exactly, so ask the user to check one diagram in the app.
- In `value`, escape `&`, `<`, and `"`, and write line breaks as `&lt;br&gt;`.

```xml
<mxfile host="Electron">
  <diagram name="Page-1" id="p1">
    <mxGraphModel grid="1" gridSize="10" page="1" pageWidth="1100" pageHeight="850">
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
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Read when relevant

| When the diagram… | Read |
|---|---|
| includes any product, service, or brand (icons and logos) | [references/icons.md](references/icons.md) |
| needs step numbers or emphasis on one path | [references/callouts.md](references/callouts.md) |
| is AWS, or a network or topology diagram | [references/aws-network.md](references/aws-network.md) |
| goes into a doc, or a doc might need one | [references/docs.md](references/docs.md) |

## Verify before handing back

Run `python3 <this skill dir>/scripts/check-layout.py <name>.drawio` and fix every edge it flags: line up the two ends exactly, or add waypoints if the bend is on purpose. Then render the diagram and look at it. Fix overlaps, lines through labels, and edges that end in mid-air:
`drawio -x -f png -b 10 -o /tmp/<name>.png <name>.drawio`, then Read the PNG.
No `image=https` may remain (see icons.md). Export only on request, keeping the diagram embedded so it stays editable:
`drawio -x -e -f <png|svg|pdf> -b 10 -o <name>.drawio.<ext> <name>.drawio`.
If the `drawio` CLI is missing (`brew install --cask drawio`), say that the render was skipped.
