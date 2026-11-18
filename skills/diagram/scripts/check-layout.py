#!/usr/bin/env python3
"""Flag edges that will render with a small jog: the source port and target
port are almost, but not exactly, in line. Usage: check-layout.py <file.drawio>
"""
import sys
import xml.etree.ElementTree as ET

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
    return problems + padding(cells, geo)


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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    found = check(sys.argv[1])
    print("\n".join(found) or "ok")
    sys.exit(1 if found else 0)
