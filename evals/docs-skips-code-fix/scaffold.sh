#!/usr/bin/env bash
set -euo pipefail
cat >paginate.py <<'PY'
def pages(items, size):
    return [items[i * size:(i + 1) * size] for i in range(len(items) // size)]
PY
