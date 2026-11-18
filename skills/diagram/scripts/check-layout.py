#!/usr/bin/env python3
"""Flag layout defects: edges with a small jog, uneven group padding, an
off-center title, and text or lines below WCAG contrast.
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
    return out


def check_page(page):
    cells = {c.get("id"): c for c in page.iter("mxCell")}
    geo = geometry(cells)
    problems = []
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
            if "cloud" in str(cells[c.get(end)].get("style")) and (fx, fy) not in CLOUD_PORTS:
                problems.append(f"{name}: {end} cloud port ({fx:g},{fy:g}) is not a side midpoint")
        pts = [port(src, ex, ey)]
        g = c.find("mxGeometry")
        arr = g.find("Array") if g is not None else None
        if arr is not None:
            pts += [(float(p.get("x", 0)), float(p.get("y", 0))) for p in arr.iter("mxPoint")]
        pts.append(port(tgt, nx, ny))
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
    return problems + padding(cells, geo) + title(cells, geo) + contrasts(cells, geo)


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
        kind = st.get("grIcon") or st.get("shape") or "box"
        _, y, _, h = geo[pid]
        pad = (min(b[1] for b in boxes) - y, y + h - max(b[1] + b[3] for b in boxes))
        kinds.setdefault(kind, []).append((pid, pad))
    out = []
    # Child groups must sit centered in their parent (equal left/right margins).
    for pid, boxes in kids.items():
        groups = [geo[c.get("id")] for c in cells.values() if c.get("parent") == pid and c.get("id") in kids]
        if groups:
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
            and not str(cells[i].get("value") or "").startswith("Updated")}
    if not body:
        return None
    left = min(b[0] for b in body.values())
    right = max(b[0] + b[2] for b in body.values())
    boxes = [b for i, b in body.items() if style(cells[i].get("style")).get("container") == "1"
             or any(c.get("parent") == i for c in cells.values())]
    main = max(boxes, key=lambda b: b[2], default=None)
    axis = main[0] + main[2] / 2 if main and main[2] >= (right - left) / 2 else (left + right) / 2
    return t, sub, axis, min(b[1] for b in body.values()) - head_bottom


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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    found = check(sys.argv[1])
    print("\n".join(found) or "ok")
    sys.exit(1 if found else 0)
