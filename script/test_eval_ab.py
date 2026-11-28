import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ab", Path(__file__).parent / "eval-ab.py")
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)


def test_each_arm_runs_the_same_cases_with_only_the_plugin_dir_changed():
    a = ab.build_cmd("/repo", "diagram-*", runs="2", concurrency="3", out="a.json", extra=[])
    b = ab.build_cmd("/variant", "diagram-*", runs="2", concurrency="3", out="b.json", extra=[])
    assert a[3] == "/repo" and b[3] == "/variant"
    strip = lambda c: [x for x in c if x not in ("/repo", "/variant", "a.json", "b.json")]
    assert strip(a) == strip(b)


def test_arms_skip_the_no_plugin_run_since_both_sides_have_a_plugin():
    cmd = ab.build_cmd("/repo", "x", runs="1", concurrency="2", out="a.json", extra=[])
    assert cmd[cmd.index("--ablation") + 1] == "none"


def test_report_flags_cases_where_b_is_worse_past_tolerance():
    a = {"x": {"with": 1.0, "without": None, "graders": {"g": 1.0}}, "y": {"with": 0.5, "without": None, "graders": {}}}
    b = {"x": {"with": 0.5, "without": None, "graders": {"g": 0.0}}, "y": {"with": 1.0, "without": None, "graders": {}}}
    rows, worse = ab.diff(a, b, tolerance=0.1)
    assert worse == ["x"]
    assert {r["case"]: r["delta"] for r in rows} == {"x": -0.5, "y": 0.5}
    assert rows[0]["lost"] == ["g"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
