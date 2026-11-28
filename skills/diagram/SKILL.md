---
name: diagram
description: Use whenever the answer includes any diagram, including a short Mermaid flowchart or sequence diagram for a README or chat reply. Covers drawing, sketching, or visualizing architecture, infrastructure, network and traffic paths, request flows, pipelines, and systems as draw.io (.drawio), Excalidraw, or Mermaid, exporting a diagram to PNG, SVG, or PDF, and spotting when an existing doc would read better with a diagram.
version: 1.2.0
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

## Style

- Boxes are rounded, 120×60, with no fill. Arrows are orthogonal with sharp right-angle bends, one head, and flow left to right. No diagonals, curves, double heads, fills, shadows, gradients, swimlanes, or decorative color.
- The internet is a cloud shape. A named CDN or edge provider gets its vendor icon instead.
- Every boundary is solid, around a real construct only (cluster, environment, trust zone), and rarely more than 1-2. Dashed lines mean planned, async, optional, or a virtual link. Trust boundaries on a Security page are dashed.
- Add a key only when 3 or more symbols need decoding. With 1-2, label the edges.
- Text is 12pt, needs 4.5:1 contrast, and any color that matters gets a `light-dark()` pair so dark mode works. Never hardcode black or white.
- Title at 36pt centered on the main box, `Updated YYYY-MM-DD` in the bottom-right corner.

Build diagrams with `python3` and `<this skill dir>/scripts/drawio_lib.py`, which applies these styles (cards, AWS groups, ports, keys, notes, multipage). Hand edit XML only for small fixes. [references/style.md](references/style.md) has every exact style, arrow port, contrast, layout, and dark mode rule.

## Read when relevant

| When the diagram…                                                                         | Read                                                   |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| includes any product, service, or brand (icons and logos)                                 | [references/icons.md](references/icons.md)             |
| needs step numbers, a `How it works` note for not obvious pieces, or emphasis on one path | [references/callouts.md](references/callouts.md)       |
| is AWS, or a network or topology diagram                                                  | [references/aws-network.md](references/aws-network.md) |
| colors any group, boundary, or line                                                       | [references/palette.md](references/palette.md)         |
| is draw.io and you hand-write a style, or a render or check finding needs the exact rule  | [references/style.md](references/style.md)             |
| goes into a doc, or a doc might need one                                                  | [references/docs.md](references/docs.md)               |
| has groups, Full detail cards, a fan-out, an emphasis path, or a Brief/Full pair          | [references/layout.md](references/layout.md)           |

## Verify before handing back

A diagram that looks fine in the XML often isn't once it renders, so check it both ways.

1. Run `embed-icons.py` first, so the check sees the final icons, then run the layout check and fix everything it flags:

   ```bash
   python3 <this skill dir>/scripts/check-layout.py <name>.drawio
   ```

   It flags overlaps, off-center or uneven layout, low contrast, and lines through shapes or labels, among others.

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
