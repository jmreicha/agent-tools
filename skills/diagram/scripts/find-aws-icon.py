#!/usr/bin/env python3
"""Find the exact draw.io AWS icon and its category color, from draw.io's own sidebar.

Usage: find-aws-icon.py <term> [<term>...]
       find-aws-icon.py --self-test

Prints the drawio_lib call for every icon whose name contains a term, e.g.
  aws_service("bedrock_agentcore", "#01A88D")
"""
import os
import re
import sys
import time
import urllib.request

URL = "https://raw.githubusercontent.com/jgraph/drawio/dev/src/main/webapp/js/diagramly/sidebar/Sidebar-AWS4.js"
CACHE = os.path.join(os.path.expanduser("~/.cache/diagram"), "Sidebar-AWS4.js")


def parse(js):
    """[(helper, name, color)]: draw.io sets color per category block, not per icon."""
    color, out = {}, []
    for line in js.splitlines():
        m = re.search(r"var (n2?) = '[^']*fillColor=(#[0-9A-Fa-f]{6})", line)
        if m:
            color[m.group(1)] = m.group(2).upper()
            continue
        m = re.search(r"\(n2 \+ 'resourceIcon;resIcon=' \+ gn \+ '\.([a-z0-9_]+);", line)
        if m and "n2" in color:
            out.append(("aws_service", m.group(1), color["n2"]))
            continue
        m = re.search(r"\(n \+ '([a-z0-9_]+);([^']*)'", line)
        if m and "n" in color:
            own = re.search(r"fillColor=(#[0-9A-Fa-f]{6})", m.group(2))
            out.append(("aws", m.group(1), own.group(1).upper() if own else color["n"]))
    return out


def sidebar():
    """The sidebar source, cached for a week: icons change with draw.io releases, not daily."""
    if not os.path.exists(CACHE) or time.time() - os.path.getmtime(CACHE) > 7 * 86400:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with urllib.request.urlopen(URL, timeout=30) as r, open(CACHE, "wb") as f:
            f.write(r.read())
    with open(CACHE) as f:
        return f.read()


def self_test():
    js = """
		var n2 = 'sketch=0;fillColor=#01A88D;strokeColor=#ffffff;';
			 this.createVertexTemplateEntry(n2 + 'resourceIcon;resIcon=' + gn + '.bedrock_agentcore;',
			 this.createVertexTemplateEntry(n2 + 'resourceIcon;resIcon=' + gn + '.bedrock;',
		var n2 = 'sketch=0;fillColor=#E7157B;strokeColor=#ffffff;';
			 this.createVertexTemplateEntry(n2 + 'resourceIcon;resIcon=' + gn + '.cloudwatch_2;',
		var n = 'sketch=0;fillColor=#8C4FFF;strokeColor=none;' + mxConstants.STYLE_SHAPE + "=mxgraph.aws4.";
			 this.createVertexTemplateEntry(n + 'nat_gateway;',
			 this.createVertexTemplateEntry(n + 'endpoint;fillColor=#7AA116;',
"""
    got = parse(js)
    assert ("aws_service", "bedrock_agentcore", "#01A88D") in got, got
    assert ("aws_service", "cloudwatch_2", "#E7157B") in got, got
    assert ("aws", "nat_gateway", "#8C4FFF") in got, got
    assert ("aws", "endpoint", "#7AA116") in got, "a per-icon fillColor overrides the block"
    assert len(got) == 5, got
    print("ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--self-test"]:
        self_test()
        sys.exit()
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    hits = sorted({h for h in parse(sidebar()) if any(t.lower() in h[1] for t in args)})
    for helper, name, color in hits:
        print(f'{helper}("{name}", "{color}")')
    if not hits:
        sys.exit("no draw.io AWS icon matches: try a shorter term, or a plain box")
