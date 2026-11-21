import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("gen", Path(__file__).parent / "gen-skills-docs.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_relative_links_point_into_skill_folder():
    text = "Read [voice](references/voice.md), [x](https://x.io), [a](#anchor), and [r](/README.md)."
    assert gen.rebase_links(text, "docs") == (
        "Read [voice](skills/docs/references/voice.md), [x](https://x.io), [a](#anchor), and [r](/README.md)."
    )


def test_section_heading_match_ignores_case():
    body = "## When to use this skill\n\n- Writing docs\n\n## Next\n"
    assert gen.extract_section(body, "When to Use This Skill") == "- Writing docs"


def test_detail_heading_is_code():
    out = gen.build_details([("docs", "docs", "desc", None, None)])
    assert "### `docs`" in out


if __name__ == "__main__":
    test_detail_heading_is_code()
    test_relative_links_point_into_skill_folder()
    test_section_heading_match_ignores_case()
    print("ok")
