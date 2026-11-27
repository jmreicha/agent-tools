---
type: llm
weight: 2
focus: { source: file, path: README.md }
---

This is the full source of `tidyup.py`, the tool the README documents.

```python
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
```

The folder also has a `pyproject.toml` with `requires-python = ">=3.10"`, so "Python 3.10 or later" is supported. A claim about what happens on an error, such as stopping at the first file it can't delete, is supported when the code has no error handling for it.

PASS if every claim in the README is supported by this source. Behavior that follows from the code counts as supported, such as recursing into subfolders, deleting files only, and the `--help` flag that argparse adds. The default for `--older-than` must be 30.

FAIL if the README states any flag, config file, install step, default, or behavior that the source doesn't support.
