#!/usr/bin/env bash
# A small service repo with a README and no decision records.
set -euo pipefail
mkdir -p src/orders docs
printf '# Orders service\n\nTakes and tracks customer orders.\n' >README.md
printf '"""Orders service."""\n' >src/orders/__init__.py
printf '# Runbook\n\nRestart the service with systemctl.\n' >docs/runbook.md
