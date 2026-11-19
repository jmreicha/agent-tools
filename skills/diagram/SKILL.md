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
- **Adapt** (editing someone else's diagram: update, add to, fix, extend): match the existing diagram, not this skill. Its owner and readers already know its conventions.
  - Before editing, read its styles: colors, line types, fonts, sizes, shapes, icon set, spacing, and key.
  - A new element copies the style of its closest existing sibling (same kind of node, same kind of line). A new line type gets a key row in the existing key's format.
  - Don't restyle, recolor, re-space, or move anything you weren't asked to change, even where this skill would do it differently.
  - Fix only real defects in the parts you touch: overlaps, edges that end in mid-air, lines through labels. Report check-layout's other findings (contrast, centering, padding) to the user instead of fixing them.
  - Switch to Technical only when the user asks for a redraw or a conversion to this style.
  - If a request like "clean this up" could mean either, ask once: "Keep its current style, or redraw it in ours?"

## Detail level

Pick the level by what the reader will do with the diagram:

| Reader's job | Level | Examples |
|---|---|---|
| Understand it | Brief | design proposals, onboarding, presentations, overview sections, leadership |
| Operate or change it | Full | troubleshooting, runbooks, change or security reviews, as-built, inventory |

Would someone copy an ID, CIDR, IP, or rule from it? Then it needs Full. Will it be shown in a meeting? Then it needs Brief.
- **Network and infrastructure diagrams** (cloud resources, networks, clusters: things with IDs someone operates; not process flows or GitOps pipelines): one file with two pages, `Brief` first, then `Full`. Use the same names, icons, and positions on both. Docs embed Brief and link to Full.
- **Everything else:** Brief only, unless the request says detailed, full, inventory, or as-built.
- **Purpose unclear:** ask once: "Is this for explaining or for operating?"

- **Brief:** shortened IDs, collapsed repeats, terse labels.
- **Full:** keep every ID, CIDR, rule, and member from the source.
  - The name stays 12pt and bold. Facts go below it at 10px in the default color, one fact per line (`Diagram.card`).
  - List repeats one per line instead of collapsing them, and keep full IDs.
  - Still no prose: explanations go in a note, the key, or the doc.
  - Grow boxes and the page to fit. Split into two diagrams only when links start crossing.
  - Show the data source and date in the subtitle.

## Tool and location

- **draw.io** is the default. **Excalidraw** only when the user says excalidraw, sketch, whiteboard, or brainstorm. **Mermaid** inline is for simple flowcharts or sequences in repo markdown (about 8 nodes or fewer, no icons). For either of those, see [references/excalidraw-mermaid.md](references/excalidraw-mermaid.md).
- **Location:**
  - a diagram about the current repo goes in `docs/diagrams/<name>.drawio`, or in the repo root if there's no `docs/`
  - anything else goes in `~/Documents/<name>.drawio`

  Use kebab-case names and uncompressed XML: one page per file, or two for Brief + Full. A single page is named after the title (`Diagram.title` does this), never `Page-1`.

## Style contract

| Element | Style | Size |
|---|---|---|
| Box | `rounded=1;whiteSpace=wrap;html=1;` | 120×60 |
| Free text | `text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;` | ~120–360×30 |
| Arrow | `edgeStyle=orthogonalEdgeStyle;endArrow=classic;html=1;rounded=0;curved=0;` | — |
| Boundary | `rounded=1;whiteSpace=wrap;html=1;fillColor=none;absoluteArcSize=1;arcSize=24;`, with an empty `value` and a separate free-text label inside the top-left | fit |
| Note link | `endArrow=none;dashed=1;html=1;dashPattern=1 3;strokeWidth=2;rounded=0;` | — |
| Note | `rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacing=8;fontSize=11;fillColor=none;absoluteArcSize=1;arcSize=8;strokeColor=light-dark(#BBBBBB,#666666);`, with a bold title line, then one short line each (`Diagram.note`). Never sticky notes | ~220 wide |
| Key | only when 3 or more symbols need decoding (see Lines and color). The note style, titled **Key**, 40px below the diagram and centered on the title's center line too (together with any "How to read" note beside it, same top and height), with one row per symbol: a short sample of the line (its dash and color), then its meaning (`Diagram.key`) | ~300 wide |
| Internet / CDN | `shape=cloud;whiteSpace=wrap;html=1;` (no `ellipse;`, which bends edges). The internet is always this cloud, never a box or an icon. Connect only at side midpoints | 160×90 |
| Title | free text + `fontSize=36;`, centered on the main box (the outermost boundary or group), not the page (`Diagram.title`). The subtitle and the bottom key row share that center line, with the first content row 60px or more below it (below the subtitle, when there is one). If the source has no title, name what it shows (`prod VPC traffic`) | — |
| Updated date | free text + `fontSize=10;fontColor=light-dark(#666666,#BBBBBB);align=right;`, reading `Updated YYYY-MM-DD`, in the bottom-right corner | 160×20 |

**Arrows**
- Flow runs left to right, out of the source's right-middle (`exitX=1;exitY=0.5`) and into the target's left-middle (`entryX=0;entryY=0.5`), with `source`/`target` set.
- Use horizontal and vertical segments with sharp right-angle bends. Never draw diagonals, curves, or double heads. Draw a request and its response as two arrows. A link with no direction (peering, a physical cable) is a line with `endArrow=none;`.
- Every edge gets its own ports (`exitX=0.25`/`0.75` when several share a side). Never merge edges, and never route through a label. Icon labels sit below the icon, so connect icons on the left, right, or top.
- Side inputs (Terraform, a template repo) sit directly above or below the node they feed. An icon that connects from below gets its label on top or to the left (`label_at(style, "top")`), so the edge never crosses it.
- Two branches from one node mirror each other around its center line (exit at 0.25 and 0.75).
- **Fan-out** (3+ edges to a column of targets) shares one trunk in open space. The **emphasis path** gets its own straight route. See layout.md.

**Lines and color**
- Every boundary is solid; dashes are for lines only. If a boundary seems to need dashes, ask the user instead of choosing. A boundary goes only around a real construct (cluster, environment, trust zone), and a diagram rarely needs more than 1–2. AWS accounts and VPCs use the AWS groups in aws-network.md. A dashed arrow means planned, async, or optional. In network diagrams, dashed also means a virtual link (see aws-network.md).
- Group by proximity, not boxes. Never use fills, shadows, gradients, `sketch=1`, swimlanes, or color for decoration.
- **Key:** add one only when the diagram uses 3 or more symbols a reader can't decode from the labels (dash patterns, line colors, user colors). Never list a plain solid arrow. With 1–2 such symbols, label the edges instead (`peering`, `later`). If you don't know what a source's notation means, ask or leave it out; never guess.
- Put an explanation as free text next to the thing it explains, or as a note when it needs a title. In a flow, the note sits before the flow's entry point in reading order (left of it in a left-to-right flow), centered on it, never below the flow. Use a note link only when the note has to sit far away, and line up the note's center with its target so the link is straight.

**Contrast** (WCAG)
- Text needs a contrast ratio of 4.5:1 against what's behind it: 3:1 for large text (18pt, or 14pt bold), and aim for 7:1 at 10–11px. Lines, icons, and borders that carry meaning need 3:1 against the page.
- Contrast comes from lightness, not hue: green text on a green tint, or red on orange, fails even though the hues differ.
- A mid-tone fails in one theme or the other. Give text that matters a `light-dark()` pair: darker in light mode, lighter in dark mode.
- check-layout.py flags text and lines below these ratios. To try a new pair first, use `contrast(fg, bg, opacity)` in drawio_lib.py, which blends a semi-transparent fill over the page.
- The accent `#F62E00` is for lines and borders only. Red text uses `RED_TEXT` (`light-dark(#C42500,#FF6A3D)`).

**Layout**
- Use a 10px grid, ~100px gaps between columns, and ~60px between rows. Sibling groups of the same kind (regions, subnets, boundaries) use the same inside padding on every side; check-layout.py flags any that differ.
- Center groups inside their parent, with equal left and right margins. A gateway (IGW, NAT) sits inside a margin, not in place of one; check-layout.py flags off-center groups.
- It's fine for a diagram to spill past the page or into new grid sections. Never cram to fit. Text is 12pt, or 24pt on every element for presentation diagrams.
- Children of a container use `parent="<container id>"` and coordinates relative to it. Never change cells `0` and `1`.
- **Dark mode:** draw.io flips default colors. The desktop app keeps explicit colors, but `--theme dark` in the CLI flips them too, so give any color that matters a `light-dark(light,dark)` pair.
  - Never set `background` on `mxGraphModel`.
  - Never hardcode black or white (`#000000`, `#1e1e1e`, `#ffffff`) on fills, strokes, or text. Leave them at the default.
  - Text on an opaque light fill (emphasis fill) gets an explicit `fontColor`. Text on a semi-transparent fill (AWS subnets) keeps the default color, never gray, and subnet labels use the darker/lighter `light-dark()` pairs in aws-network.md.
  - Gray text uses `light-dark(#666666,#BBBBBB)`, because a fixed gray is unreadable on a dark or semi-transparent fill.
  - `light-dark()` works only in style keys (`fontColor`, `strokeColor`, `fillColor`). Inside label HTML (`<b style="color:…">`), draw.io always renders the light value, so dark mode gets dark text. Color a whole cell with `fontColor`, or give the colored text its own cell; check-layout.py flags inline `light-dark()`.
  - `--theme dark` doesn't match the desktop app exactly, so ask the user to check one diagram in the app.
- In `value`, escape `&`, `<`, and `"`, and write line breaks as `&lt;br&gt;`.

Build diagrams with `python3` and `<this skill dir>/scripts/drawio_lib.py` (styles, cards, AWS groups, ports, multi-page). Hand-edit XML only for small fixes.

## Read when relevant

| When the diagram… | Read |
|---|---|
| includes any product, service, or brand (icons and logos) | [references/icons.md](references/icons.md) |
| needs step numbers or emphasis on one path | [references/callouts.md](references/callouts.md) |
| is AWS, or a network or topology diagram | [references/aws-network.md](references/aws-network.md) |
| colors any group, boundary, or line | [references/palette.md](references/palette.md) |
| goes into a doc, or a doc might need one | [references/docs.md](references/docs.md) |
| has groups, Full-detail cards, a fan-out, an emphasis path, or a Brief/Full pair | [references/layout.md](references/layout.md) |

## Verify before handing back

Run `python3 <this skill dir>/scripts/check-layout.py <name>.drawio` and fix everything it flags: edge jogs (line up the two ends exactly, or add waypoints if the bend is on purpose), uneven padding, an off-center title or subtitle, content closer than 60px to the heading, low contrast, lines through labels, edge labels on borders or on each other, and logos without the standard tile. Then render the diagram and look at it. The label checks estimate text width, so still look for overlaps, crowded labels, and edges that end in mid-air:
`drawio -x -f png -b 10 -p <page> --theme <light|dark> -o /tmp/<name>.png <name>.drawio`, then Read the PNG. Check every page in both themes (`-p` is 1-based). The `Updated` date is today; the subtitle's data date comes from the source, and the two may differ.
No `image=https` may remain (see icons.md). Export only on request, keeping the diagram embedded so it stays editable:
`drawio -x -e -f <png|svg|pdf> -b 10 -o <name>.drawio.<ext> <name>.drawio`.
If the `drawio` CLI is missing (`brew install --cask drawio`), say that the render was skipped.
