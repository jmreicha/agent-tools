#!/usr/bin/env python3
"""Flag edges that will render with a small jog: the source port and target
port are almost, but not exactly, in line. Usage: check-layout.py <file.drawio>
"""
import sys
import xml.etree.ElementTree as ET

# Offsets under this read as a mistake, not an intended bend.
JOG = 40


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
        g = c.find("mxGeometry")
        # Edges with explicit waypoints bend on purpose.
        if not src or not tgt or (g is not None and g.find("Array") is not None):
            continue
        st = style(c.get("style"))
        ex, ey = float(st.get("exitX", 0.5)), float(st.get("exitY", 0.5))
        nx, ny = float(st.get("entryX", 0.5)), float(st.get("entryY", 0.5))
        (sx, sy), (tx, ty) = port(src, ex, ey), port(tgt, nx, ny)
        sideways = ex in (0, 1) and nx in (0, 1)
        vertical = ey in (0, 1) and ny in (0, 1)
        off = abs(sy - ty) if sideways else abs(sx - tx) if vertical else 0
        if 1 <= off < JOG:
            problems.append(f"{c.get('id')}: {c.get('source')} -> {c.get('target')} is {off:g}px out of line")
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
