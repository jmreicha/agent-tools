#!/usr/bin/env python3
"""Record eval results as the baseline, or compare new results against it.

Usage:
  script/eval-baseline.py record evals/results/<run>.json ...
  script/eval-baseline.py compare evals/results/<run>.json ... [--tolerance 0.1]

The baseline lives in evals/baseline.json and is committed, so every change is judged
against the scores the last accepted version earned.
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).parent.parent
BASELINE = REPO / "evals" / "baseline.json"


def _arm(runs):
    # An errored run measures the harness, not the skill, so it doesn't count.
    good = [r for r in runs or [] if not r.get("error")]
    if not good:
        return None, {}, 0
    score = round(sum(r["score"] for r in good) / len(good), 3)
    names = {g["name"] for r in good for g in r["graders"]}
    rates = {n: round(sum(g["passed"] for r in good for g in r["graders"] if g["name"] == n) / len(good), 3) for n in sorted(names)}
    return score, rates, len(good)


def summarize(result):
    out = {}
    for case in result["cases"]:
        with_score, graders, runs = _arm(case["arms"].get("with"))
        without_score, _, _ = _arm(case["arms"].get("without"))
        out[case["name"]] = {
            "with": with_score,
            "without": without_score,
            "runs": runs,
            "graders": graders,
            "claude": result.get("claudeVersion"),
            "started": result.get("startedAt"),
        }
    return out


def record(baseline, results, commit):
    # Newest run wins when several result files cover the same case.
    for result in sorted(results, key=lambda r: r.get("startedAt") or ""):
        for name, summary in summarize(result).items():
            if summary["with"] is not None:
                # A/B runs skip the no-plugin arm, so keep the last no-plugin score we have.
                if summary["without"] is None and name in baseline:
                    summary["without"] = baseline[name].get("without")
                baseline[name] = {**summary, "commit": commit, "recorded": date.today().isoformat()}
    return dict(sorted(baseline.items()))


def compare(baseline, now, tolerance):
    rows, regressed = [], []
    for name in sorted(now):
        cur, base = now[name], baseline.get(name)
        row = {"case": name, "with": cur["with"], "without": cur["without"], "baseline": None, "delta": None, "lost": []}
        if base and cur["with"] is not None:
            row["baseline"] = base["with"]
            row["delta"] = round(cur["with"] - base["with"], 3)
            row["lost"] = sorted(g for g, rate in base["graders"].items() if rate == 1.0 and cur["graders"].get(g, 0) < 1.0)
            if row["delta"] < -tolerance:
                regressed.append(name)
        rows.append(row)
    return rows, regressed


def _fmt(x):
    return "-" if x is None else f"{x:.2f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["record", "compare"])
    ap.add_argument("results", nargs="+", type=Path, help="Result files from claude plugin eval --json")
    ap.add_argument("--tolerance", type=float, default=0.1, help="Allowed drop before a case counts as a regression (default: 0.1)")
    args = ap.parse_args()

    results = [json.loads(p.read_text()) for p in args.results]
    baseline = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}

    if args.action == "record":
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        updated = record(baseline, results, commit)
        BASELINE.write_text(json.dumps(updated, indent=2) + "\n")
        print(f"Recorded {len(updated)} cases in {BASELINE.relative_to(REPO)}")
        return 0

    now = {}
    for result in sorted(results, key=lambda r: r.get("startedAt") or ""):
        now.update(summarize(result))
    rows, regressed = compare(baseline, now, args.tolerance)
    print(f"{'case':34} {'base':>5} {'now':>5} {'delta':>6} {'w/o':>5}  lost graders")
    for r in rows:
        delta = "new" if r["baseline"] is None else f"{r['delta']:+.2f}"
        print(f"{r['case']:34} {_fmt(r['baseline']):>5} {_fmt(r['with']):>5} {delta:>6} {_fmt(r['without']):>5}  {', '.join(r['lost'])}")
    if regressed:
        print(f"Regressed past {args.tolerance}: {', '.join(regressed)}")
    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main())
