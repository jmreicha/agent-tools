# Layout recipes

These are the measurements and patterns that keep diagrams consistent from one to the next.
Build them with `scripts/drawio_lib.py` (`Diagram`, `group`, `card`, `edge`, `port`, `save_pages`).
Its docstring has a usage example, and `python3 drawio_lib.py` runs its self-check.

## Full-detail card

- Use `Diagram.card(id, name, facts, icon, x, y, w, h, parent)`: the icon is 36×36 at the left, the name bold, and the facts in 10px gray, one per line.
- Leave `h` out and `card()` sizes it from the fact count (64px minimum, +12px per fact).
- Rows step 80–90px. Two columns are 480px wide with a 40px gap between them.
- Icon labels on Brief stay under ~20 characters, so they fit under a 60px icon. Long IDs belong on Full cards.
- Plain lists (subnets, VLANs) go in a `LIST` text block inside their group, not in a card: one line per item, in the format `AZ  CIDR  name`.

## Spacing

- Groups pad 35px above their first content, which leaves room for the label, and 30px below. Every sibling of the same kind matches.
- Nested AWS groups sit 35px inside their parent at the top, which leaves room for the label, and 20px at the sides and bottom.
- Boundaries are containers (`d.boundary(..., icon=...)`): put their children inside with `parent=`. Their label row takes 40px, so content starts 60px below the top.
- A gateway (IGW) sits inside the VPC's left margin. Widen the VPC so both margins stay equal.
- Keep about 40px of clear space between a fan-out and any other label.

## Ports and straight lines

- Edge labels sit at the middle of the edge. On a long route, move them off borders and trunks with `label_at` (-1 to 1), or use free text placed by hand.
- Compute ports from geometry, never guess: `entry=(0, d.port(target, "y", source_center_y))`.
- Line up a source's center with its target's center whenever a straight line is possible.
- Stack right-hand destinations top to bottom in the same order as their source exits (Internet outbound, then endpoints, then peers), so the lines never cross.
- Internet inbound sits on the left and Internet outbound on the right, both as clouds.

## Fan-out

When 3 or more edges go from one source to a column of targets:
- Give every edge the same exit port, and center the target column on it.
- Use `d.fanout(prefix, src, targets, trunk_x)`. Put `trunk_x` 50px before the targets: never on a container border, never under a label.
- One trunk branching cleanly is the exception to "never merge edges". Skip zip ties (`shape=tie`).

## Fan-in

- The mirror of fan-out: 3 or more sources in a column merge on one trunk into one port, with `d.fanin(prefix, sources, tgt, trunk_x)`.

## Emphasis path

- The red path gets its own straight route, crossing no other edge or box.
- Reorder nodes to make that possible: put the emphasized target first in its row, and line up Internet, the gateway, and the target on one center line.
- Other traffic leaves the shared node from a different side, such as the top.
- A note placed right next to the path needs no link.
- To emphasize an icon-only node (Brief), make its label red and bold and color the path into it. Never recolor the icon.

## Brief and Full pages

- Draw Full first. Make Brief by collapsing it: counts instead of lists, shortened IDs, icons instead of cards.
- Keep the same relative positions on both pages, so switching pages doesn't jump around.
- Write both pages with `save_pages(path, [("Brief", brief, w, h), ("Full", full, w, h)])`.

## Reading a source image

- Crop low-resolution PNGs into regions and scale each 2×: `sips -c <h> <w> --cropOffset <y> <x> in.png --out part.png && sips -z <2h> <2w> part.png`. Use offsets of at least 1, because `sips` ignores `0 0`.
- Transcribe IDs exactly, and list every uncertain value for the user to check.
