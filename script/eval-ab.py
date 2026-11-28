#!/usr/bin/env python3
"""A/B test two copies of the plugin on the same eval cases.

Usage:
  script/eval-ab.py <variant dir> --case 'diagram-*' [--case ...] [--a .] [--runs 2] [--concurrency 3] [--tolerance 0.1] [-- extra eval flags]

A is this repo unless --a says otherwise. B is the variant: a full copy of the plugin, such as a
git worktree or an rsync copy with one skill edited. Both arms run at the same time, and the
results land in evals/results/ab-<timestamp>/.
"""

import argparse
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).parent.parent

# Reuse the baseline script's scoring, so A/B and baseline numbers mean the same thing.
_spec = importlib.util.spec_from_file_location("eval_baseline", Path(__file__).parent / "eval-baseline.py")
assert _spec and _spec.loader
eb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eb)


def build_cmd(plugin, case, runs, concurrency, out, extra):
    # Both arms load a plugin, so the no-plugin run would only add cost.
    return [
        "claude", "plugin", "eval", str(plugin), "--case", case, "--runs", runs, "--concurrency", concurrency,
        "--ablation", "none", "--scaffold", "--trust-plugin", "--no-publish",
        "--allow-tools", "Write", "Edit", "Bash", "--json", str(out), *extra,
    ]


def diff(a, b, tolerance):
    return eb.compare(a, b, tolerance)


def _load(paths):
    merged = {}
    for p in paths:
        if p.exists():
            merged.update(eb.summarize(json.loads(p.read_text())))
    return merged


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("variant", type=Path, help="Plugin dir for arm B")
    ap.add_argument("--a", type=Path, default=REPO, help="Plugin dir for arm A (default: this repo)")
    ap.add_argument("--case", action="append", required=True, help="Case glob; repeat for more")
    ap.add_argument("--runs", default="2", help="Runs per case and arm (default: 2)")
    ap.add_argument("--concurrency", default="3", help="Agent runs at once per arm (default: 3)")
    ap.add_argument("--tolerance", type=float, default=0.1, help="Drop in B that counts as worse (default: 0.1)")
    args, extra = ap.parse_known_args()
    extra = [a for a in extra if a != "--"]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = REPO / "evals" / "results" / f"ab-{stamp}"
    out_dir.mkdir(parents=True)

    def arm(name, plugin):
        outs = []
        for i, case in enumerate(args.case):
            out = out_dir / f"{name}-{i}.json"
            cmd = build_cmd(plugin.resolve(), case, args.runs, args.concurrency, out, extra)
            log = subprocess.run(cmd, cwd=plugin, capture_output=True, text=True)
            (out_dir / f"{name}-{i}.log").write_text(log.stdout + log.stderr)
            outs.append(out)
        return outs

    with ThreadPoolExecutor(max_workers=2) as pool:
        a_out, b_out = pool.map(lambda x: arm(*x), [("a", args.a), ("b", args.variant)])

    rows, worse = diff(_load(a_out), _load(b_out), args.tolerance)
    print(f"A: {args.a}\nB: {args.variant}\nResults: {out_dir.relative_to(REPO)}\n")
    print(f"{'case':34} {'A':>5} {'B':>5} {'delta':>6}  graders B lost")
    for r in rows:
        delta = "-" if r["delta"] is None else f"{r['delta']:+.2f}"
        print(f"{r['case']:34} {eb._fmt(r['baseline']):>5} {eb._fmt(r['with']):>5} {delta:>6}  {', '.join(r['lost'])}")
    if worse:
        print(f"B is worse past {args.tolerance}: {', '.join(worse)}")
    return 1 if worse else 0


if __name__ == "__main__":
    sys.exit(main())
