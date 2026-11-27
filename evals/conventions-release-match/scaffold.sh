#!/usr/bin/env bash
# A Node package that already has a semantic-release config, but no release step wired up.
set -euo pipefail
printf 'export function slugify(t) {\n  return t.toLowerCase().split(/\\s+/).join("-");\n}\n' >index.js
cat >package.json <<'JSON'
{
  "name": "slugify",
  "version": "0.0.0-development",
  "type": "module",
  "scripts": { "test": "node --test" },
  "devDependencies": { "semantic-release": "^24.0.0" }
}
JSON
printf '{\n  "branches": ["main"]\n}\n' >.releaserc.json
git init -q -b main
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m "feat: add slugify"
