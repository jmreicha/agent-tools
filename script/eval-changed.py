#!/usr/bin/env python3
"""Run the eval cases for skills changed since a base ref.

Usage: script/eval-changed.py [--base main] [--runs 1] [--max-cost-usd 5] [--dry-run] [-- extra eval flags]
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
EVALS = REPO / "evals"


def parse_tags(text):
    match = re.search(r"^tags:\s*\[([^\]]*)\]", text, re.M)
    return {t.strip() for t in match.group(1).split(",") if t.strip()} if match else set()


def load_cases():
    return {p.parent.name: parse_tags(p.read_text()) for p in sorted(EVALS.glob("*/prompt.md"))}


def select_cases(paths, cases):
    skills, picked = set(), set()
    for path in paths:
        parts = Path(path).parts
        if len(parts) > 2 and parts[0] == "skills":
            skills.add(parts[1])
        elif len(parts) > 2 and parts[0] == "evals" and parts[1] in cases:
            picked.add(parts[1])
    picked |= {name for name, tags in cases.items() if tags & skills}
    return sorted(picked)


def changed_paths(base):
    git = lambda *a: subprocess.run(["git", *a], cwd=REPO, check=True, capture_output=True, text=True).stdout.split()
    merge_base = git("merge-base", "HEAD", base)[0]
    # Uncommitted and untracked work counts, so this runs before the first commit too.
    return git("diff", "--name-only", merge_base) + git("ls-files", "--others", "--exclude-standard")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="main", help="Git ref to compare against (default: main)")
    ap.add_argument("--runs", default="1", help="Runs per case and arm (default: 1)")
    ap.add_argument("--max-cost-usd", default="5", help="Cost ceiling per case (default: 5)")
    ap.add_argument("--dry-run", action="store_true", help="Print the commands, run nothing")
    args, extra = ap.parse_known_args()
    extra = [a for a in extra if a != "--"]

    cases = select_cases(changed_paths(args.base), load_cases())
    if not cases:
        print(f"No eval cases cover the changes since {args.base}.")
        return 0

    failed = []
    for case in cases:
        cmd = [
            "claude", "plugin", "eval", ".", "--case", case, "--runs", args.runs,
            "--max-cost-usd", args.max_cost_usd, "--scaffold", "--trust-plugin", "--no-publish",
            "--allow-tools", "Write", "Edit", "Bash", *extra,
        ]
        print("+", " ".join(cmd), flush=True)
        if not args.dry_run and subprocess.run(cmd, cwd=REPO).returncode != 0:
            failed.append(case)

    if failed:
        print(f"Below threshold or errored: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
