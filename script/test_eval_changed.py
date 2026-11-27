import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ec", Path(__file__).parent / "eval-changed.py")
ec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ec)

CASES = {
    "docs-readme": {"docs"},
    "docs-skips-code-fix": {"docs", "diagram", "negative"},
    "diagram-mermaid": {"diagram"},
}


def test_skill_change_selects_cases_tagged_with_it():
    assert ec.select_cases(["skills/diagram/SKILL.md"], CASES) == ["diagram-mermaid", "docs-skips-code-fix"]


def test_case_change_selects_only_that_case():
    assert ec.select_cases(["evals/docs-readme/graders/x.md"], CASES) == ["docs-readme"]


def test_unrelated_change_selects_nothing():
    assert ec.select_cases(["README.md", "skills/terraform/SKILL.md", "evals/README.md"], CASES) == []


def test_tags_parse_from_prompt_frontmatter():
    text = "---\ndescription: x\ntags: [docs, negative]\nmax_turns: 5\n---\n\nprompt\n"
    assert ec.parse_tags(text) == {"docs", "negative"}


if __name__ == "__main__":
    test_skill_change_selects_cases_tagged_with_it()
    test_case_change_selects_only_that_case()
    test_unrelated_change_selects_nothing()
    test_tags_parse_from_prompt_frontmatter()
    print("ok")
