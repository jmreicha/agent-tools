#!/usr/bin/env python3
"""Build .drawio files from Python with the skill's styles baked in.

Write coordinates in absolute page space; children of a group are converted
to group-relative automatically. Labels are HTML (html=1): write <b>/<br> as
markup, and pass literal text that contains < or > through lit(). When a style
key repeats, the last copy wins, so `extra` arguments override defaults.
Run this file directly for a self-check.

    import sys; sys.path.insert(0, "<this skill dir>/scripts")
    from drawio_lib import *
    d = Diagram()
    d.group("vpc", "VPC 10.0.0.0/16", "vpc", 100, 100, 600, 300)
    d.card("alb", "ALB web", ["HTTPS 443"], aws("application_load_balancer"), 140, 160, 300, parent="vpc")
    d.key("key", [(ARROW, "request"), (ARROW + DASHED, "virtual link")], 40, 440)
    d.save("out.drawio", 800, 560)
"""
import html
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

GRAY = "light-dark(#666666,#BBBBBB)"
# White that survives the CLI's --theme dark (a bare #ffffff gets flipped).
WHITE = "light-dark(#ffffff,#ffffff)"
BOX = "rounded=1;whiteSpace=wrap;html=1;"
TEXT = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
LIST = TEXT + "align=left;verticalAlign=top;fontSize=10;"
ARROW = "edgeStyle=orthogonalEdgeStyle;endArrow=classic;html=1;rounded=0;curved=0;"
LINK = "endArrow=none;"
BOUNDARY = BOX + "fillColor=none;absoluteArcSize=1;arcSize=24;container=1;collapsible=0;"
# No "ellipse;" prefix: its perimeter bends edges that enter off-center.
CLOUD = "shape=cloud;whiteSpace=wrap;html=1;"
CARD = BOX + "align=left;verticalAlign=middle;spacingLeft=56;spacingRight=8;absoluteArcSize=1;arcSize=12;"
# Notes and keys share one quiet style: thin gray border, left-aligned text.
NOTE = (BOX + "align=left;verticalAlign=top;spacing=8;fontSize=11;fillColor=none;absoluteArcSize=1;arcSize=8;"
        "strokeColor=light-dark(#BBBBBB,#666666);")
BADGE = ("ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeColor=none;fontStyle=1;fontSize=11;"
         "fillColor=light-dark(#1e1e1e,#e0e0e0);fontColor=light-dark(#ffffff,#1e1e1e);")
ACCENT = "#F62E00"
RED = f"strokeColor={ACCENT};strokeWidth=2;"
# ACCENT is only 3.96:1 on white: fine for lines, too faint for small text.
RED_TEXT = "light-dark(#C42500,#FF6A3D)"
RED_EDGE = RED + f"fontColor={RED_TEXT};"
DASHED = "dashed=1;"
ICON = "verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;aspect=fixed;outlineConnect=0;"
_LABEL = {
    "bottom": "labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;",
    "top": "labelPosition=center;verticalLabelPosition=top;align=center;verticalAlign=bottom;",
    "left": "labelPosition=left;verticalLabelPosition=middle;align=right;verticalAlign=middle;",
    "right": "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;",
}

_GROUP = ("outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;container=1;pointerEvents=0;"
          "collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=30;")
GROUPS = {
    "cloud": "grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=light-dark(#232F3E,#D5DBDB);fillColor=none;fontColor=light-dark(#232F3E,#D5DBDB);",
    "account": "grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fillColor=none;fontColor=light-dark(#B81D58,#F06A9A);",
    "region": "grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;fontColor=light-dark(#0F6A9E,#5FB4E8);",
    "vpc": "grIcon=mxgraph.aws4.group_vpc;strokeColor=#8C4FFF;fillColor=none;fontColor=light-dark(#7A3EF0,#B394FF);",
    "public": "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#DCEBC6;fillOpacity=40;fontColor=light-dark(#1E6B10,#A6E06A);",
    "private": "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#C9E9EE;fillOpacity=40;fontColor=light-dark(#0B5A8A,#8ED3F5);",
    "security_group": "grIcon=mxgraph.aws4.group_security_group;strokeColor=#DD3522;fillColor=none;fontColor=light-dark(#C42B1C,#FF7A6B);",
    "asg": "grIcon=mxgraph.aws4.group_auto_scaling_group;strokeColor=#ED7100;fillColor=none;fontColor=light-dark(#B35500,#FF9A3D);",
    "datacenter": "grIcon=mxgraph.aws4.group_corporate_data_center;strokeColor=#7D8998;fillColor=none;fontColor=light-dark(#5A6573,#AEB8C4);",
}
# Boundary colors by kind (stroke, label text); see references/palette.md.
BOUNDARY_KINDS = {
    "eks": ("#ED7100", "light-dark(#B35500,#FF9A3D)"),
    "namespace": ("#326CE5", "light-dark(#2457C5,#7FA6F5)"),
    "datacenter": ("#7D8998", "light-dark(#5A6573,#AEB8C4)"),
}


def contrast(fg, bg, opacity=1, page="#FFFFFF"):
    """WCAG contrast ratio of two #RRGGBB colors. A semi-transparent bg is blended
    over the page first, because that's the color the reader actually sees."""
    rgb = lambda h: [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    bg = [b * opacity + p * (1 - opacity) for b, p in zip(rgb(bg), rgb(page))]
    lum = lambda c: sum(w * ((x / 255) / 12.92 if x / 255 <= 0.03928 else ((x / 255 + 0.055) / 1.055) ** 2.4)
                        for w, x in zip((0.2126, 0.7152, 0.0722), c))
    hi, lo = sorted((lum(rgb(fg)), lum(bg)), reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 2)


def lit(s):
    """Literal text for an HTML label: apps/<app>.yaml stays visible."""
    return html.escape(s, quote=False)


def label_at(style, where):
    """Move an icon's label: bottom (default), top, left, or right. Use top/left
    when the icon connects from below, so the edge doesn't cross its label."""
    return style + _LABEL[where]


def aws(shape, color="#8C4FFF"):
    """Resource-level AWS icon (ALB, NAT, IGW, TGW, endpoints, peering...)."""
    return ICON + f"strokeColor=none;shape=mxgraph.aws4.{shape};fillColor={color};"


def aws_service(service, color):
    """Square AWS service icon (EC2 #ED7100, EKS #ED7100, RDS #C925D1...)."""
    return ICON + f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{service};fillColor={color};strokeColor={WHITE};"


def k8s(kind):
    """Kubernetes object icon: pod, svc, deploy, ing, crd, secret, cm, job, ns, node, api..."""
    return ICON + f"shape=mxgraph.kubernetes.icon;prIcon={kind};fillColor=#2875E2;strokeColor={WHITE};"


# Generic people: one silhouette style everywhere. Color only to tell user types apart
# (blue, green, purple), and then give each color a key row.
PERSON = "light-dark(#232F3E,#D5DBDB)"


def person(kind="user", color=PERSON):
    """Outline silhouette for any user, client, or team: kind = user (one) or team (group)."""
    shape = {"user": "user", "team": "users"}[kind]
    return ICON + f"strokeColor=none;shape=mxgraph.aws4.{shape};fillColor={color};"


def image(src):
    """Brand logo by URL or data URI. Run embed-icons.py afterwards to inline URLs."""
    return ICON + f"strokeColor=none;shape=image;imageAspect=0;image={src};"


def cloudflare(product):
    """Cloudflare product icon (workers, r2, d1, kv, dns, waf, tunnel, access...), CC-BY-4.0.
    Outline-only, so embed-icons.py draws it orange on a peach tile, as Cloudflare's own diagrams do."""
    return image(f"https://raw.githubusercontent.com/cloudflare/cloudflare-docs/production/src/icons/{product}.svg#tile=FEF4E6,F6821F")


class Diagram:
    def __init__(self):
        self.cells, self.geo, self.n = [], {"1": (0, 0, 0, 0)}, 0

    def _id(self, base):
        self.n += 1
        return f"{base}{self.n}"

    def vertex(self, id, label, style, x, y, w, h, parent="1"):
        px, py = self.geo[parent][:2]
        self.geo[id] = (x, y, w, h)
        value = escape(label, {'"': "&quot;"})
        self.cells.append(f'<mxCell id="{id}" value="{value}" style="{style}" vertex="1" parent="{parent}">'
                          f'<mxGeometry x="{x - px}" y="{y - py}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return self.geo[id]

    def text(self, id, label, x, y, w, h, extra="", parent="1"):
        return self.vertex(id, label, TEXT + extra, x, y, w, h, parent)

    def title(self, label, cx, y=20):
        """36pt title centered on cx, the main box's center (not the page's), so it lines
        up with the diagram. Keep the first content row 60px+ below it (or the subtitle)."""
        return self.text("title", label, cx - 400, y, 800, 50, "fontSize=36;")

    def group(self, id, label, kind, x, y, w, h, parent="1"):
        return self.vertex(id, label, _GROUP + GROUPS[kind], x, y, w, h, parent)

    def boundary(self, id, label, x, y, w, h, icon=None, parent="1", kind=None):
        """Solid boundary. It's a container: put children in it with parent=id.
        An optional 30x30 vendor icon sits before the label in the top-left.
        kind (eks, namespace, datacenter) colors the border and label."""
        stroke, text = BOUNDARY_KINDS[kind] if kind else (None, None)
        self.vertex(id, "", BOUNDARY + (f"strokeColor={stroke};" if stroke else ""), x, y, w, h, parent)
        lx = x + 20
        if icon:
            self.vertex(id + "_i", "", icon, lx, y + 10, 30, 30, id)
            lx += 40
        self.text(id + "_l", label, lx, y + 10, w - (lx - x) - 20, 30,
                  "align=left;" + (f"fontColor={text};" if text else ""), id)
        return self.geo[id]

    def card(self, id, name, facts, icon, x, y, w, h=None, parent="1", extra=""):
        """Full-detail node: icon left, bold name, smaller facts one per line.
        Leave h out to size it from the number of facts. Facts keep the default color:
        draw.io ignores light-dark() inside label HTML, so an inline gray fails dark mode."""
        h = h or max(64, 34 + 12 * len(facts))
        rows = "<br>".join(facts)
        label = f'<b>{name}</b><br><span style="font-size:10px">{rows}</span>'
        self.vertex(id, label, CARD + ("" if icon else "spacingLeft=12;") + extra, x, y, w, h, parent)
        if icon:
            self.vertex(id + "_i", "", icon, x + 10, y + (h - 36) // 2, 36, 36, parent)
        return self.geo[id]

    def note(self, id, title, lines, x, y, w=220, accent=None):
        """Explanation or emphasis note: bold title, one short line each.
        accent colors the title, e.g. ACCENT to match an emphasized path."""
        body = "<br>".join(lines)
        h = 30 + 15 * len(lines)
        if not accent:
            return self.vertex(id, f"<b>{title}</b><br>{body}", NOTE, x, y, w, h)
        # An accent title is its own cell, so its color can be a fontColor style key:
        # light-dark() inside label HTML always renders the light value.
        self.vertex(id, f'<b style="visibility:hidden">{title}</b><br>{body}', NOTE, x, y, w, h)
        color = RED_TEXT if accent == ACCENT else accent
        self.vertex(id + "_t", f"<b>{title}</b>", TEXT + f"align=left;verticalAlign=top;spacing=8;fontSize=11;fontColor={color};",
                    x, y, w, 30, id)
        return self.geo[id]

    def key(self, id, rows, x, y, w=300):
        """Key in the note style: one row per line type, as (edge style, meaning).
        Each row draws a short sample of that line, then its meaning. A row whose
        style is an icon (e.g. person(color=...)) shows a small icon instead."""
        h = 34 + 20 * len(rows)
        self.vertex(id, "<b>Key</b>", NOTE, x, y, w, h)
        for i, (style, meaning) in enumerate(rows):
            ry = y + 38 + 20 * i
            sid = f"{id}_s{i}"
            if "shape=" in style and "edgeStyle" not in style:
                self.vertex(sid, "", style, x + 22, ry - 8, 16, 16)
                self.text(f"{id}_t{i}", meaning, x + 60, ry - 10, w - 70, 20, "align=left;fontSize=11;")
                continue
            self.cells.append(f'<mxCell id="{sid}" style="{ARROW}{style}" edge="1" parent="1">'
                              f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x + 10}" y="{ry}" as="sourcePoint"/>'
                              f'<mxPoint x="{x + 50}" y="{ry}" as="targetPoint"/></mxGeometry></mxCell>')
            self.text(f"{id}_t{i}", meaning, x + 60, ry - 10, w - 70, 20, "align=left;fontSize=11;")
        return self.geo[id]

    def badge(self, n, target=None, at=None):
        """Step number. On a node: centered on its top-left corner. With at=(x, y):
        centered there, for steps with no node (put it just above the arrow)."""
        if target:
            x, y = self.geo[target][:2]
        else:
            assert at, "badge needs a target or at=(x, y)"
            x, y = at
        return self.vertex(self._id("badge"), str(n), BADGE, x - 11, y - 11, 22, 22)

    def center(self, id):
        x, y, w, h = self.geo[id]
        return x + w / 2, y + h / 2

    def port(self, id, axis, at):
        """Fraction along a cell for an absolute x or y, so edges come out straight."""
        x, y, w, h = self.geo[id]
        return round((at - y) / h if axis == "y" else (at - x) / w, 4)

    def edge(self, id, src, tgt, style="", label="", exit=(1, 0.5), entry=(0, 0.5), points=(), label_at=0):
        """label_at moves the label along the edge: -1 = source end, 0 = middle, 1 = target end."""
        s = ARROW + style + (f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
                             f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;")
        pts = "".join(f'<mxPoint x="{a}" y="{b}"/>' for a, b in points)
        pts = f'<Array as="points">{pts}</Array>' if pts else ""
        self.cells.append(f'<mxCell id="{id}" value="{escape(label)}" style="{s}" edge="1" parent="1" '
                          f'source="{src}" target="{tgt}"><mxGeometry x="{label_at}" relative="1" as="geometry">{pts}</mxGeometry></mxCell>')

    def fanout(self, prefix, src, targets, trunk_x, style="", exit_y=0.5):
        """3+ edges from one port to a column of targets, sharing one trunk at trunk_x.
        Put trunk_x about 50px before the targets, clear of borders and labels."""
        _, y, _, h = self.geo[src]
        sy = y + h * exit_y
        for i, t in enumerate(targets):
            self.edge(f"{prefix}{i}", src, t, style, exit=(1, exit_y), points=[(trunk_x, sy), (trunk_x, self.center(t)[1])])

    def fanin(self, prefix, sources, tgt, trunk_x, style="", entry_y=0.5):
        """Mirror of fanout: 3+ sources in a column merge on one trunk into one port.
        Put trunk_x about 50px after the sources."""
        _, y, _, h = self.geo[tgt]
        ty = y + h * entry_y
        for i, s in enumerate(sources):
            self.edge(f"{prefix}{i}", s, tgt, style, entry=(0, entry_y), points=[(trunk_x, self.center(s)[1]), (trunk_x, ty)])

    def xml(self, w, h, name="Page-1", page_id="p1"):
        body = "\n".join(self.cells)
        return (f'<diagram name="{name}" id="{page_id}"><mxGraphModel grid="1" gridSize="10" page="1" '
                f'pageWidth="{w}" pageHeight="{h}"><root><mxCell id="0"/><mxCell id="1" parent="0"/>\n'
                f'{body}\n</root></mxGraphModel></diagram>')

    def save(self, path, w, h, name="Page-1"):
        with open(path, "w") as f:
            f.write(f'<mxfile host="Electron">{self.xml(w, h, name)}</mxfile>')


def save_pages(path, pages):
    """Write one file with several pages: pages = [("Brief", diagram, w, h), ...]."""
    body = "".join(d.xml(w, h, name, f"p{i + 1}") for i, (name, d, w, h) in enumerate(pages))
    with open(path, "w") as f:
        f.write(f'<mxfile host="Electron">{body}</mxfile>')


if __name__ == "__main__":
    import tempfile, os
    d = Diagram()
    d.group("vpc", "VPC", "vpc", 100, 100, 400, 200)
    d.card("a", "A", ["fact"], aws("nat_gateway"), 120, 150, 200, 64, "vpc")
    assert 'x="20" y="50"' in d.cells[-2], "child coordinates must be group-relative"
    assert d.port("vpc", "y", 182) == 0.41
    assert d.card("b", "B", ["1", "2", "3", "4"], None, 120, 230, 200)[3] == 82
    d.fanout("f", "vpc", ["a", "b"], 550)
    assert '<mxPoint x="550" y="200.0"/>' in d.cells[-1]
    d.fanin("g", ["a", "b"], "vpc", 90)
    assert '<mxPoint x="90" y="200.0"/>' in d.cells[-1]
    d.boundary("eks", "EKS", 600, 100, 300, 200, icon=aws_service("eks", "#ED7100"))
    d.vertex("pod", "pod", k8s("pod"), 650, 160, 48, 48, "eks")
    assert 'parent="eks"' in d.cells[-1] and 'x="50" y="60"' in d.cells[-1]
    assert "#ffffff;" not in aws_service("ec2", "#ED7100").replace(WHITE, "")
    assert lit("apps/<app>.yaml") == "apps/&lt;app&gt;.yaml"
    d.note("nt", "Hot", ["x"], 0, 950, accent=ACCENT)
    assert "color:light-dark(" not in d.cells[-2] and RED_TEXT in d.cells[-1]
    d.boundary("k", "EKS", 0, 700, 300, 200, kind="eks")
    assert "strokeColor=#ED7100" in d.cells[-2] and "#B35500" in d.cells[-1]
    assert contrast("#C42500", "#FFFFFF") >= 4.5 and contrast("#FF6A3D", "#121212") >= 4.5
    assert contrast("#000000", "#FFFFFF") == 21 and contrast("#1E6B10", "#DCEBC6", 0.4) >= 4.5
    d.key("key", [(ARROW, "request"), (ARROW + DASHED, "virtual")], 40, 400)
    d.badge(1, "a")
    d.key("key2", [(person("team", "#2875E2"), "platform team")], 400, 400)
    assert "shape=mxgraph.aws4.users;fillColor=#2875E2" in d.cells[-2]
    out = os.path.join(tempfile.mkdtemp(), "t.drawio")
    save_pages(out, [("Brief", d, 1000, 600), ("Full", d, 1000, 600)])
    assert [p.get("name") for p in ET.parse(out).iter("diagram")] == ["Brief", "Full"]
    print("ok")
