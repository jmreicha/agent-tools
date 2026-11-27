---
name: diagram
description: Use whenever the answer includes any diagram, including a short Mermaid flowchart or sequence diagram for a README or chat reply. Covers drawing, sketching, or visualizing architecture, infrastructure, network and traffic paths, request flows, pipelines, and systems as draw.io (.drawio), Excalidraw, or Mermaid, exporting a diagram to PNG, SVG, or PDF, and spotting when an existing doc would read better with a diagram.
version: 1.1.0
tags: [diagrams, drawio, excalidraw, architecture]
---

# Diagram

Plain black and white boxes, right-angle arrows, real vendor icons, and terse free floating text.
The look stays close to draw.io defaults. Color is for vendor icons and the occasional emphasis.

## Principles

- **Terse.** Labels are 1-3 words (`ALB`, `API pod`). Notes are one line. Edge labels are a verb, plus the protocol when it matters (`Reads (SQL)`). Leave obvious edges unlabeled. When a diagram is crowded, cut before shrinking.

- **One zoom level per diagram** (from the C4 model):
  - **context:** the system, its users, and external systems
  - **containers:** apps and data stores inside the system
  - **components:** the parts inside one container

  Show more detail in a second diagram.

- **Consistent sets.** Diagrams of the same system reuse names, icons, and relative positions. Read the existing diagrams first.

- **Symmetric.** The main flow runs on one center line, and branches fan out evenly on both sides. Nodes in a row share the same size and spacing. Nodes stacked in a column share one center line, even when one is a box and the other an icon. Titles and boundaries are centered.

- **Accurate.** Put each thing where it actually lives. Use a vendor icon only for the real product, and a plain box for a generic concept. Trace every edge that crosses a boundary to its real hops (DNS, then CDN, load balancer, NAT, IGW, or private endpoint, then service) before you draw it, including PrivateLink: a vendor hostname (`collector.newrelic.com`) can resolve to an endpoint inside the VPC instead of the internet. An edge drawn inside one VPC says the traffic stays private.

- **Specific names.** Label every account, resource, and service with its real name (`InternalServices-Stg (320343233951)`, `claude-gateway-prod-reports`), not a placeholder named after what it holds or does (`Claude Gateway account`). If the source gives only an ID, look the name up (`~/.aws/config`, `organizations describe-account`, tags, the repo). If you can't find it, use the ID alone.

- **Labels read `Name (details)`.** Group and boundary labels put IDs, CIDRs, routes, and qualifiers in parentheses after the name, comma-separated, like accounts: `VPC prod (vpc-0c8f…, 10.94.0.0/16)`, `EKS prod-us-blue (v1.34, private endpoint)`, `Internet (untrusted)`. A cluster's version and endpoint access are worth looking up (`eks describe-cluster`). No `·` separators. check-layout.py flags the rest.

## Wabi-sabi

Technical diagrams should look handmade: balanced, but not machine-perfect. A slightly uneven
gap, a long route, or a crossing that can't be avoided is fine. Stop polishing once the diagram
reads clearly. Only fix real defects: overlaps, lines through labels, edges that end in mid-air.
check-layout.py findings count as defects: fix them, or leave one on purpose and tell the user why (a nested trust zone that can't share its siblings' padding).

## Feng shui

Wabi-sabi lets a diagram be imperfect. Feng shui keeps it calm. Busy diagrams, and busy lines most of all, are the most common complaint. These are judgment calls for the render review, not rules to enforce:

- **Fewer lines.** Draw only the edges that tell the story. Leave out ones the reader assumes (image pulls, secret mounts, health checks). Two parallel lines between the same groups can become one labeled line.
- **Short, direct lines.** Move nodes so each line is short with at most one bend. A long detour around other nodes means a node is in the wrong place.
- **One direction.** Lines follow the reading direction. U-turns, lines doubling back, and long return paths break the flow. If one is needed, give it its own lane on the edge of the diagram.
- **Room for the main node.** The node the diagram is about sits where the eye lands first, with space around it. More than two lines arriving on one side crowds it.
- **Even weight.** No dense corner next to an empty one, and no large group that's mostly empty. Shrink or rearrange instead.
- **Calm, not vague.** These are engineers' diagrams: keep the terse facts (names, intervals, roles, protocols). When you cut a line, move its fact into a node label, an edge label, or the subtitle (`describe (dibs-reader)`, `poll (2 min)`) instead of dropping it.
- **Explain the not obvious.** When labels can't say what a piece does (a job, a sync loop, an ownership rule), number it and explain it in a `How it works` note beside the diagram (callouts.md). Don't make the label longer.
- **Split by concern.** When a diagram stays busy after this, split it into pages, one concern each (`Runtime`, `Discovery`, `Deploy`), then add a last page named `Full` with everything combined. Order the pages from least to most detail. Readers land on the calm pages first, and engineers still have the whole picture. All pages share names, labels, icons, and step numbers, and draw from one facts table (layout.md).

## Modes

- **Technical** (the default): everything in this skill.

- **Styled** (company products, customer facing content, anything that needs to look polished): find a brand guide, checking in this order:
  1. the conversation
  2. a location saved in memory (check that the file still exists)
  3. ask the user, then offer to save the location

  Apply only its palette (as accents on key nodes), its typeface (if draw.io has it), and its hard "don't" rules. Don't copy the guide's content anywhere.

- **Adapt** (editing someone else's diagram: update, add to, fix, extend): match the existing diagram, not this skill. Its owner and readers already know its conventions.
  - Before editing, read its styles: colors, line types, fonts, sizes, shapes, icon set, spacing, and key.
  - A new element copies the style of its closest existing sibling (same kind of node, same kind of line). A new line type gets a key row in the existing key's format.
  - Don't restyle, recolor, respace, or move anything you weren't asked to change, even where this skill would do it differently.
  - Fix only real defects in the parts you touch: overlaps, edges that end in mid-air, lines through labels. Report check-layout's other findings (contrast, centering, padding) to the user instead of fixing them.
  - Switch to Technical only when the user asks for a redraw or a conversion to this style.
  - If a request like "clean this up" could mean either, ask once: "Keep its current style, or redraw it in ours?"

## Detail level

Pick the level by what the reader does with the diagram:

| Reader's job         | Level | Examples                                                                   |
| -------------------- | ----- | -------------------------------------------------------------------------- |
| Understand it        | Brief | design proposals, onboarding, presentations, overview sections, leadership |
| Operate or change it | Full  | troubleshooting, runbooks, change or security reviews, as-built, inventory |

If someone would copy an ID, CIDR, IP, or rule from it, it needs Full. If it goes up on a screen in a meeting, it needs Brief.

- **Network and infrastructure diagrams** (cloud resources, networks, and clusters: things with IDs someone operates, not process flows or GitOps pipelines): one file with two pages, `Brief` first, then `Full`. Use the same names, icons, and positions on both. Docs embed Brief and link to Full. When the source has no more detail than Brief shows (no IDs, CIDRs, ports, or accounts), make one page named after the title, and say which facts a Full page needs.
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
  - a diagram about the current repo goes next to its existing architecture docs or diagrams. Find them first: `git ls-files '*.drawio' '*.excalidraw' '*.mmd'`, plus any `architecture`, `design`, or `diagrams` folder. If none exist, create `docs/diagrams/<name>.drawio`.
  - anything else goes in `~/Documents/<name>.drawio`

  Use kebab-case names and uncompressed XML: one page per file, two for Brief + Full, or concern pages plus a last `Full` page when split (see Feng shui). Name a single page after the title, which `Diagram.title` does for you. Leave no page named `Page-1`.

## Style contract

| Element      | Style                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Size        |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| Box          | `rounded=1;whiteSpace=wrap;html=1;`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | 120×60      |
| Free text    | `text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;`                                                                                                                                                                                                                                                                                                                                                                                                                                                     | ~120-360×30 |
| Arrow        | `edgeStyle=orthogonalEdgeStyle;endArrow=classic;html=1;rounded=0;curved=0;`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | n/a         |
| Boundary     | `rounded=1;whiteSpace=wrap;html=1;fillColor=none;absoluteArcSize=1;arcSize=24;`, with an empty `value` and a separate free-text label inside the top-left. A boundary with a vendor icon (EKS, Docker) gets square corners (`rounded=0;`) to match the AWS groups. `Diagram.boundary(icon=...)` does this                                                                                                                                                                                                                                                      | fit         |
| Note link    | `endArrow=none;dashed=1;html=1;dashPattern=1 3;strokeWidth=2;rounded=0;`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | n/a         |
| Note         | `rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacing=8;fontSize=11;fillColor=none;absoluteArcSize=1;arcSize=8;strokeColor=light-dark(#BBBBBB,#666666);`, with a bold title, a blank line, then one short line each, or numbered steps that wrap (`Diagram.note`). Never sticky notes                                                                                                                                                                                                                                                         | ~220 wide   |
| Key          | only when 3 or more symbols need decoding (see Lines and color). The note style, titled by what it decodes (`Issue severity and crown jewels`, `Line types`), not just **Key** (`Diagram.key(..., title=)`), in the bottom-left corner: 40px below the lowest shape, its left edge flush with the leftmost shape (any "How to read" note goes beside it, same top and height). One row per symbol: a short sample (line, icon, or chip), then its meaning in 1-2 words. Drop words the title or page already says (`High`, not `High finding`) (`Diagram.key`) | ~300 wide   |
| Internet     | `shape=cloud;whiteSpace=wrap;html=1;` (no `ellipse;`, which bends edges). The internet is this cloud, not a box or an icon. A named CDN or edge provider (Cloudflare, CloudFront, Akamai, Fastly) gets its vendor icon instead. Connect only at side midpoints                                                                                                                                                                                                                                                                                                 | 160×90      |
| Title        | free text + `fontSize=36;`, centered on the main box (the outermost boundary or group), not the page (`Diagram.title`). The subtitle shares that center line, with the first content row 60px or more below it (below the subtitle, when there is one). If the source has no title, name what it shows (`prod VPC traffic`)                                                                                                                                                                                                                                    | n/a         |
| Updated date | free text + `fontSize=10;fontColor=light-dark(#666666,#BBBBBB);align=right;`, reading `Updated YYYY-MM-DD`, in the bottom-right corner                                                                                                                                                                                                                                                                                                                                                                                                                         | 160×20      |

### Arrows

- Flow runs left to right, out of the source's right-middle (`exitX=1;exitY=0.5`) and into the target's left-middle (`entryX=0;entryY=0.5`), with `source`/`target` set.
- Use horizontal and vertical segments with sharp right-angle bends. Don't draw diagonals, curves, or double heads. Draw a request and its response as two arrows. A link with no direction (peering, a physical cable) is a line with `endArrow=none;`.
- Every edge gets its own ports (`exitX=0.25`/`0.75` when several share a side). Don't merge edges or route through a label. Icon labels sit below the icon, so connect icons on the left, right, or top.
- Side inputs (Terraform, a template repo) sit directly above or below the node they feed. An icon that connects from below gets its label on top or to the left (`label_at(style, "top")`), so the edge doesn't cross it. That's the only reason to move a label. When a line would cross something on its way into an icon (a group's label, say), bring the line in from a side and keep the label below, so the group stays compact.
- Two branches from one node mirror each other around its center line (exit at 0.25 and 0.75), and turn at the same distance from it: give both the same waypoint x (or y).
- **Fan-out** (3+ edges to a column of targets) shares one trunk in open space. The **emphasis path** gets its own straight route. See layout.md.

### Lines and color

- Every boundary is solid, except trust boundaries on a Security page, which are dashed (aws-network.md). Otherwise dashes are for lines only. If another boundary seems to need dashes, ask the user instead of choosing. A boundary goes only around a real construct (cluster, environment, trust zone), and a diagram rarely needs more than 1-2. AWS accounts and VPCs use the AWS groups in aws-network.md. A dashed arrow means planned, async, or optional. In network diagrams, dashed also means a virtual link (see aws-network.md).
- Group by proximity, not boxes. Never use fills, shadows, gradients, `sketch=1`, swimlanes, or color for decoration.
- **Key:** add one only when the diagram uses 3 or more symbols a reader can't decode from the labels (dash patterns, line colors, user colors). Leave plain solid arrows out of it. With 1-2 such symbols, label the edges instead (`peering`, `later`). If you don't know what a source's notation means, ask or leave it out. Don't guess.
- Put an explanation as free text next to the thing it explains, or as a note when it needs a title. In a flow, the note sits before the flow's entry point in reading order (left of it in a left to right flow), centered on it. Don't put it below the flow. A numbered `How it works` note is the exception: it goes on the right (callouts.md). Use a note link only when the note has to sit far away, and line up the note's center with its target so the link is straight.

### Contrast (WCAG)

- Text needs a contrast ratio of 4.5:1 against what's behind it: 3:1 for large text (18pt, or 14pt bold), and aim for 7:1 at 10-11px. Lines, icons, and borders that carry meaning need 3:1 against the page.
- Contrast comes from lightness, not hue: green text on a green tint, or red on orange, fails even though the hues differ.
- A mid-tone fails in one theme or the other. Give text that matters a `light-dark()` pair: darker in light mode, lighter in dark mode.
- `check-layout.py` flags text and lines below these ratios. To try a new pair first, use `contrast(fg, bg, opacity)` in `drawio_lib.py`, which blends a semitransparent fill over the page.
- The accent `#F62E00` is for lines and borders only. Red text uses `RED_TEXT` (`light-dark(#C42500,#FF6A3D)`).

### Layout

- Use a 10px grid, ~100px gaps between columns, and ~60px between rows. Sibling groups of the same kind (regions, subnets, boundaries) use the same inside padding on every side. `check-layout.py` flags any that differ.
- Center groups inside their parent, with equal left and right margins. A gateway (IGW, NAT) sits inside a margin, not in place of one. `check-layout.py` flags off center groups. When the order is deliberate (Security's trust zones, a gateway widening one margin), mark the parent with `Diagram.fixed(id, ...)`, which skips its centering and sibling padding checks.
- It's fine for a diagram to spill past the page or into new grid sections. Don't cram to fit. When a label has no room (it lands on a border, or a line runs through it), widen the gap: move columns apart or widen the group. Don't shrink, abbreviate, or drop the label to make it fit. Text is 12pt, or 24pt on every element for presentation diagrams.
- Children of a container use `parent="<container id>"` and coordinates relative to it. Never change cells `0` and `1`.
- **Dark mode:** draw.io flips default colors. The desktop app keeps explicit colors, but `--theme dark` in the CLI flips them too, so give any color that matters a `light-dark(light,dark)` pair.
  - Never set `background` on `mxGraphModel`.
  - Never hardcode black or white (`#000000`, `#1e1e1e`, `#ffffff`) on fills, strokes, or text. Leave them at the default.
  - Text on an opaque light fill (emphasis fill) gets an explicit `fontColor`. Text on a semitransparent fill (AWS subnets) keeps the default color, not gray, and subnet labels use the darker/lighter `light-dark()` pairs in aws-network.md.
  - Gray text uses `light-dark(#666666,#BBBBBB)`, because a fixed gray is unreadable on a dark or semitransparent fill.
  - `light-dark()` works only in style keys (`fontColor`, `strokeColor`, `fillColor`). Inside label HTML (`<b style="color:…">`), draw.io always renders the light value, so dark mode gets dark text. Color a whole cell with `fontColor`, or give the colored text its own cell. `check-layout.py` flags inline `light-dark()`.
  - `--theme dark` doesn't match the desktop app exactly, so ask the user to check one diagram in the app.
- In `value`, escape `&`, `<`, and `"`, and write line breaks as `&lt;br&gt;`.

Build diagrams with `python3` and `<this skill dir>/scripts/drawio_lib.py` (styles, cards, AWS groups, ports, multipage). Hand edit XML only for small fixes.

## Read when relevant

| When the diagram…                                                                         | Read                                                   |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| includes any product, service, or brand (icons and logos)                                 | [references/icons.md](references/icons.md)             |
| needs step numbers, a `How it works` note for not obvious pieces, or emphasis on one path | [references/callouts.md](references/callouts.md)       |
| is AWS, or a network or topology diagram                                                  | [references/aws-network.md](references/aws-network.md) |
| colors any group, boundary, or line                                                       | [references/palette.md](references/palette.md)         |
| goes into a doc, or a doc might need one                                                  | [references/docs.md](references/docs.md)               |
| has groups, Full detail cards, a fan-out, an emphasis path, or a Brief/Full pair          | [references/layout.md](references/layout.md)           |

## Verify before handing back

A diagram that looks fine in the XML often isn't once it renders, so check it both ways.

1. Run `embed-icons.py` first, so the check sees the final icons, then run the layout check and fix everything it flags:

   ```bash
   python3 <this skill dir>/scripts/check-layout.py <name>.drawio
   ```

   It flags duplicate cell IDs, a key outside the bottom-left corner, stacked shapes off a shared center line, children that spill past their container's border, mirrored branches that bend at different points, lines that run through a shape or hug its edge (keep lanes 20px clear), edge jogs (line up the two ends exactly, or add waypoints if the bend is on purpose), uneven padding, an off center title or subtitle, content closer than 60px to the heading, low contrast, lines through labels, edge labels on borders or on each other, logos without the standard tile, account labels not in `Name (ID)` form, and icon labels moved off the bottom with no line there, named CDN or edge vendors drawn as the internet cloud, and concern-page edges missing from Full.

2. Before the first render, write down the reading path you planned: entry → … → exit.

3. Render every page in both themes, and read each PNG. `-p` is 1-based.

   ```bash
   drawio -x -f png -b 10 -p <page> --theme <light|dark> -o /tmp/<name>.png <name>.drawio
   ```

   If the `drawio` CLI is missing (`brew install --cask drawio`), say that you skipped the render.

4. Check that the render follows the reading path. Name every defect you see, or say why each of these passes, and fix them in this order: overlaps, lines through boxes, crossings, crowded or wrapped labels, and edges that end in mid-air. Move a node before you add waypoints.

5. Stop after 2 rounds of fixes, and report what's left. Past that point you're nudging blindly.

6. Give it a feng shui pass. If it looks busy, cut or shorten lines before you polish anything else.

7. Sweep every plain box and icon-less card. Each one is either a generic concept (keep it plain) or gets its icon: containers get the runtime logo, host agents their product logo (icons.md).

8. In a multipage file, when a fact changes on one page (a hop, port, or name), update every page that shows that node or edge.

9. Confirm no `image=https` remains (see [references/icons.md](references/icons.md)). The `Updated` date is today. The subtitle's data date comes from the source, so the two can differ.

Export only when asked, and keep the diagram embedded so it stays editable:

```bash
drawio -x -e -f <png|svg|pdf> -b 10 -o <name>.drawio.<ext> <name>.drawio
```
