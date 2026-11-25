#!/usr/bin/env python3
"""Flag layout defects: edges with a small jog, uneven group padding, an
off-center title, text or lines below WCAG contrast, lines through labels, and
edge labels on borders or on each other, image icons without the standard tile,
icon labels moved off the bottom with no line there, and badges on labels.
Usage: check-layout.py <file.drawio>
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawio_lib import contrast  # noqa: E402

# Offsets under this read as a mistake, not an intended bend.
JOG = 40
CLOUD_PORTS = {(0, 0.5), (1, 0.5), (0.5, 0), (0.5, 1)}


def geometry(cells):
    """Absolute (x, y, w, h) per vertex id; children are relative to parents."""
    out = {}

    def resolve(cid):
        if cid in out:
            return out[cid]
        c = cells[cid]
        g = c.find("mxGeometry")
        if g is None or c.get("vertex") != "1":
            out[cid] = None
            return None
        x, y = float(g.get("x", 0)), float(g.get("y", 0))
        parent = cells.get(c.get("parent"))
        if parent is not None and parent.get("vertex") == "1":
            p = resolve(parent.get("id"))
            if p:
                x, y = x + p[0], y + p[1]
        out[cid] = (x, y, float(g.get("width", 0)), float(g.get("height", 0)))
        return out[cid]

    for cid in cells:
        resolve(cid)
    return out


def style(s):
    return dict(kv.split("=", 1) for kv in str(s or "").split(";") if "=" in kv)


def port(box, fx, fy):
    x, y, w, h = box
    return x + w * fx, y + h * fy


def check(path):
    # IDs repeat across pages, so check each page on its own.
    pages = list(ET.parse(path).iter("diagram"))
    out = []
    for page in pages:
        prefix = f"[{page.get('name')}] " if len(pages) > 1 else ""
        out += [prefix + p for p in check_page(page)]
    return out + full_union(pages)


def node_name(value):
    """A node's name: the first line of its label, without markup."""
    return re.sub(r"<[^>]+>", "", re.split(r"<br\s*/?>", value or "")[0]).strip()


def named_edges(page):
    cells = {c.get("id"): c for c in page.iter("mxCell")}
    names = {i: node_name(c.get("value")) for i, c in cells.items() if c.get("vertex") == "1"}
    edges = {(names.get(c.get("source")), names.get(c.get("target")))
             for c in cells.values() if c.get("edge") == "1"}
    return {n for n in names.values() if n}, {e for e in edges if all(e)}


def reaches(edges, src, tgt):
    """True if Full connects src to tgt, directly or through hops a concern page skipped."""
    seen, todo = {src}, [src]
    while todo:
        n = todo.pop()
        for a, b in edges:
            if a == n and b not in seen:
                if b == tgt:
                    return True
                seen.add(b)
                todo.append(b)
    return False


def full_union(pages):
    """Full combines the concern pages, so a concern-page edge whose two ends are on Full
    must be on Full too. Brief collapses on purpose, so it's exempt."""
    by_name = {p.get("name"): p for p in pages}
    if "Full" not in by_name:
        return []
    full_nodes, full_edges = named_edges(by_name["Full"])
    out = []
    for name, page in by_name.items():
        if name in ("Full", "Brief"):
            continue
        for src, tgt in sorted(named_edges(page)[1]):
            if src in full_nodes and tgt in full_nodes and not reaches(full_edges, src, tgt):
                out.append(f"[{name}] Full is missing {src} -> {tgt}; Full combines every concern page")
    return out


def check_page(page):
    cells = {c.get("id"): c for c in page.iter("mxCell")}
    geo = geometry(cells)
    problems, paths = [], {}
    # The dict above keeps only the last cell per id, so catch repeats first.
    ids = [c.get("id") for c in page.iter("mxCell")]
    problems += [f"{i}: duplicate cell id" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for c in cells.values():
        if c.get("edge") != "1":
            continue
        src, tgt = geo.get(c.get("source")), geo.get(c.get("target"))
        if not src or not tgt:
            continue
        st = style(c.get("style"))
        ex, ey = float(st.get("exitX", 0.5)), float(st.get("exitY", 0.5))
        nx, ny = float(st.get("entryX", 0.5)), float(st.get("entryY", 0.5))
        name = f"{c.get('id')}: {c.get('source')} -> {c.get('target')}"
        # A cloud's outline only touches its box at the middle of each side.
        for end, fx, fy in (("source", ex, ey), ("target", nx, ny)):
            if style(cells[c.get(end)].get("style")).get("shape") == "cloud" and (fx, fy) not in CLOUD_PORTS:
                problems.append(f"{name}: {end} cloud port ({fx:g},{fy:g}) is not a side midpoint")
        pts = [port(src, ex, ey)]
        g = c.find("mxGeometry")
        arr = g.find("Array") if g is not None else None
        if arr is not None:
            pts += [(float(p.get("x", 0)), float(p.get("y", 0))) for p in arr.iter("mxPoint")]
        pts.append(port(tgt, nx, ny))
        paths[c.get("id")] = pts
        # Every segment should be exactly straight; a small offset renders as a jog.
        # End segments only count the offset across the port's direction.
        last = len(pts) - 2
        for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
            dx, dy = abs(ax - bx), abs(ay - by)
            fx, fy = (ex, ey) if i == 0 else (nx, ny)
            if (i == 0 or i == last) and fx in (0, 1):
                off = dy
            elif (i == 0 or i == last) and fy in (0, 1):
                off = dx
            else:
                off = min(dx, dy)
            if 1 <= off < JOG:
                problems.append(f"{name} is {off:g}px out of line")
                break
    return (problems + padding(cells, geo) + title(cells, geo) + key_corner(cells, geo) + columns(cells, geo) + spills(cells, geo) + mirrors(cells, paths) + hugs(cells, geo, paths) + contrasts(cells, geo)
            + crossings(cells, geo, paths) + tiles(cells, geo) + side_labels(cells) + badges(cells, geo) + account_labels(cells) + group_labels(cells)
            + vendor_clouds(cells) + iconless(cells))


# Named edge/CDN vendors that have icons; the cloud shape is only the public internet.
CDN_VENDORS = ("Cloudflare", "CloudFront", "Akamai", "Fastly", "Imperva", "Zscaler")


# Labels that name a product or construct with a draw.io shape or logo (icons.md).
ICONED = [
    (r"docker|container|compose", "Docker"), (r"\botel\b|opentelemetry", "OpenTelemetry"),
    (r"new relic", "New Relic"), (r"honeycomb", "Honeycomb"), (r"datadog", "Datadog"),
    (r"grafana", "Grafana"), (r"prometheus", "Prometheus"), (r"kafka", "Kafka"), (r"redis", "Redis"),
    (r"postgres", "PostgreSQL"), (r"mysql", "MySQL"), (r"nginx", "NGINX"),
    (r"kubernetes|\bk8s\b(?!-)|\bpod\b|service ?account", "Kubernetes"), (r"\beks\b(?!-)", "EKS"),
    (r"peer(ed|ing)|\bpcx-", "VPC peering"), (r"\bvpc\b", "VPC"),
    (r"\biam\b|\brole\b|polic(y|ies)", "IAM"), (r"\bs3\b|bucket", "S3"), (r"lambda", "Lambda"),
    (r"\bebs\b|\bvolume\b|\bgp3\b", "EBS"), (r"nat gateway", "NAT gateway"),
    (r"load balancer|\b[an]lb\b", "Elastic Load Balancing"), (r"route ?53", "Route 53"),
    (r"secrets manager", "Secrets Manager"), (r"systems manager|\bssm\b", "Systems Manager"),
]


def iconless(cells):
    """A plain box, or a card without its icon, whose label names something that has an icon."""
    out = []
    for i, c in cells.items():
        st = style(c.get("style"))
        raw = str(c.get("style") or "")
        if (c.get("vertex") != "1" or not raw.startswith("rounded=1;") or "shape" in st
                or st.get("container") == "1" or st.get("spacing") == "8"):
            continue  # not a node box: icons, groups, boundaries, notes
        card = "spacingLeft" in st
        if card and f"{i}_i" in cells:
            continue
        label = c.get("value") or ""
        text = node_name(label) if card else re.sub(r"<[^>]+>", " ", label)
        for pat, product in ICONED:
            if re.search(pat, text, re.I):
                out.append(f"{i}: box names {product}; give it its icon (icons.md)")
                break
    return out


def vendor_clouds(cells):
    """A cloud shape labeled with a real CDN/edge product hides it as generic internet."""
    out = []
    for i, c in cells.items():
        if style(c.get("style")).get("shape") != "cloud":
            continue
        label = (c.get("value") or "").lower()
        for v in CDN_VENDORS:
            if v.lower() in label:
                out.append(f"{i}: {v} drawn as a cloud; use its vendor icon (icons.md)")
                break
    return out



DETAIL = re.compile(r"\b(?:vpc|subnet|rtb|sg|igw|nat|pcx|vpce|eni|i)-[0-9a-f]{4,}\b|\b\d{1,3}(?:\.\d{1,3}){3}(?:/\d+)?|\b\d{12}\b")


def group_labels(cells):
    """Group and boundary labels read `Name (detail, detail)`, like accounts: IDs, CIDRs, and
    qualifiers go in parens, not run on or split with ` · `."""
    out = []
    for i, c in cells.items():
        st = str(c.get("style"))
        if "group_account" in st:
            continue  # account_labels covers these
        if "grIcon=" in st or "container=1" in st:
            v = c.get("value") or ""
            if not v:  # Diagram.boundary puts the label in its own `<id>_l` text cell
                lab = cells.get(f"{i}_l")
                v = lab.get("value") if lab is not None else ""
            v = re.sub(r"<[^>]+>", " ", v or "").strip()
            bare = re.sub(r"\([^)]*\)", "", v)
            if " · " in bare or DETAIL.search(bare):
                out.append(f"{i}: label {v!r}; put details in parens: `Name (id, 10.0.0.0/16)`")
    return out


def account_labels(cells):
    """Account groups read `Name (123456789012)` or the bare ID; the group already says account."""
    out = []
    for i, c in cells.items():
        if "group_account" not in str(c.get("style")):
            continue
        v = re.sub(r"<[^>]+>", " ", c.get("value") or "").strip()
        if re.search(r"\baccount\b", v, re.I) or not re.fullmatch(r"\d{12}|.+ \(\d{12}\)", v):
            out.append(f"{i}: account label {v!r}; use `Name (123456789012)`")
    return out


def badges(cells, geo):
    """Step badges sit on a node's corner, never on its label."""
    boxes = labels(cells, geo)
    out = []
    for i, c in cells.items():
        b = geo.get(i)
        if not b or not str(c.get("style")).startswith("ellipse;") or "fontStyle=1" not in str(c.get("style")):
            continue
        for j, (lx, ly, lw, lh) in boxes.items():
            if b[0] < lx + lw and lx < b[0] + b[2] and b[1] < ly + lh and ly < b[1] + b[3]:
                out.append(f"{i}: badge on {j}'s label; move it to a free corner")
    return out

def side_labels(cells):
    """A moved icon label widens its box; it's only for a line at the icon's bottom."""
    bottom = set()
    for c in cells.values():
        st = style(c.get("style"))
        if c.get("edge") == "1":
            if st.get("exitY") == "1":
                bottom.add(c.get("source"))
            if st.get("entryY") == "1":
                bottom.add(c.get("target"))
    out = []
    for i, c in cells.items():
        st = style(c.get("style"))
        moved = st.get("verticalLabelPosition") == "top" or st.get("labelPosition") in ("left", "right")
        if moved and c.get("value") and i not in bottom:
            out.append(f"{i}: label is beside the icon; keep it below and bring the line in from a side")
    return out


def tiles(cells, geo):
    """Image icons (not screenshots) must carry embed-icons.py's standard tile."""
    out = []
    for i, c in cells.items():
        st, b = style(c.get("style")), geo.get(i)
        if st.get("shape") == "image" and b and max(b[2], b[3]) <= 100 and st.get("iconTile") != "1":
            out.append(f"{i}: icon has no tile; use a library shape, or image() + embed-icons.py (icons.md)")
    return out


def padding(cells, geo):
    """Containers of the same kind (same AWS group icon or shape) should pad
    their children the same way, or sibling groups look uneven."""
    kids = {}
    for c in cells.values():
        if geo.get(c.get("id")) and c.get("parent") in geo and geo[c.get("parent")]:
            kids.setdefault(c.get("parent"), []).append(geo[c.get("id")])
    kinds = {}
    for pid, boxes in kids.items():
        st = style(cells[pid].get("style"))
        if st.get("fixedLayout") == "1":
            continue  # drawio_lib's Diagram.fixed: padding is deliberate
        kind = st.get("grIcon") or st.get("shape") or "box"
        _, y, _, h = geo[pid]
        pad = (min(b[1] for b in boxes) - y, y + h - max(b[1] + b[3] for b in boxes))
        kinds.setdefault(kind, []).append((pid, pad))
    out = []
    # Child groups must sit centered in their parent (equal left/right margins).
    for pid, boxes in kids.items():
        groups = [geo[c.get("id")] for c in cells.values() if c.get("parent") == pid and c.get("id") in kids]
        if groups and style(cells[pid].get("style")).get("fixedLayout") != "1":
            x, _, w, _ = geo[pid]
            left, right = min(b[0] for b in groups) - x, x + w - max(b[0] + b[2] for b in groups)
            if abs(left - right) >= 2:
                out.append(f"{pid}: child groups off-center (left {left:g}, right {right:g})")
    for kind, items in kinds.items():
        for side, name in ((0, "top"), (1, "bottom")):
            vals = {pid: round(p[side]) for pid, p in items}
            if max(vals.values()) - min(vals.values()) >= 2:
                out.append(f"{kind} {name} padding differs: " + ", ".join(f"{k}={v}" for k, v in vals.items()))
    return out


def title_axis(cells, geo):
    """(title id, subtitle id, center x, gap below the heading) or None.
    The main box is the widest container, when it spans half the content or more;
    otherwise the heading centers on the content's bounding box."""
    top = {i: geo[i] for i, c in cells.items() if geo.get(i) and c.get("parent") == "1"}
    t = next((i for i in top if style(cells[i].get("style")).get("fontSize") == "36"), None)
    if not t:
        return None
    tx, ty, tw, th = top[t]
    sub = next((i for i, (x, y, w, h) in top.items() if i != t and ty + th - 10 <= y <= ty + th + 40
                and "text" in str(cells[i].get("style"))), None)
    head_bottom = top[sub][1] + top[sub][3] if sub else ty + th
    body = {i: b for i, b in top.items() if i not in (t, sub)
            and not str(cells[i].get("value") or "").startswith("Updated")
            and "spacing=8;fontSize=11" not in str(cells[i].get("style"))}  # notes and keys sit beside the body
    if not body:
        return None
    left = min(b[0] for b in body.values())
    right = max(b[0] + b[2] for b in body.values())
    boxes = [b for i, b in body.items() if style(cells[i].get("style")).get("container") == "1"
             or any(c.get("parent") == i for c in cells.values())]
    main = max(boxes, key=lambda b: b[2], default=None)
    axis = main[0] + main[2] / 2 if main and main[2] >= (right - left) / 2 else (left + right) / 2
    return t, sub, axis, min(b[1] for b in body.values()) - head_bottom


def hugs(cells, geo, paths):
    """A line segment through a card or icon (not its own ends), or within 10px of running along its top or
    bottom edge, reads as tangled. Give the lane room: 20px or more from any shape it passes."""
    shapes = {i: geo[i] for i, c in cells.items() if c.get("vertex") == "1" and geo.get(i)
              and "container" not in str(c.get("style")) and "text" not in str(c.get("style"))
              and not any(k.get("parent") == i for k in cells.values()) and geo[i][2] >= 40 and geo[i][3] >= 40}
    out = []
    for e, pts in paths.items():
        ends = (cells[e].get("source"), cells[e].get("target"))
        hit = None
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            for i, (x, y, w, h) in shapes.items():
                if i in ends or hit:
                    continue
                if abs(ay - by) < 1 and min(ax, bx) < x + w - 5 and max(ax, bx) > x + 5:  # horizontal
                    if y + 5 < ay < y + h - 5:
                        hit = f"{e}: line runs through {i}"
                    elif abs(ay - y) <= 10 or abs(ay - (y + h)) <= 10:
                        hit = f"{e}: line runs along {i}'s edge; give the lane 20px"
                elif abs(ax - bx) < 1 and min(ay, by) < y + h - 5 and max(ay, by) > y + 5:  # vertical
                    if x + 5 < ax < x + w - 5:
                        hit = f"{e}: line runs through {i}"
                    elif abs(ax - x) <= 10 or abs(ax - (x + w)) <= 10:
                        hit = f"{e}: line runs along {i}'s edge; give the lane 20px"
        if hit:
            out.append(hit)
    return out


def mirrors(cells, paths):
    """Two branches out of one side (exit 0.25 and 0.75) should turn at the same distance, or they look uneven."""
    sides = {}
    for i, pts in paths.items():
        st = style(cells[i].get("style"))
        ex, ey = float(st.get("exitX", 0.5)), float(st.get("exitY", 0.5))
        if ex in (0, 1) and ey != 0.5:
            sides.setdefault((cells[i].get("source"), ex), []).append((i, ey, pts))
        elif ey in (0, 1) and ex != 0.5:
            sides.setdefault((cells[i].get("source"), "y", ey), []).append((i, ex, pts))
    out = []
    for key, items in sides.items():
        horiz = key[1] != "y"
        for a, fa, pa in items:
            for b, fb, pb in items:
                straight = lambda p: len(p) == 2 and abs(p[0][1 if horiz else 0] - p[1][1 if horiz else 0]) < 1
                if a < b and abs(fa + fb - 1) < 0.01 and not (straight(pa) or straight(pb)):
                    ba = pa[1][0 if horiz else 1] if len(pa) > 2 else None
                    bb = pb[1][0 if horiz else 1] if len(pb) > 2 else None
                    if ba != bb:
                        out.append(f"{b}: mirrors {a} but bends at {bb} vs {ba}; give both the same waypoint {'x' if horiz else 'y'}")
    return out


def spills(cells, geo):
    """A child past its container's border reads as outside it: widen the container instead."""
    out = []
    for i, c in cells.items():
        p, b = c.get("parent"), geo.get(i)
        if c.get("vertex") == "1" and b and geo.get(p):
            px, py, pw, ph = geo[p]
            if b[0] < px - 1 or b[1] < py - 1 or b[0] + b[2] > px + pw + 1 or b[1] + b[3] > py + ph + 1:
                out.append(f"{i}: spills past {p}'s border; widen {p} or move it in")
    return out


def columns(cells, geo):
    """A shape stacked over another (x ranges overlap, nothing between) should share its center line."""
    shapes = {i: geo[i] for i, c in cells.items() if c.get("vertex") == "1" and geo.get(i)
              and "text" not in str(c.get("style")) and "container" not in str(c.get("style"))
              and not any(k.get("parent") == i for k in cells.values())
              and not str(c.get("value") or "").startswith("<b>")  # skip cards/notes: they stack by left edge
              and 40 <= geo[i][2] <= 200 and 40 <= geo[i][3] <= 200}  # node-sized: not badges, key rows, screenshots
    # Any shape between two breaks the stack, cards and groups included, not just nodes.
    blockers = {i: geo[i] for i, c in cells.items() if c.get("vertex") == "1" and geo.get(i) and "text" not in str(c.get("style"))}
    out = []
    for a, (ax, ay, aw, ah) in shapes.items():
        for b, (bx, by, bw, bh) in shapes.items():
            if cells[a].get("parent") != cells[b].get("parent") or by <= ay + ah or not (ax < bx + bw and bx < ax + aw):
                continue
            between = any(o not in (a, b) and oy >= ay + ah and oy + oh <= by and ox < max(ax + aw, bx + bw) and ox + ow > min(ax, bx)
                          for o, (ox, oy, ow, oh) in blockers.items())
            off = (bx + bw / 2) - (ax + aw / 2)
            if not between and 2 <= abs(off) <= aw / 2 + bw / 2 - 1:
                out.append(f"{b}: off {a}'s center line by {off:g}px; stacked shapes share one center")
    return out


def key_corner(cells, geo):
    """Readers look for the key in one place: under the lowest shape, flush with the leftmost."""
    top = {i: geo[i] for i, c in cells.items() if geo.get(i) and c.get("parent") == "1"}
    keys = [i for i in top if "keyNote=1" in str(cells[i].get("style"))
            or str(cells[i].get("value") or "").startswith("<b>Key</b>")]
    body = [b for i, b in top.items() if "spacing=8;fontSize=11" not in str(cells[i].get("style"))
            and style(cells[i].get("style")).get("fontSize") != "36" and "text" not in str(cells[i].get("style"))
            and not str(cells[i].get("value") or "").startswith("Updated")]
    inside = lambda b, k: k[0] <= b[0] and b[0] + b[2] <= k[0] + k[2] and k[1] <= b[1] and b[1] + b[3] <= k[1] + k[3]
    body = [b for b in body if not any(inside(b, top[k]) for k in keys)]  # the key's own rows
    if not keys or not body:
        return []
    left, bottom = min(b[0] for b in body), max(b[1] + b[3] for b in body)
    out = [f"{k}: title the key by what it decodes (`Line types`), not just Key"
           for k in keys if str(cells[k].get("value") or "").strip() == "<b>Key</b>"]
    return out + [f"{k}: put the key in the bottom-left, 40px under the lowest shape at x={left:g}, y={bottom + 40:g}"
            for k in keys if abs(top[k][0] - left) > 10 or not bottom + 30 <= top[k][1] <= bottom + 60]


def title(cells, geo):
    found = title_axis(cells, geo)
    if not found:
        return []
    t, sub, axis, gap = found
    top = geo
    out = []
    for i, name in ((t, "title"), (sub, "subtitle")):
        if i and abs(top[i][0] + top[i][2] / 2 - axis) >= 2:
            out.append(f"{i}: {name} off-center by {top[i][0] + top[i][2] / 2 - axis:g}px (center on x={axis:g})")
    if gap < 60:
        out.append(f"content starts {gap:g}px below the subtitle (or title); use 60px+")
    return out


HEX = r"#[0-9A-Fa-f]{6}"


def pair(v):
    """(light, dark) from #RRGGBB or light-dark(a,b); None for none/default."""
    m = re.fullmatch(rf"light-dark\(({HEX}),\s*({HEX})\)", v or "")
    if m:
        return m.group(1), m.group(2)
    return (v, v) if re.fullmatch(HEX, v or "") else None


def contrasts(cells, geo):
    """WCAG: text 4.5:1 (3:1 at 18pt+, or 14pt+ bold), lines 3:1 against the page.
    Light mode uses the real fill behind the text; dark mode only checks text with
    no filled background, because draw.io darkens fills by an amount we can't know."""
    out = []
    for i, c in cells.items():
        st, val = style(c.get("style")), str(c.get("value") or "")
        if c.get("edge") == "1":
            col = pair(st.get("strokeColor"))
            if col:
                for theme, fg, page in (("light", col[0], "#FFFFFF"), ("dark", col[1], "#121212")):
                    r = contrast(fg, page)
                    if r < 3:
                        out.append(f"{i}: line contrast {r} in {theme} mode (need 3)")
            continue
        # draw.io only resolves light-dark() in style keys; inside label HTML it always
        # renders the light value, so dark mode gets dark text on a dark page.
        if re.search(r"color:\s*light-dark\(", val):
            out.append(f"{i}: inline light-dark() in the label; draw.io ignores it in dark mode. Use the fontColor style key")
            val = re.sub(r"color:\s*light-dark\([^)]*\)", "", val)
        colors = [pair(st.get("fontColor"))] + [pair(m) for m in re.findall(r"color:\s*(light-dark\([^)]*\)|#[0-9A-Fa-f]{6})", val)]
        colors = [x for x in colors if x]
        if not colors or not val.strip():
            continue
        size = float(st.get("fontSize", 12))
        need = 3 if size >= 24 or (size >= 18.5 and ("<b" in val or "fontStyle=1" in str(c.get("style")))) else 4.5
        bg, opacity, node = None, 1, c
        # A label outside its shape (icon labels) sits on the parent, not the shape's fill.
        if st.get("verticalLabelPosition") in ("top", "bottom") or st.get("labelPosition") in ("left", "right"):
            node = cells.get(c.get("parent"))
        while node is not None and bg is None:
            f = pair(style(node.get("style")).get("fillColor"))
            if f:
                bg, opacity = f, float(style(node.get("style")).get("fillOpacity", 100)) / 100
            node = cells.get(node.get("parent"))
        for fg in colors:
            r = contrast(fg[0], bg[0] if bg else "#FFFFFF", opacity)
            if r < need:
                out.append(f"{i}: text contrast {r} in light mode (need {need:g})")
            if bg is None and (r := contrast(fg[1], "#121212")) < need:
                out.append(f"{i}: text contrast {r} in dark mode (need {need:g})")
    return out


def text_box(value, size, cx=None, x=None, y=0):
    """Rough rendered extent of a label: ~0.55em per character, 1.25em per line."""
    lines = re.split(r"<br\s*/?>|\n", re.sub(r"<(?!br)[^>]+>", "", value))
    w, h = max(len(ln) for ln in lines) * size * 0.55, len(lines) * size * 1.25
    return (cx - w / 2 if x is None else x, y, w, h)


def labels(cells, geo):
    """{id: box} for text a line shouldn't cross: free text, icon labels, group labels."""
    out = {}
    for i, c in cells.items():
        b, val = geo.get(i), str(c.get("value") or "").strip()
        if not b or not val:
            continue
        st, raw = style(c.get("style")), str(c.get("style"))
        size = float(st.get("fontSize", 12))
        x, y, w, h = b
        if st.get("verticalLabelPosition") == "bottom":
            out[i] = text_box(val, size, cx=x + w / 2, y=y + h + 2)
        elif st.get("verticalLabelPosition") == "top":
            t = text_box(val, size, cx=x + w / 2)
            out[i] = (t[0], y - t[3] - 2, t[2], t[3])
        elif st.get("labelPosition") in ("left", "right"):
            t = text_box(val, size, cx=0, y=y + h / 2)
            lx = x + w + 2 if st["labelPosition"] == "right" else x - t[2] - 2
            out[i] = (lx, y + (h - t[3]) / 2, t[2], t[3])
        elif "mxgraph.aws4.group" in raw:
            out[i] = text_box(val, size, x=x + float(st.get("spacingLeft", 0)), y=y + 4)
        elif raw.startswith("text;"):
            t = text_box(val, size, cx=x + w / 2, y=y + (h - text_box(val, size, cx=0)[3]) / 2)
            out[i] = (x, t[1], t[2], t[3]) if st.get("align") == "left" else t
    return out


def hits(seg, box, pad=1):
    """True when an axis-aligned segment passes through a box's interior."""
    (ax, ay), (bx, by) = seg
    x, y, w, h = box
    x, y, w, h = x + pad, y + pad, w - 2 * pad, h - 2 * pad
    if ax != bx and ay != by:
        return False
    return min(ax, bx) < x + w and max(ax, bx) > x and min(ay, by) < y + h and max(ay, by) > y


def along(pts, frac):
    """Point at a fraction of a path's length."""
    segs = list(zip(pts, pts[1:]))
    lens = [abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in segs]
    left = sum(lens) * frac
    for (a, b), ln in zip(segs, lens):
        if left <= ln and ln:
            t = left / ln
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        left -= ln
    return pts[-1]


def crossings(cells, geo, paths):
    """Defects a render shows but the XML hides: a line through a label, an edge label
    on a group border, and two edge labels on top of each other."""
    out, texts, edge_labels = [], labels(cells, geo), {}
    for eid, pts in paths.items():
        for tid, box in texts.items():
            if any(hits(seg, box) for seg in zip(pts, pts[1:])):
                out.append(f"{eid}: line crosses {tid}'s label; reroute it or move the label")
        val = str(cells[eid].get("value") or "").strip()
        if val:
            g = cells[eid].find("mxGeometry")
            cx, cy = along(pts, (float(g.get("x", 0)) + 1) / 2)
            size = float(style(cells[eid].get("style")).get("fontSize", 11))
            t = text_box(val, size, cx=cx)
            edge_labels[eid] = (t[0], cy - t[3] / 2, t[2], t[3])
    def is_group(i, b):
        st = style(cells[i].get("style"))
        # Older diagrams draw a boundary as a large empty box instead of a container.
        plain = st.get("fillColor") == "none" and not cells[i].get("value") and min(b[2], b[3]) >= 150
        return st.get("container") == "1" or plain or any(c.get("parent") == i for c in cells.values())
    groups = {i: b for i, b in geo.items() if b and is_group(i, b)}
    for eid, (x, y, w, h) in edge_labels.items():
        for gid, (gx, gy, gw, gh) in groups.items():
            sides = [((gx, gy), (gx, gy + gh)), ((gx + gw, gy), (gx + gw, gy + gh)),
                     ((gx, gy), (gx + gw, gy)), ((gx, gy + gh), (gx + gw, gy + gh))]
            if any(hits(s, (x, y, w, h)) for s in sides):
                out.append(f"{eid}: label sits on {gid}'s border; move it with label_at")
    ids = sorted(edge_labels)
    for n, a in enumerate(ids):
        for b in ids[n + 1:]:
            ax, ay, aw, ah = edge_labels[a]
            bx, by, bw, bh = edge_labels[b]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                out.append(f"{a}: label overlaps {b}'s label")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    found = check(sys.argv[1])
    print("\n".join(found) or "ok")
    sys.exit(1 if found else 0)
