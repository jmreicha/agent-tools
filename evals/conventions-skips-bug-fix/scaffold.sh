#!/usr/bin/env bash
# A plain bug fix: no structural work, so the repo skill must not fire.
set -euo pipefail
cat >chunk.py <<'PY'
"""Split a list into fixed-size chunks."""


def chunk(items, size):
    return [items[i:i + size] for i in range(0, len(items) // size * size, size)]
PY
