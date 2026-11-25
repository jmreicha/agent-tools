# Layout recipes

These are the measurements and patterns that keep diagrams consistent from one to the next.
Build them with `scripts/drawio_lib.py` (`Diagram`, `group`, `card`, `edge`, `port`, `save_pages`).
Its docstring has a usage example, and `python3 drawio_lib.py` runs its self check.

## Full detail card

- Use `Diagram.card(id, name, facts, icon, x, y, w, h, parent)`: the icon is 36×36 at the left, the name bold, and the facts at 10px in the default color, one per line.
- Leave `h` out and `card()` sizes it from the fact count (64px minimum, +15px per fact, which is how tall a 10px line renders).
- Rows step 80-90px. Two columns are 480px wide with a 40px gap between them.
- Icon labels on Brief use the real name in its shortest unique form (`prod-us-blue-public`, not `ALB`). Long IDs belong on Full cards.
- Plain lists (subnets, VLANs) go in a `LIST` text block inside their group, not in a card: one line per item, in the format `AZ  CIDR  name`.

## Spacing

- A group with only icons or cards inside pads 35px above its first content, which leaves room for the label, and 30px below. A group that holds other groups uses the nested rule below. Either way, every sibling of the same kind matches. Subnets and SG boxes share an AWS icon, so check-layout.py treats them as one kind: give both the same top and bottom padding (50 and 30 work).
- Boxes inside a subnet (SG boxes) pad their children 50px at the top and 30px at the bottom, the same as the subnets around them. The 60px rule below is for labeled groups nesting in their parent.
- Nested AWS groups (Cloud > Region > VPC > subnet) sit 60px inside their parent at the top, which leaves room for the label, 30px at the sides, and 40px at the bottom. Tighter nesting stacks the labels into a cluttered staircase.
- Boundaries are containers (`d.boundary(..., icon=...)`): put their children inside with `parent=`. Their label row takes 40px, so content starts 60px below the top.
- A gateway (IGW) sits inside the VPC's left margin. Widen the VPC so both margins stay equal.
- Keep about 40px of clear space between a fan-out and any other label.
- A labeled straight edge between two side-by-side nodes needs a gap of at least the label's width plus 20px, so it clears both ends. Width is about 6px per character of the longest line at 11pt (`anomaly alerts` → 105px).

## Ports and straight lines

- Edge labels sit at the middle of the edge. On a long route, move them off borders and trunks with `label_at` (-1 to 1), or use free text placed by hand.
- Compute ports from geometry. Don't guess: `entry=(0, d.port(target, "y", source_center_y))`.
- Line up a source's center with its target's center whenever a straight line is possible.
- Stack right-hand destinations top to bottom in the same order as their source exits (Internet outbound, then endpoints, then peers), so the lines never cross.
- Internet inbound sits on the left and Internet outbound on the right, both as clouds.
- Stores and branches sit centered directly above or below their owner, all on the same side.
- A return edge (response, callback, ack) runs on an empty side, not back along the forward route.

## Fan-out

When 3 or more edges go from one source to a column of targets:

- Give every edge the same exit port, and center the target column on it.
- A fan-out label with no room: widen the gap first. If it's still crowded, put the port in the target's label (`ALB · HTTPS 443`) and leave the branch unlabeled.
- Use `d.fanout(prefix, src, targets, trunk_x)`. Put `trunk_x` 50px before the targets. Keep it off container borders and out from under labels.
- One trunk branching cleanly is the exception to "never merge edges". Skip zip ties (`shape=tie`).

## Fan-in

- The mirror of fan-out: 3 or more sources in a column merge on one trunk into one port, with `d.fanin(prefix, sources, tgt, trunk_x)`.

## Emphasis path (not network diagrams)

- The red path gets its own straight route, crossing no other edge or box.
- Reorder nodes to make that possible: put the emphasized target first in its row, and line up Internet, the gateway, and the target on one center line.
- Other traffic leaves the shared node from a different side, such as the top.
- A note placed right next to the path needs no link.
- To emphasize an icon-only node (Brief), make its label red and bold and color the path into it. Never recolor the icon.

## Brief, concern, and Full pages

- Collect the facts before you draw: one table in the build script holds every node and edge (name, ID, hop, port, protocol, rule, role). Every page draws from it, so a fact found late reaches every page.
- Order pages from least to most detail: Brief, then concern pages from narrowest to widest zoom, then Full.
- Full is the union of the concern pages' nodes and edges: every path on a concern page is on Full too. check-layout.py flags a concern-page edge missing from Full.
- Full has no Node-page detail (containers, host agents, volumes). It stays at the network and service zoom, and the Node page is the zoom in.
- **Detail tables** (SG rules, IAM policies, any list a reader scans row by row) all share one layout. `Diagram.detail` puts the icon top-left, the bold title (`name (id)`), a blank line, then 10px rows, with equal room above and below the text. Rows a reader compares column by column (SG rules) are tuples, which render as a borderless table with a bold header row. Notes that aren't rows go as plain lines above the table, and a string among the table rows spans it as a section heading. IAM role cards are an `action | resource` table: `arrow_rows` splits `action → resource` lines, keeps the trust lines above, and makes each policy name a heading. When the grid is wider than its container, widen the container (the account) instead of shrinking the cards. `Diagram.detail_grid` lays out the set:
  - every card gets the widest card's fitted width, so titles stay on one line without trailing space
  - table columns share one set of widths across the grid, so columns line up from card to card
  - each card stacks under the shortest column, so short cards pack together instead of leaving row gaps
  - the grid centers in its container, and its heading sits flush with the grid's left edge
  Use fewer columns rather than wrapping a title. SG cards come from `sg_rows` (inbound before outbound) and take the SG color.
- Detail tables (SG rule cards, IAM policy cards) live only on the concern page they belong to: SG rules on Network, role policies at the bottom of Security. Full keeps the SG boxes and role names, not the tables, or it gets too busy to read.
- Make Brief by collapsing Full: counts instead of lists, shortened IDs, icons instead of cards.
- Keep the same relative positions on every page, so switching pages doesn't jump around.
- Write both pages with `save_pages(path, [("Brief", brief, w, h), ("Full", full, w, h)])`.

## Reading a source image

- Crop low-resolution PNGs into regions and scale each 2×: `sips -c <h> <w> --cropOffset <y> <x> in.png --out part.png && sips -z <2h> <2w> part.png`. Use offsets of at least 1, because `sips` ignores `0 0`.
- Transcribe IDs exactly, and list every uncertain value for the user to check.
- Never add a component the source doesn't show. Ask about it instead. Hand back a short change record: what you merged, collapsed, renamed, or dropped.
- Keep the source's color coding for every line you draw. The key lists only symbols that appear on this diagram. Drop source legend rows with no matching line. Use the line palette in aws-network.md. When the emphasis red would clash with a source color, the source color wins on lines, and red stays on the box and its note.
