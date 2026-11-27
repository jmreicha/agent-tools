#!/usr/bin/env bash
# A small CLI with real flags, so the README can be checked against the source.
set -euo pipefail
cat >tidyup.py <<'PY'
"""Delete files older than a cutoff from a folder."""
import argparse, sys, time
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(prog="tidyup", description=__doc__)
    p.add_argument("path", type=Path, help="Folder to clean")
    p.add_argument("--older-than", type=int, default=30, metavar="DAYS", help="Age cutoff in days (default: 30)")
    p.add_argument("--dry-run", action="store_true", help="Print what would be deleted, delete nothing")
    args = p.parse_args(argv)
    cutoff = time.time() - args.older_than * 86400
    for f in sorted(args.path.rglob("*")):
        if f.is_file() and f.stat().st_mtime < cutoff:
            print(f"delete {f}")
            if not args.dry_run:
                f.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
printf 'requires-python = ">=3.10"\n' >pyproject.toml
