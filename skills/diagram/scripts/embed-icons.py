#!/usr/bin/env python3
"""Inline web-hosted images as data URIs so diagrams render offline.

.drawio:      every style `image=https://...`
.excalidraw:  every `files.<id>.dataURL` that is still an http(s) URL

A `#tile=<tile hex>[,<glyph hex>]` suffix on an SVG URL puts a one-color glyph (white by default)
on a rounded tile, for vendors that ship only outline icons (Cloudflare).
"""

import base64
import json
import mimetypes
import re
import sys
import urllib.parse
import urllib.request

# Icon CDNs reject urllib's default user agent.
UA = {"User-Agent": "Mozilla/5.0"}
IMG = re.compile(r"image=(https?://[^;\"]+)")


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        ctype = r.headers.get_content_type()
        body = r.read()
    # Some hosts serve images as octet-stream or text/plain; trust the file extension then.
    if not ctype.startswith("image/"):
        ctype = mimetypes.guess_type(urllib.parse.urlparse(url).path)[0] or ctype
    if not ctype.startswith("image/"):
        raise ValueError(f"returned {ctype}, not an image")
    return ctype, body


def tile(svg, colors):
    """Glyph on a 64px rounded tile, fixed colors so it reads the same in both themes.
    colors is "<tile>" (white glyph) or "<tile>,<glyph>"."""
    color, _, ink = colors.partition(",")
    ink = "#" + ink if ink else "#ffffff"
    svg = svg.decode()
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    inner = re.sub(r"^.*?<svg\b[^>]*>|</svg>\s*$", "", svg, flags=re.S)
    # Outline sets draw in black or currentColor; both become the glyph color.
    inner = re.sub(r'(fill|stroke)="(currentColor|#000|#000000|black)"', rf'\1="{ink}"', inner)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
            f'<rect width="64" height="64" rx="8" fill="#{color}"/>'
            f'<svg x="12" y="12" width="40" height="40" viewBox="{vb}" fill="{ink}" color="{ink}">'
            f"{inner}</svg></svg>").encode()


def embed_drawio(text, failed):
    def swap(m):
        try:
            url, _, frag = m.group(1).partition("#tile=")
            ctype, body = fetch(url)
            if frag:
                body = tile(body, frag)
            # draw.io expects "data:<type>," + base64, without the ";base64" marker.
            return f"image=data:{ctype}," + base64.b64encode(body).decode()
        except Exception as e:
            failed.append(f"{m.group(1)}: {e}")
            return m.group(0)

    return IMG.sub(swap, text)


def embed_excalidraw(text, failed):
    scene = json.loads(text)
    for f in scene.get("files", {}).values():
        url = f.get("dataURL", "")
        if not url.startswith("http"):
            continue
        try:
            ctype, body = fetch(url)
            if ctype == "image/svg+xml":
                # Excalidraw mis-scales SVGs that only have a viewBox.
                svg = body.decode()
                body = re.sub(r"<svg\b(?![^>]*\bwidth=)", '<svg width="256" height="256"', svg, count=1).encode()
            f["mimeType"] = ctype
            f["dataURL"] = f"data:{ctype};base64," + base64.b64encode(body).decode()
        except Exception as e:
            failed.append(f"{url}: {e}")
    return json.dumps(scene)


def embed(path):
    failed = []
    text = open(path).read()
    out = embed_excalidraw(text, failed) if path.endswith(".excalidraw") else embed_drawio(text, failed)
    open(path, "w").write(out)
    return failed


def self_test():
    g = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="currentColor" d="M0"/><path fill="none" d="M1"/><path d="M2"/></svg>'
    out = tile(g.encode(), "F38020").decode()
    assert '<rect width="64" height="64" rx="8" fill="#F38020"/>' in out, out
    assert 'viewBox="0 0 48 48"' in out and 'fill="#ffffff"' in out
    assert "currentColor" not in out and 'fill="none"' in out
    out = tile(g.encode(), "FEF4E6,F6821F").decode()
    assert 'fill="#FEF4E6"/>' in out and 'fill="#F6821F" color="#F6821F"' in out, out
    print("ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        sys.exit()
    if len(sys.argv) < 2:
        sys.exit("usage: embed-icons.py <file.drawio|file.excalidraw>...")
    bad = [f for p in sys.argv[1:] for f in embed(p)]
    for f in bad:
        print("FAILED", f, file=sys.stderr)
    sys.exit(1 if bad else 0)
