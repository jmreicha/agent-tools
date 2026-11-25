#!/usr/bin/env python3
"""Self-check for check-layout.py's title and contrast rules: python3 test_check_layout.py"""
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from drawio_lib import Diagram, GROUPS, aws_service, label_at  # noqa: E402

spec = importlib.util.spec_from_file_location("check_layout", os.path.join(HERE, "check-layout.py"))
assert spec and spec.loader
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)


def problems(d):
    path = os.path.join(tempfile.mkdtemp(), "t.drawio")
    d.save(path, 1600, 900)
    return cl.check(path)


def base(title_cx=700, sub_cx=None, gap=60):
    d = Diagram()
    d.title("T", title_cx)
    d.text("st", "sub", (sub_cx or title_cx) - 300, 70, 600, 30)
    # Main box spans most of the content, so the title centers on it, not the page.
    d.group("aws", "AWS Cloud", "cloud", 200, 100 + gap, 1000, 600)
    d.text("side", "peer", 1300, 400, 120, 30)
    return d


def has(found, word):
    return any(word in p for p in found)


assert not has(problems(base()), "title"), problems(base())
assert has(problems(base(title_cx=800)), "title off-center")
assert has(problems(base(sub_cx=800)), "subtitle off-center")
assert has(problems(base(gap=20)), "below the subtitle")
# A side note sits outside the body, so it doesn't move the title's center line.
d = base()
d.note("how", "How it works", [(1, "A step that explains a piece of the diagram.")], 2300, 300, 340)
assert not has(problems(d), "title off-center"), problems(d)

d = base()
d.text("bad", "red", 300, 300, 100, 20, "fontColor=#F62E00;")
d.text("good", "red", 300, 330, 100, 20, "fontColor=light-dark(#C42500,#FF6A3D);")
d.vertex("pub", "", "html=1;" + GROUPS["public"], 300, 400, 400, 100)
d.text("dim", "list", 10, 10, 100, 20, "fontColor=#999999;", parent="pub")
d.cells.append('<mxCell id="faint" style="strokeColor=#DDDDDD;" edge="1" parent="1">'
               '<mxGeometry relative="1" as="geometry"><mxPoint x="300" y="600" as="sourcePoint"/>'
               '<mxPoint x="400" y="600" as="targetPoint"/></mxGeometry></mxCell>')
# An icon's label sits below it, so the icon's own fill isn't the label's background.
d.vertex("ec2", "EC2", "verticalLabelPosition=bottom;fillColor=#ED7100;fontColor=light-dark(#C42500,#FF6A3D);", 800, 300, 60, 60)
d.text("inl", '<b style="color:light-dark(#1e1e1e,#eeeeee)">T</b>', 300, 360, 100, 20)
found = problems(d)
assert has(found, "bad: text contrast"), found
assert not has(found, "good:"), found
assert has(found, "dim: text contrast"), found
assert has(found, "faint: line contrast"), found
assert not has(found, "ec2:"), found
assert has(found, "inl: inline light-dark"), found

# Lines through labels and edge labels on borders only show up in a render, so check them.
d = base()
d.vertex("bus", "Event bus", aws_service("eventbridge", "#E7157B"), 400, 300, 60, 60, "aws")
d.vertex("rule", "Rule", aws_service("eventbridge", "#E7157B"), 400, 500, 60, 60, "aws")
d.edge("up", "rule", "bus", exit=(0.5, 0), entry=(0.5, 1))
d.vertex("a", "A", aws_service("sqs", "#E7157B"), 600, 300, 60, 60, "aws")
d.vertex("b", "B", aws_service("sqs", "#E7157B"), 800, 300, 60, 60, "aws")
d.edge("ok", "a", "b", label="poll")
d.vertex("out", "Out", aws_service("sqs", "#E7157B"), 1240, 420, 60, 60)
d.vertex("c", "C", aws_service("sqs", "#E7157B"), 600, 420, 60, 60, "aws")
d.edge("edge", "c", "out", label="sends", label_at=0.86)
d.edge("l1", "bus", "a", label="first label", exit=(1, 0.25), entry=(0, 0.25))
d.edge("l2", "bus", "a", label="second label", exit=(1, 0.3), entry=(0, 0.3))
d.vertex("side", "a long side label", label_at(aws_service("sqs", "#E7157B"), "right"), 400, 600, 60, 60, "aws")
d.vertex("far", "Far", aws_service("sqs", "#E7157B"), 800, 600, 60, 60, "aws")
d.edge("thru", "side", "far")
found = problems(d)
assert has(found, "thru: line crosses side's label"), found
assert has(found, "up: line crosses bus's label"), found
assert not has(found, "ok:"), found
assert has(found, "edge: label sits on aws's border"), found
assert has(found, "l1: label overlaps l2's label") or has(found, "l2: label overlaps l1's label"), found

# Every non-library icon sits on the standard tile, which embed-icons.py adds.
d = base()
d.vertex("bare", "Okta", "shape=image;verticalLabelPosition=bottom;image=data:image/png,AA;", 300, 300, 60, 60)
d.vertex("tiled", "Vault", "shape=image;verticalLabelPosition=bottom;iconTile=1;image=data:image/svg+xml,AA;", 500, 300, 60, 60)
d.vertex("shot", "", "shape=image;image=data:image/png,AA;", 300, 500, 400, 300)
# Older diagrams draw boundaries as plain empty boxes, not containers.
d.vertex("zone", "", "rounded=1;whiteSpace=wrap;html=1;fillColor=none;", 900, 300, 200, 300)
d.vertex("z1", "Z1", aws_service("sqs", "#E7157B"), 1000, 400, 60, 60)
d.vertex("z2", "Z2", aws_service("sqs", "#E7157B"), 1200, 400, 60, 60)
d.edge("zl", "z1", "z2", label="crossing", label_at=-0.25)
found = problems(d)
assert has(found, "zl: label sits on zone's border"), found
assert has(found, "bare: icon has no tile"), found
assert not has(found, "tiled:") and not has(found, "shot:"), found

# Icon labels go below; moving one is only for an icon with a line at its bottom.
d = base()
d.vertex("bkt", "a-long-bucket-name", label_at(aws_service("s3", "#7AA116"), "right"), 300, 300, 60, 60)
d.vertex("src", "ec2-sweep (daily)", label_at(aws_service("sqs", "#E7157B"), "top"), 600, 300, 60, 60)
d.vertex("dst", "Dst", aws_service("sqs", "#E7157B"), 600, 500, 60, 60)
d.edge("down", "src", "dst", exit=(0.5, 1), entry=(0.5, 0))
found = problems(d)
assert has(found, "bkt: label is beside the icon"), found
assert not has(found, "src: label"), found

# A step badge must not sit on a label.
d.badge(1, at=(600, 290))
d.badge(2, "dst")
found = problems(d)
assert has(found, "badge on src's label"), found
assert not has(found, "badge on dst's label"), found
# Account groups read `Name (ID)`; the magenta group already says "account".
d = base()
d.group("wordy", "InternalServices-Prod account 135330967441", "account", 300, 300, 300, 200, "aws")
d.group("bare_id", "InternalServices-Prod 135330967441", "account", 700, 300, 300, 200, "aws")
d.group("tidy", "InternalServices-Prod (135330967441)", "account", 300, 540, 300, 200, "aws")
d.group("id_only", "135330967441", "account", 700, 540, 300, 200, "aws")
found = problems(d)
assert has(found, "wordy: account label"), found
assert has(found, "bare_id: account label"), found
assert not has(found, "tidy:") and not has(found, "id_only:"), found

# The cloud shape is the public internet; a named CDN or edge vendor gets its icon.
d = base()
d.vertex("inet", "Internet", "shape=cloud;whiteSpace=wrap;html=1;", 300, 300, 160, 90)
d.vertex("cdn", "CDN", "shape=cloud;whiteSpace=wrap;html=1;", 300, 450, 160, 90)
d.vertex("cf", "Cloudflare<br>api.example.com", "shape=cloud;whiteSpace=wrap;html=1;", 600, 300, 160, 90)
d.vertex("cfr", "Amazon CloudFront", "shape=cloud;whiteSpace=wrap;html=1;", 600, 450, 160, 90)
found = problems(d)
assert has(found, "cf: Cloudflare drawn as a cloud"), found
assert has(found, "cfr: CloudFront drawn as a cloud"), found
assert not has(found, "inet:") and not has(found, "cdn:"), found

# Full is the union of the concern pages: an edge drawn on a concern page must be on Full too.
from drawio_lib import save_pages  # noqa: E402
def pages(full_has_edge, full_has_node=True):
    net, full = Diagram(), Diagram()
    for g in (net, full):
        g.card("nlb", "tunnel-nlb", ["NLB"], None, 100, 100, 200)
    net.card("tun", "cloud-tunnel-service", ["svc"], None, 500, 100, 200)
    net.edge("e", "nlb", "tun")
    if full_has_node:
        full.card("tun", "cloud-tunnel-service", ["svc", "IRSA role"], None, 500, 100, 200)
    if full_has_edge:
        full.edge("e", "nlb", "tun")
    path = os.path.join(tempfile.mkdtemp(), "p.drawio")
    save_pages(path, [("Brief", Diagram(), 800, 400), ("Network", net, 800, 400), ("Full", full, 800, 400)])
    return cl.check(path)
assert has(pages(False), "Full is missing tunnel-nlb -> cloud-tunnel-service"), pages(False)
assert not has(pages(True), "Full is missing"), pages(True)
assert not has(pages(False, full_has_node=False), "Full is missing"), pages(False, False)
# A concern page may skip hops (Internet -> NLB without the IGW); Full just needs a path.
net, full = Diagram(), Diagram()
for g in (net, full):
    g.card("a", "Internet", ["x"], None, 0, 0, 100)
    g.card("c", "tunnel", ["x"], None, 400, 0, 100)
net.edge("e", "a", "c")
full.card("b", "igw-1", ["x"], None, 200, 0, 100)
full.edge("e1", "a", "b")
full.edge("e2", "b", "c")
path = os.path.join(tempfile.mkdtemp(), "q.drawio")
save_pages(path, [("Security", net, 800, 400), ("Full", full, 800, 400)])
assert not cl.check(path), cl.check(path)

# card() sizes long fact lists for 10px text (~15px a line), so they don't overflow.
d = Diagram()
assert d.card("big", "SG", [str(i) for i in range(12)], None, 0, 0, 300)[3] >= 34 + 14 * 12

# A plain box or icon-less card that names an iconed product or construct needs that icon.
from drawio_lib import BOX, CARD  # noqa: E402
d = base()
d.vertex("ctr", "surf-hls-server<br>docker container", BOX, 300, 300, 200, 60)
d.vertex("otel", "OTel collector<br>:4318", BOX, 300, 400, 200, 60)
d.card("peer", "Peered VPCs", ["pcx-1"], None, 300, 500, 300)
d.card("ok_card", "Peered VPCs", ["pcx-1"], aws_service("vpc", "#8C4FFF"), 700, 500, 300)
d.vertex("generic", "AI-12 dashcams", BOX, 700, 300, 120, 60)
d.note("nt", "Docker notes", ["notes are prose, not nodes"], 700, 400)
found = problems(d)
assert has(found, "ctr: box names Docker"), found
assert has(found, "otel: box names OpenTelemetry"), found
assert has(found, "peer: box names VPC peering"), found
assert not has(found, "ok_card:") and not has(found, "generic:") and not has(found, "nt:"), found
# Resource names that only start with a product prefix (k8s-traffic-...) aren't that product.
d = base()
d.card("sg", "k8s-traffic-produsblue", ["sg-0ba8"], None, 300, 300, 300)
d.vertex("api", "cloud-api<br>(EKS prod-us-blue)", BOX, 300, 400, 200, 60)
found = problems(d)
assert not has(found, "sg:"), found
assert has(found, "api: box names EKS"), found
# The key sits in the bottom-left corner: 40px under the lowest shape, flush with the leftmost.
d = base()
d.key("key", [("dashed=1;", "planned")], 200, 800, title="Line types")
assert not has(problems(d), "key: "), problems(d)
d = base()
d.key("key", [("dashed=1;", "planned")], 600, 800)
assert has(problems(d), "key: put the key in the bottom-left"), problems(d)
d = base()
d.key("key", [("dashed=1;", "planned")], 1500, 200)
assert has(problems(d), "key: put the key in the bottom-left"), problems(d)
d = base()
d.key("legend", [("dashed=1;", "planned")], 1500, 200, title="Line types")
assert has(problems(d), "legend: put the key in the bottom-left"), problems(d)

# A key's title says what it decodes; a bare "Key" makes readers guess.
d = base()
d.key("key", [("dashed=1;", "planned")], 200, 800)
assert has(problems(d), "key: title the key"), problems(d)
d = base()
d.key("key", [("dashed=1;", "planned")], 200, 800, title="Line types")
assert not has(problems(d), "title the key"), problems(d)

# Shapes stacked in a column share one center line, even a box over an icon.
d = base()
d.vertex("top", "Dashcams", BOX, 300, 300, 120, 60)
d.vertex("low", "Users", aws_service("sqs", "#E7157B"), 390, 500, 60, 60)
d.vertex("ok1", "Dashcams", BOX, 700, 300, 120, 60)
d.vertex("ok2", "Users", aws_service("sqs", "#E7157B"), 730, 500, 60, 60)
found = problems(d)
assert has(found, "low: off top's center line") or has(found, "top: off low's center line"), found
assert not has(found, "ok1:") and not has(found, "ok2:"), found
d = Diagram()  # a group or card between them breaks the stack: the shapes aren't one column
d.vertex("over", "iac", BOX, 300, 40, 120, 60)
d.group("mid", "A (123456789012)", "account", 200, 140, 600, 200)
d.card("in", "x", ["fact"], None, 260, 220, 300, 64, "mid")
d.vertex("under", "vendor", aws_service("sqs", "#E7157B"), 390, 400, 60, 60)
assert not has(problems(d), "off over's center line"), problems(d)

# Mirrored branches (exit 0.25 / 0.75 on one side) bend at the same distance from the node.
d = base()
d.vertex("hub", "Users", aws_service("sqs", "#E7157B"), 300, 400, 60, 60)
d.vertex("up", "Up", aws_service("sqs", "#E7157B"), 600, 250, 60, 60)
d.vertex("dn", "Down", aws_service("sqs", "#E7157B"), 600, 550, 60, 60)
d.edge("b1", "hub", "up", exit=(1, 0.25), points=[(420, 280)])
d.edge("b2", "hub", "dn", exit=(1, 0.75))
assert has(problems(d), "b2: mirrors b1 but bends"), problems(d)
d = base()
d.vertex("hub", "Users", aws_service("sqs", "#E7157B"), 300, 400, 60, 60)
d.vertex("up", "Up", aws_service("sqs", "#E7157B"), 600, 250, 60, 60)
d.vertex("dn", "Down", aws_service("sqs", "#E7157B"), 600, 550, 60, 60)
d.edge("b1", "hub", "up", exit=(1, 0.25), points=[(420, 280)])
d.edge("b2", "hub", "dn", exit=(1, 0.75), points=[(420, 580)])
assert not has(problems(d), "mirrors"), problems(d)

# Group and boundary labels read `Name (detail, detail)`, like accounts: IDs and CIDRs go in parens.
d = base()
d.group("v1", "VPC prod vpc-0c8f 10.94.0.0/16", "vpc", 300, 300, 300, 200, "aws")
d.group("v2", "prod-public tier · rtb-0d41aa7d", "public", 700, 300, 300, 200, "aws")
d.boundary("b1", "docker compose · host network", 300, 550, 300, 120)
d.group("ok1", "VPC prod (vpc-0c8ff26d, 10.94.0.0/16)", "vpc", 700, 550, 300, 120, "aws")
d.boundary("ok2", "EKS prod-us-blue", 300, 700, 300, 50)
found = problems(d)
assert has(found, "v1: label") and has(found, "v2: label") and has(found, "b1: label"), found
assert not has(found, "ok1: label") and not has(found, "ok2: label"), found

# Only the cloud shape has side-midpoint ports; an icon whose URL says "cloudflare" is a normal box.
d = base()
d.vertex("cfi", "edge", "shape=image;iconTile=1;image=https://cdn.simpleicons.org/cloudflare;", 300, 300, 60, 60)
d.vertex("dst", "Dst", aws_service("sqs", "#E7157B"), 600, 300, 60, 60)
d.edge("ce", "cfi", "dst", exit=(1, 0.25), entry=(0, 0.25))
assert not has(problems(d), "cloud port"), problems(d)

# A line that runs through a card, or hugs its edge, reads as tangled.
d = base()
d.card("src", "Src", ["x"], None, 300, 300, 120)
d.card("dst", "Dst", ["x"], None, 900, 300, 120)
d.card("mid", "NAT", ["x"], None, 500, 420, 200)
d.edge("hug", "src", "dst", exit=(0.5, 1), entry=(0.5, 1), points=[(360, 415), (960, 415)])
d.edge("thru", "src", "dst", exit=(0.25, 1), entry=(0.25, 1), points=[(330, 450), (930, 450)])
d.edge("clear", "src", "dst", exit=(0.75, 1), entry=(0.75, 1), points=[(390, 600), (990, 600)])
found = problems(d)
assert has(found, "hug: line runs along mid's edge"), found
assert has(found, "thru: line runs through mid"), found
assert not has(found, "clear: line runs"), found  # (mirror findings are a separate check)

# Duplicate cell IDs on a page make draw.io and every check pick one cell silently.
d = base()
d.card("dup", "A", ["x"], None, 300, 300, 200)
d.card("dup", "B", ["y"], None, 600, 300, 200)
assert has(problems(d), "dup: duplicate cell id"), problems(d)
assert not has(problems(base()), "duplicate cell id")
# A deliberate column order (Security's trust zones) opts out of centering and sibling padding.
for fixed in (False, True):
    d = base()
    d.group("acct", "A (123456789012)", "account", 300, 200, 800, 400, "aws")
    d.group("v", "V (10.0.0.0/16)", "vpc", 330, 260, 300, 300, "acct")
    d.vertex("vc", "c", "rounded=1;", 400, 360, 120, 60, "v")
    d.boundary("z1", "Z1", 250, 250, 40, 300)
    d.boundary("z2", "Z2", 1150, 250, 40, 300)
    d.vertex("a", "a", "rounded=1;", 255, 310, 30, 30, "z1")
    d.vertex("b", "b", "rounded=1;", 1155, 310, 30, 200, "z2")
    if fixed:
        d.fixed("acct", "z1", "z2")
    found = problems(d)
    assert has(found, "acct: child groups off-center") != fixed, found
    assert any("padding differs" in p and "z1" in p for p in found) != fixed, found
# A child that spills past its container's border reads as outside it.
d = base()
d.card("spill", "S", ["x"], None, 1100, 300, 200, 64, "aws")
d.card("fits", "F", ["x"], None, 300, 300, 200, 64, "aws")
found = problems(d)
assert has(found, "spill: spills past aws"), found
assert not has(found, "fits: spills"), found
print("ok")
