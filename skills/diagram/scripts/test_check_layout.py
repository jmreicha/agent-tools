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
print("ok")
