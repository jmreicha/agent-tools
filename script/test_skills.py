"""Structural checks on skills/, so a rename or a dead link fails before an agent hits it."""

import re
from pathlib import Path

SKILLS = Path(__file__).parent.parent / "skills"
FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
SKILL_REF = re.compile(r"agent-tools:([a-z0-9-]+)")
LOCAL_LINK = re.compile(r"\]\((?![a-z]+:|#|/)([^)#]+)")


def skill_files():
    return sorted(SKILLS.glob("*/SKILL.md"))


def field(f, key):
    meta = FRONTMATTER.match(f.read_text())
    value = meta and re.search(rf"^{key}:\s*(.+)", meta.group(1), re.M)
    assert value, f"{f}: no {key} in frontmatter"
    return value.group(1)


# Kept by choice; add a name here only with the owner's approval.
MULTI_WORD_OK = {"rubber-duck"}


def test_name_is_one_word_matching_folder():
    for f in skill_files():
        name = field(f, "name")
        # One word keeps /agent-tools:<name> short and the folder and name in sync.
        one_word = re.fullmatch(r"[a-z0-9]+", name) or name in MULTI_WORD_OK
        assert one_word, f"{f}: name {name!r} is not one word"
        assert name == f.parent.name, f"{f}: name {name!r} != folder"


def test_description_fits():
    for f in skill_files():
        desc = field(f, "description")
        # Claude Code truncates longer descriptions, which hurts triggering.
        assert 20 <= len(desc) <= 1024, f"{f}: description is {len(desc)} chars"


def test_skill_references_resolve():
    names = {f.parent.name for f in skill_files()}
    for f in SKILLS.rglob("*.md"):
        for ref in SKILL_REF.findall(f.read_text()):
            assert ref in names, f"{f}: agent-tools:{ref} has no skill folder"


def test_local_links_resolve():
    for f in SKILLS.rglob("*.md"):
        # Links inside code are examples, not navigation.
        prose = re.sub(r"```.*?```|`[^`\n]*`", "", f.read_text(), flags=re.DOTALL)
        for target in LOCAL_LINK.findall(prose):
            assert (f.parent / target).exists(), f"{f}: broken link {target}"


if __name__ == "__main__":
    test_name_is_one_word_matching_folder()
    test_description_fits()
    test_skill_references_resolve()
    test_local_links_resolve()
    print("ok")
