#!/usr/bin/env python3
"""Inline web-hosted images as data URIs so diagrams render offline.

.drawio:      every style `image=https://...`
.excalidraw:  every `files.<id>.dataURL` that is still an http(s) URL

Every draw.io icon lands on the same rounded tile (see tile()). Outline sets with no color of
their own (Cloudflare) pass their brand color as a `#tile=<hex>` suffix on the URL.
"""

import base64
import json
import mimetypes
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from drawio_lib import contrast  # noqa: E402

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


NEUTRAL, DARK = "#F4F4F4", "#232F3E"  # multicolor/raster tile; tile for a glyph too light for its tint
INK = r'(fill|stroke)="(currentColor|#000|#000000|black)"'


def tint(c, amount=0.1):
    """c mixed with white, the pale tile behind a one-color glyph."""
    rgb = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(255 - (255 - v) * amount):02X}" for v in rgb)


def tile(body, ctype, brand=None):
    """Every non-library icon on the same 64px rounded tile, in fixed colors so it reads the
    same in both themes: a one-color glyph in its color on a tint of it, anything else on gray."""
    if ctype != "image/svg+xml":
        uri = f"data:{ctype};base64," + base64.b64encode(body).decode()
        inner, bg = f'<image x="8" y="8" width="48" height="48" href="{uri}"/>', NEUTRAL
    else:
        svg = body.decode()
        vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
        root = re.match(r".*?<svg\b[^>]*>", svg, re.S).group(0)
        inner = svg[len(root):].rsplit("</svg>", 1)[0]
        colors = {c.upper() for c in re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{6})"', svg)} - {"#FFFFFF"}
        if len(colors) > 1:
            inner = f'<svg x="12" y="12" width="40" height="40" viewBox="{vb}">{inner}</svg>'
            bg = NEUTRAL
        else:
            ink = "#" + brand.upper() if brand else (colors.pop() if colors else "#000000")
            inner = re.sub(INK, rf'\1="{ink}"', inner)
            inner = f'<svg x="12" y="12" width="40" height="40" viewBox="{vb}" fill="{ink}" color="{ink}">{inner}</svg>'
            bg = tint(ink) if contrast(ink, tint(ink)) >= 1.5 else DARK
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
            f'<rect width="64" height="64" rx="8" fill="{bg}"/>{inner}</svg>').encode()


def embed_drawio(text, failed):
    def swap(m):
        try:
            url, _, brand = m.group(1).partition("#tile=")
            ctype, body = fetch(url)
            body = tile(body, ctype, brand or None)
            # draw.io expects "data:<type>," + base64, without the ";base64" marker.
            return "iconTile=1;image=data:image/svg+xml," + base64.b64encode(body).decode()
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
    outline = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="currentColor" d="M0"/><path fill="none" d="M1"/><path d="M2"/></svg>'
    out = tile(outline, "image/svg+xml", "F6821F").decode()
    assert 'rx="8" fill="#FEF2E9"' in out and 'fill="#F6821F" color="#F6821F"' in out, out
    assert "currentColor" not in out and 'fill="none"' in out and 'viewBox="0 0 48 48"' in out
    okta = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#007DC1"><path d="M0"/></svg>'
    assert 'fill="#E6F2F9"' in tile(okta, "image/svg+xml").decode()
    vault = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFEC6E"><path d="M0"/></svg>'
    assert 'fill="#232F3E"' in tile(vault, "image/svg+xml").decode(), "a glyph lost on its tint gets a dark tile"
    multi = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 9 9"><path fill="#EF7B4D" d="M0"/><path fill="#2875E2" d="M1"/></svg>'
    out = tile(multi, "image/svg+xml").decode()
    assert 'fill="#F4F4F4"' in out and "#EF7B4D" in out and "#2875E2" in out
    png = b"\x89PNG\r\n\x1a\n" + b"\0" * 16
    assert 'href="data:image/png;base64,' in tile(png, "image/png").decode()
    assert embed_drawio('style="shape=image;image=data:x;"', []) == 'style="shape=image;image=data:x;"'
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
