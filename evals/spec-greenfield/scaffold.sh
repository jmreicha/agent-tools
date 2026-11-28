#!/usr/bin/env bash
# A small Flask-style API with no specs.
set -euo pipefail
mkdir -p api tests
printf '"""Public API."""\n\n\ndef handle(request):\n    return {"status": 200}\n' >api/__init__.py
printf 'from api import handle\n\n\ndef test_handle():\n    assert handle({})["status"] == 200\n' >tests/test_api.py
printf '# API\n\nThe public API.\n' >README.md
