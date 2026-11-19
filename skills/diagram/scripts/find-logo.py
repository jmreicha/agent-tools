#!/usr/bin/env python3
"""Find a usable logo for a vendor or product with no draw.io icon set.

Usage: find-logo.py <name> [--domain example.com] [--github org]
       find-logo.py --self-test

Tries sources in order, vector first, and prints every one that works; the first
line is the pick. Use it as `image(url)`, then run embed-icons.py.
"""
import importlib.util
import json
import os
import re
import struct
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("embed_icons", os.path.join(HERE, "embed-icons.py"))
assert spec and spec.loader
embed_icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(embed_icons)

MIN_PX = 64  # smaller rasters look blurry next to library icons


def slugs(name):
    """simple-icons and CNCF slugs: lowercase, no spaces, dots, or dashes."""
    base = name.lower().strip()
    out = [re.sub(r"[^a-z0-9]", "", base), re.sub(r"[^a-z0-9]+", "-", base).strip("-")]
    return list(dict.fromkeys(s for s in out if s))


def png_size(body):
    if body[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", body[16:24])


def dark_svg(body):
    """True when every fill is near black: it will vanish on a dark page."""
    fills = re.findall(rb"fill\s*[:=]\s*[\"']?(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}\b)", body)
    if not fills:
        return b"fill" not in body  # simple-icons with no fill render black
    def lum(h):
        h = h.decode().lstrip("#")
        h = "".join(c * 2 for c in h) if len(h) == 3 else h
        return sum(int(h[i:i + 2], 16) for i in (0, 2, 4)) / 765
    return all(lum(f) < 0.2 for f in fills)


def candidates(name, domain=None, github=None):
    for s in slugs(name):
        yield "simple-icons", f"https://cdn.simpleicons.org/{s}"
    for s in slugs(name):
        yield "cncf", f"https://raw.githubusercontent.com/cncf/artwork/main/projects/{s}/icon/color/{s}-icon-color.svg"
    for org in [github] if github else github_orgs(name):
        yield "github", f"https://github.com/{org}.png?size=256"
    if domain:
        yield "site", f"https://{domain}/apple-touch-icon.png"
        for href in site_icons(domain):
            yield "site", href
        yield "favicon", f"https://www.google.com/s2/favicons?domain={domain}&sz=256"


def github_orgs(name):
    """Top org matches; GitHub's search API allows a few unauthenticated calls a minute."""
    q = urllib.parse.quote(f"{name} type:org")
    try:
        req = urllib.request.Request(f"https://api.github.com/search/users?q={q}&per_page=3", headers=embed_icons.UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return [u["login"] for u in json.load(r)["items"]]
    except Exception:
        return []


def site_icons(domain):
    """<link rel="icon"> and apple-touch-icon hrefs from the homepage, SVG first."""
    try:
        req = urllib.request.Request(f"https://{domain}/", headers=embed_icons.UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read(300_000).decode(errors="ignore")
    except Exception:
        return []
    hrefs = []
    for tag in re.findall(r"<link\b[^>]*>", html, re.I):
        if re.search(r'rel=["\'][^"\']*(icon|apple-touch-icon)', tag, re.I):
            m = re.search(r'href=["\']([^"\']+)', tag)
            if m:
                hrefs.append(urllib.parse.urljoin(f"https://{domain}/", m.group(1)))
    return sorted(dict.fromkeys(hrefs), key=lambda h: not h.split("?")[0].endswith(".svg"))


def check(url):
    """(ok, note) for one candidate."""
    try:
        ctype, body = embed_icons.fetch(url)
    except Exception as e:
        return False, str(e)
    if ctype == "image/svg+xml":
        return True, "svg" + ("; all black: embed-icons.py tiles it, or use a library shape (icons.md)" if dark_svg(body) else "")
    size = png_size(body)
    if not size:
        return False, f"{ctype}: not PNG or SVG"
    if min(size) < MIN_PX:
        return False, f"{size[0]}x{size[1]}px, under {MIN_PX}px"
    return True, f"png {size[0]}x{size[1]}; prefer an SVG, which tiles in its own color"


def self_test():
    assert slugs("Cato Networks") == ["catonetworks", "cato-networks"]
    assert slugs("Node.js") == ["nodejs", "node-js"]
    assert png_size(b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + struct.pack(">II", 128, 64)) == (128, 64)
    assert dark_svg(b'<svg><path fill="#181717"/></svg>')
    assert not dark_svg(b'<svg><path fill="#EF7B4D"/></svg>')
    assert dark_svg(b"<svg><path d='M0'/></svg>")
    print("ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--self-test"]:
        self_test()
        sys.exit()
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    opt = dict(zip(args[1::2], args[2::2]))
    found = False
    for source, url in candidates(args[0], opt.get("--domain"), opt.get("--github")):
        ok, note = check(url)
        if ok:
            found = True
            print(f"{source:12} {url}  ({note})")
    if not found:
        print("no logo found: use a plain box (or a cloud for an edge/CDN service)")
        sys.exit(1)
