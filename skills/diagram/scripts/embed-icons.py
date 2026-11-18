#!/usr/bin/env python3
"""Inline web-hosted images as data URIs so diagrams render offline.

.drawio:      every style `image=https://...`
.excalidraw:  every `files.<id>.dataURL` that is still an http(s) URL
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


def embed_drawio(text, failed):
    def swap(m):
        try:
            ctype, body = fetch(m.group(1))
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: embed-icons.py <file.drawio|file.excalidraw>...")
    bad = [f for p in sys.argv[1:] for f in embed(p)]
    for f in bad:
        print("FAILED", f, file=sys.stderr)
    sys.exit(1 if bad else 0)
