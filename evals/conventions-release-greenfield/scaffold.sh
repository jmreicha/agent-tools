#!/usr/bin/env bash
# A small Python package with tests and git history, but no release tooling.
set -euo pipefail
mkdir -p src/slugify tests
printf '"""Turn titles into URL slugs."""\n\n\ndef slugify(title):\n    return "-".join(title.lower().split())\n' >src/slugify/__init__.py
printf 'from slugify import slugify\n\n\ndef test_slugify():\n    assert slugify("Hello World") == "hello-world"\n' >tests/test_slugify.py
printf '[project]\nname = "slugify"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n' >pyproject.toml
git init -q -b main
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m "feat: add slugify"
