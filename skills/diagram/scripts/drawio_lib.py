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
import re
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
# Network line palette (palette.md): hue = kind of traffic, dash = how it travels, arrowhead = direction.
INGRESS = "strokeColor=light-dark(#1B7F3B,#3DDC84);strokeWidth=2;fontColor=light-dark(#1B7F3B,#3DDC84);"
EGRESS = "strokeColor=light-dark(#1F4FD1,#6E9BFF);strokeWidth=2;fontColor=light-dark(#1F4FD1,#6E9BFF);"
ENDPOINT = INGRESS + DASHED  # VPC endpoint or PrivateLink
PEER = "endArrow=none;strokeColor=light-dark(#7A4A2A,#C49A6C);strokeWidth=2;fontColor=light-dark(#7A4A2A,#C49A6C);"
APP = "strokeWidth=2;"  # app or service call inside the network
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
    "security_group": "grIcon=mxgraph.aws4.group_security_group;strokeColor=light-dark(#CF6F63,#D9776B);fillColor=none;fontColor=light-dark(#A8443A,#F0958A);",  # AWS red, softened so severity chips own bright red
    "asg": "grIcon=mxgraph.aws4.group_auto_scaling_group;strokeColor=#ED7100;fillColor=none;fontColor=light-dark(#B35500,#FF9A3D);",
    "datacenter": "grIcon=mxgraph.aws4.group_corporate_data_center;strokeColor=#7D8998;fillColor=none;fontColor=light-dark(#5A6573,#AEB8C4);",
}
# Boundary colors by kind (stroke, label text); see references/palette.md.
BOUNDARY_KINDS = {
    "eks": ("#ED7100", "light-dark(#B35500,#FF9A3D)"),
    "namespace": ("#326CE5", "light-dark(#2457C5,#7FA6F5)"),
    "datacenter": ("#7D8998", "light-dark(#5A6573,#AEB8C4)"),
    # Security pages only: a dashed trust boundary (threat-model convention), see aws-network.md.
    "trust": ("light-dark(#666666,#BBBBBB)", "light-dark(#4D4D4D,#CCCCCC)"),
}
# Finding severity chips, pinned so dark mode keeps the scale. Text pairs pass 4.5:1 on each fill.
SEVERITY = {
    "C": ("Critical", "#C92A2A", "#FFFFFF"),
    "H": ("High", "#E8590C", "#1A1A1A"),
    "M": ("Medium", "#FAB005", "#1A1A1A"),
    "L": ("Low", "#ADB5BD", "#1A1A1A"),
}
# Crown jewel (sensitive data store) marker: a small purple hexagon beside the node.
SG_RED = "light-dark(#CF6F63,#D9776B)"  # AWS SG red, softened; shared by SG boxes and rule cards
SG_ICON = f"shape=mxgraph.aws4.group_security_group;html=1;strokeColor=none;fillColor={SG_RED};"
SG_CARD = f"strokeColor={SG_RED};"  # card(..., SG_ICON, ..., extra=SG_CARD) pairs a rule card with its SG box

CROWN = ("shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1;size=5;html=1;strokeColor=none;"
         "fillColor=light-dark(#7048E8,#9775FA);")


def severity_style(code):
    _, fill, text = SEVERITY[code]
    return (f"shape=rect;rounded=1;arcSize=30;html=1;strokeColor=none;fontStyle=1;fontSize=10;"
            f"fillColor=light-dark({fill},{fill});fontColor=light-dark({text},{text});")


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
    Outline-only, so it passes the brand orange; embed-icons.py tiles it like every other logo."""
    return image(f"https://raw.githubusercontent.com/cloudflare/cloudflare-docs/production/src/icons/{product}.svg#tile=F6821F")


def _bare(t):
    return re.sub(r"<[^>]+>", "", t)


def col_widths(row_sets):
    """Pixel width of each table column across every card, so columns line up from card to card."""
    rows = [r for rs in row_sets for r in rs if isinstance(r, tuple)]
    return [round(5 * max(len(_bare(r[i])) for r in rows)) + 12 for i in range(len(rows[0]))] if rows else []  # cells render ~5px a char


def detail_w(title, rows, colw=None):
    """Width that fits a detail card's text, so cards don't trail empty space. detail_grid gives
    every card the widest. ~6.5px a bold 12px character, ~4.5px at 10px, 56px icon + 20px pad."""
    table = sum(colw or col_widths([rows]))  # table columns carry their own 12px gap
    text = max(6.5 * len(_bare(title)), table, *(4.5 * len(_bare(r)) for r in rows if not isinstance(r, tuple)))
    return int(-(-(text + 76) // 10) * 10)


def arrow_rows(rows, head):
    """Turn `a → b` lines into table rows under a bold header (IAM `action → resource`).
    Lines before the first one stay plain lines above the table; later ones span it as headings."""
    i = next((n for n, r in enumerate(rows) if " → " in r), len(rows))
    first = max((n for n in range(i) if not rows[n].startswith("<b>")), default=-1) + 1  # a heading right above stays in the table
    table = [tuple(r.split(" → ", 1)) if " → " in r else r for r in rows[first:]]
    return rows[:first] + ([tuple(f"<b>{h}</b>" for h in head)] if table else []) + table


def sg_rows(name, sg_id, rules):
    """(title, rows, icon) for an SG rule card: "name (id)", inbound before outbound."""
    def cols(r):
        t = r.split()
        if t[0] not in ("in", "out") or len(t) < 3:
            return r  # a note, not a rule: one spanning row
        port, rest = ("all", t[2:]) if t[1] == "all" else (t[2], t[3:])
        return (t[0], t[1], port, " ".join(rest[1:] if rest[:1] == ["from"] else rest))
    rows = [cols(r) for r in sorted(rules, key=lambda r: not r.startswith("in"))]
    notes, table = [r for r in rows if isinstance(r, str)], [r for r in rows if isinstance(r, tuple)]
    head = [("<b>dir</b>", "<b>proto</b>", "<b>port</b>", "<b>source / dest</b>")] if table else []
    return f"{name} ({sg_id})", notes + head + table, SG_ICON  # notes read as plain lines above the table


class Diagram:
    def __init__(self):
        self.cells, self.geo, self.styles, self.n = [], {"1": (0, 0, 0, 0)}, {}, 0
        self.name = "Diagram"

    def _id(self, base):
        self.n += 1
        return f"{base}{self.n}"

    def vertex(self, id, label, style, x, y, w, h, parent="1"):
        px, py = self.geo[parent][:2]
        self.geo[id], self.styles[id] = (x, y, w, h), style
        value = escape(label, {'"': "&quot;"})
        self.cells.append(f'<mxCell id="{id}" value="{value}" style="{style}" vertex="1" parent="{parent}">'
                          f'<mxGeometry x="{x - px}" y="{y - py}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return self.geo[id]

    def text(self, id, label, x, y, w, h, extra="", parent="1"):
        return self.vertex(id, label, TEXT + extra, x, y, w, h, parent)

    def title(self, label, cx, y=20):
        """36pt title centered on cx, the main box's center (not the page's), so it lines
        up with the diagram. Keep the first content row 60px+ below it (or the subtitle).
        It also names the page, so the tab doesn't read "Page-1"."""
        self.name = label
        return self.text("title", label, cx - 400, y, 800, 50, "fontSize=36;")

    def group(self, id, label, kind, x, y, w, h, parent="1"):
        return self.vertex(id, label, _GROUP + GROUPS[kind], x, y, w, h, parent)

    def boundary(self, id, label, x, y, w, h, icon=None, parent="1", kind=None):
        """Solid boundary. It's a container: put children in it with parent=id.
        An optional 30x30 vendor icon sits before the label in the top-left, and squares the corners.
        kind (eks, namespace, datacenter) colors the border and label."""
        stroke, text = BOUNDARY_KINDS[kind] if kind else (None, None)
        dash = "dashed=1;dashPattern=8 4;" if kind == "trust" else ""
        square = "rounded=0;" if icon else ""  # iconed boundaries match the square AWS groups
        self.vertex(id, "", BOUNDARY + (f"strokeColor={stroke};" if stroke else "") + dash + square, x, y, w, h, parent)
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
        h = h or max(64, 34 + 15 * len(facts))  # 10px fact lines render ~15px tall
        rows = "<br>".join(facts)
        label = f'<b>{name}</b><br><span style="font-size:10px">{rows}</span>'
        self.vertex(id, label, CARD + ("" if icon else "spacingLeft=12;") + extra, x, y, w, h, parent)
        if icon:
            self.vertex(id + "_i", "", icon, x + 10, y + (h - 36) // 2, 36, 36, parent)
        return self.geo[id]

    def fixed(self, *ids):
        """Mark containers whose layout is deliberate (a required column order, columns
        sharing one bottom): check-layout skips their centering and sibling padding."""
        for n, c in enumerate(self.cells):
            if any(f'<mxCell id="{i}" ' in c for i in ids):
                self.cells[n] = c.replace('style="', 'style="fixedLayout=1;', 1)

    def detail(self, id, title, rows, icon, x, y, w=None, parent="1", colw=None):
        """Detail card (SG rules, IAM roles): icon top-left, bold title, a blank line, then 10px rows:
        strings as plain lines, tuples as table rows whose columns line up. colw: shared column widths.
        An SG icon also takes the SG stroke, to match its box."""
        start = next((n for n, r in enumerate(rows) if isinstance(r, tuple)), len(rows))
        lines, table = rows[:start], rows[start:]  # strings inside the table span it, as section headings
        colw = colw or col_widths([rows])
        w = w or detail_w(title, rows, colw)
        heads = sum(isinstance(r, str) for r in table)  # section headings get 4px above them
        h = round(56 + 14.4 * len(lines) + 11.5 * len(table) + 4 * heads)  # <br> lines ~14.4px, table rows ~11.5px; 56 = title, blank, padding
        body = f'<span style="font-size:10px">{"<br>".join(lines)}</span>' if lines else ""
        if table:
            body += '<table style="font-size:10px;border-collapse:collapse">' + "".join(
                "<tr>" + ("".join(f'<td style="width:{cw}px;padding:0">{c}</td>' for c, cw in zip(r, colw)) if isinstance(r, tuple)
                          else f'<td colspan="{len(colw)}" style="padding:4px 0 0 0">{r}</td>') + "</tr>"
                for r in table) + "</table>"
        label = f'<b>{title}</b><br><br>{body}'
        style = CARD.replace("verticalAlign=middle", "verticalAlign=top;spacingTop=8") + (SG_CARD if icon == SG_ICON else "")
        self.vertex(id, label, style if icon else style + "spacingLeft=12;", x, y, w, h, parent)
        if icon:
            self.vertex(id + "_i", "", icon, x + 10, y + 10, 36, 36, parent)
        return self.geo[id]

    def detail_grid(self, cards, cx, y, cols, gap, parent="1"):
        """Detail cards in `cols` columns centered on cx, all the widest card's width.
        cards: (id, title, rows, icon). Each goes under the shortest column (masonry),
        so short cards pack together instead of leaving row gaps. Returns the bottom y."""
        colw = col_widths([r for _, _, r, _ in cards])
        w = max(detail_w(t, r, colw) for _, t, r, _ in cards)
        x0 = cx - (cols * w + (cols - 1) * gap) // 2
        tops = [y] * cols
        for id, title, rows, icon in cards:
            i = tops.index(min(tops))
            tops[i] += self.detail(id, title, rows, icon, x0 + i * (w + gap), tops[i], w, parent, colw)[3] + 30
        return max(tops) - 30

    def note(self, id, title, lines, x, y, w=220, accent=None):
        """Explanation or emphasis note: bold title, a blank line, then the body.
        lines: short strings, one per line, or (n, text) steps, which render as a numbered
        list that wraps to the box and keeps the badge numbers (3, 4, 7...).
        accent colors the title, e.g. ACCENT to match an emphasized path."""
        per_line = max(1, int((w - 34) / 5.5))  # ~5.5px a character at 11px, inside spacing and list indent
        if lines and isinstance(lines[0], tuple):
            body = ('<ol style="margin:0;padding-left:18px">'
                    + "".join(f'<li value="{n}" style="margin-bottom:4px">{t}</li>' for n, t in lines) + "</ol>")
            rows = sum(-(-len(t) // per_line) for _, t in lines) + 0.3 * len(lines)
        else:
            body, rows = "<br>".join(lines), sum(max(1, -(-len(t) // (per_line + 4))) for t in lines)  # +4: no list indent
        h = round(38 + 14 * rows)  # 11px text renders ~13.5px a line; 38 = padding, title, blank line
        if not accent:
            return self.vertex(id, f"<b>{title}</b><br><br>{body}", NOTE, x, y, w, h)
        # An accent title is its own cell, so its color can be a fontColor style key:
        # light-dark() inside label HTML always renders the light value.
        self.vertex(id, f'<b style="visibility:hidden">{title}</b><br><br>{body}', NOTE, x, y, w, h)
        color = RED_TEXT if accent == ACCENT else accent
        self.vertex(id + "_t", f"<b>{title}</b>", TEXT + f"align=left;verticalAlign=top;spacing=8;fontSize=11;fontColor={color};",
                    x, y, w, 30, id)
        return self.geo[id]

    def key(self, id, rows, x, y, w=300, title="Key"):
        """Key in the note style: one row per line type, as (edge style, meaning).
        Each row draws a short sample of that line, then its meaning. A row whose
        style is an icon (e.g. person(color=...)) shows a small icon instead."""
        h = 34 + 20 * len(rows)
        # keyNote=1 lets check-layout.py find a key whatever its title says.
        self.vertex(id, f"<b>{title}</b>", NOTE + "keyNote=1;", x, y, w, h)
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

    def severity(self, code, n, target, slot=0):
        """Finding chip (`H2`) on a node's top-right corner; slot steps left for a second chip.
        Number findings in their own note; the chip's letter is the level (SEVERITY)."""
        x, y, w, _ = self.geo[target]
        return self.vertex(self._id("sev"), f"{code}{n}", severity_style(code), x + w - 30 - slot * 34, y - 9, 30, 18)

    def crown(self, target):
        """Crown-jewel marker on a node's top-left corner (sensitive data store)."""
        x, y, _, _ = self.geo[target]
        return self.vertex(self._id("crown"), "", CROWN, x - 9, y - 9, 20, 18)

    def badge(self, n, target=None, at=None):
        """Step number. On a node: centered on its top-left corner, or bottom-left when the
        label is on top. With at=(x, y): centered there, for steps with no node (just above the arrow)."""
        if target:
            x, y, _, h = self.geo[target]
            y += h if "verticalLabelPosition=top" in self.styles.get(target, "") else 0
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

    def xml(self, w, h, name=None, page_id="p1"):
        body = "\n".join(self.cells)
        name = escape(name or self.name, {'"': "&quot;"})
        return (f'<diagram name="{name}" id="{page_id}"><mxGraphModel grid="1" gridSize="10" page="1" '
                f'pageWidth="{w}" pageHeight="{h}"><root><mxCell id="0"/><mxCell id="1" parent="0"/>\n'
                f'{body}\n</root></mxGraphModel></diagram>')

    def save(self, path, w, h, name=None):
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
    assert d.card("b", "B", ["1", "2", "3", "4"], None, 120, 230, 200)[3] == 94
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
    d.boundary("tz", "Internet (untrusted)", 0, 1100, 300, 200, kind="trust")
    assert "dashed=1" in d.cells[-2] and "rounded=0" not in d.cells[-2]
    # A boundary with an icon gets square corners, like the AWS groups it sits beside.
    d.boundary("cf", "third party", 400, 1100, 300, 200, icon=aws_service("eks", "#ED7100"), kind="trust")
    assert "rounded=0" in d.cells[-3] and "dashed=1" in d.cells[-3]
    d.severity("H", 1, "a")
    assert "H1" in d.cells[-1] and "fillColor=light-dark(#E8590C,#E8590C)" in d.cells[-1]
    for _, fill, text in SEVERITY.values():
        assert contrast(text, fill) >= 4.5, (text, fill)
    d.crown("a")
    assert "shape=hexagon" in d.cells[-1]
    # Detail card: icon top-left, bold title, a blank line, one row per line
    d.detail("r", *sg_rows("web-sg", "sg-1", ["out tcp 443 0.0.0.0/0", "in tcp 80 a", "in tcp 22 b"]), 0, 1400)
    c, i = d.cells[-2], d.cells[-1]
    assert "&lt;b&gt;web-sg (sg-1)&lt;/b&gt;&lt;br&gt;&lt;br&gt;" in c and "verticalAlign=top" in c
    assert c.index("&gt;80&lt;") < c.index("&gt;22&lt;") < c.index("&gt;443&lt;"), "inbound first, source order kept"
    assert SG_RED in c and 'x="10" y="1410"' in i, "SG color, icon top-left"
    assert "&lt;table" in c and "&lt;td" in c and "&gt;port&lt;" in c, "SG rules render as a table with a header"
    assert sg_rows("x", "sg-1", ["in all from itself"])[1][1] == ("in", "all", "all", "itself"), "all: no port, drop 'from'"
    t, rows, _ = sg_rows("x", "sg-1", ["out all 0.0.0.0/0", "no inbound rules"])
    assert rows[0] == "no inbound rules" and isinstance(rows[1], tuple), "notes go above the table"
    d.detail("nt", t, rows, SG_ICON, 0, 1500)
    assert d.cells[-2].index("no inbound rules") < d.cells[-2].index("&lt;table"), "notes render above the table"
    rows = arrow_rows(["assumed by x", "<b>pol</b>", "s3:Get → b", "ec2:Describe → *"], ("action", "resource"))
    assert rows[0] == "assumed by x" and rows[1] == ("<b>action</b>", "<b>resource</b>") and rows[3] == ("s3:Get", "b")
    d.detail("rl", "IAM r", rows, None, 0, 1700)
    c = d.cells[-1]
    assert c.index("assumed by x") < c.index("&lt;table") < c.index("colspan"), "lines above, policy name spans the table"
    g = Diagram()
    g.detail_grid([("p", *sg_rows("p", "sg-1", ["in tcp 1 a"])), ("q", *sg_rows("q", "sg-2", ["in tcp 33001 a-much-longer-source"]))], 500, 0, 2, 40)
    widths = [re.findall(r"td style=&quot;width:(\d+)px", c) for c in g.cells if 'id="p"' in c or 'id="q"' in c]
    assert widths[0] == widths[1] and widths[0], "one set of column widths across the grid, so columns line up"
    d.detail("role", "IAM r", ["<b>policy</b>", "s3:Get → b"], aws("role", "#DD344C"), 0, 1600)
    assert "strokeColor=light-dark(#CF6F63" not in d.cells[-2], "only SG cards take the SG color"
    g = Diagram()
    cards = [("a", "a", ["x"] * 10, None), ("b", "b", ["x"], None), ("c", "c", ["x"], None), ("d", "d", ["x"], None)]
    bottom = g.detail_grid(cards, 500, 0, 2, 40)
    col = lambda k: g.geo[k][0]
    assert col("b") == col("c") == col("d") != col("a"), "short cards pack under each other, not in rows"
    assert bottom == max(g.geo[k][1] + g.geo[k][3] for k in "abcd")
    assert len({g.geo[k][2] for k in "abcd"}) == 1, "one shared width"
    assert detail_w("a", ["x"]) < detail_w("a" * 40, ["x"]) < 520, "width fits the title"
    assert detail_w("a", ["x" * 80]) > 400, "a long row widens it too"
    assert detail_w("a", ["<b>p</b>"]) == detail_w("a", ["p"]), "markup takes no width"
    out = os.path.join(tempfile.mkdtemp(), "t.drawio")
    save_pages(out, [("Brief", d, 1000, 600), ("Full", d, 1000, 600)])
    assert [p.get("name") for p in ET.parse(out).iter("diagram")] == ["Brief", "Full"]
    t = Diagram()
    t.title("dibs & co", 500)
    t.save(out, 1000, 600)
    assert [p.get("name") for p in ET.parse(out).iter("diagram")] == ["dibs & co"]
    b = Diagram()
    b.vertex("job", "job", label_at(k8s("job"), "top"), 100, 100, 60, 60)
    b.badge(1, "job")
    assert 'x="89" y="149"' in b.cells[-1], "top label: badge moves to the bottom-left"
    # Notes: a blank line after the title; numbered steps become a wrapped list that keeps badge numbers
    b.note("n1", "Plain", ["one line"], 0, 0)
    assert "&lt;/b&gt;&lt;br&gt;&lt;br&gt;one line" in b.cells[-1], "blank line after the title"
    _, _, _, short = b.note("n2", "How", [(3, "Short.")], 0, 0, 340)
    _, _, _, long = b.note("n3", "How", [(3, "word " * 60), (7, "Short.")], 0, 0, 340)
    assert "&lt;li value=&quot;7&quot;" in b.cells[-1], "list keeps badge numbers"
    assert "&lt;br&gt;" not in b.cells[-1].split("&lt;ol")[1], "steps wrap to the box, not by hand"
    assert long > short + 40, "height follows the wrapped text"
    _, _, _, p1 = b.note("n4", "Plain", ["short"], 0, 0, 220)
    _, _, _, p2 = b.note("n5", "Plain", ["word " * 40], 0, 0, 220)
    assert p2 > p1 + 40, "plain lines that wrap grow the note too"
    print("ok")
