import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("eb", Path(__file__).parent / "eval-baseline.py")
eb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eb)


def run(score, graders):
    return {"score": score, "error": None, "graders": [{"name": n, "passed": p, "scored": True} for n, p in graders]}


def result(case, started, with_runs, without_runs):
    arms = {"with": with_runs}
    if without_runs is not None:
        arms["without"] = without_runs
    return {"claudeVersion": "2.1.332", "startedAt": started, "cases": [{"name": case, "arms": arms}]}


def test_summary_averages_runs_and_grader_pass_rates():
    r = result("docs-readme", "2026-11-28T01:00:00Z", [run(1.0, [("a", True)]), run(0.5, [("a", False)])], [run(0.25, [])])
    s = eb.summarize(r)["docs-readme"]
    assert s["with"] == 0.75 and s["without"] == 0.25 and s["runs"] == 2
    assert s["graders"] == {"a": 0.5}


def test_errored_runs_are_left_out_of_the_score():
    errored = {"score": 0, "error": "Not logged in", "graders": []}
    s = eb.summarize(result("x", "t", [run(1.0, []), errored], None))["x"]
    assert s["with"] == 1.0 and s["runs"] == 1 and s["without"] is None


def test_record_keeps_the_newest_result_per_case():
    old = result("x", "2026-11-27T00:00:00Z", [run(0.5, [])], None)
    new = result("x", "2026-11-28T00:00:00Z", [run(1.0, [])], None)
    assert eb.record({}, [new, old], "abc123")["x"]["with"] == 1.0


def test_compare_flags_a_drop_past_tolerance_and_names_lost_graders():
    base = {"x": {"with": 1.0, "without": 0.5, "graders": {"a": 1.0, "b": 1.0}}}
    now = {"x": {"with": 0.5, "without": 0.5, "graders": {"a": 1.0, "b": 0.0}}}
    rows, regressed = eb.compare(base, now, tolerance=0.1)
    assert regressed == ["x"]
    assert rows[0]["lost"] == ["b"]


def test_compare_ignores_noise_inside_tolerance_and_new_cases():
    base = {"x": {"with": 1.0, "without": 0.5, "graders": {}}}
    now = {"x": {"with": 0.95, "without": 0.5, "graders": {}}, "y": {"with": 0.3, "without": None, "graders": {}}}
    rows, regressed = eb.compare(base, now, tolerance=0.1)
    assert regressed == []
    assert [r["case"] for r in rows] == ["x", "y"] and rows[1]["baseline"] is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
