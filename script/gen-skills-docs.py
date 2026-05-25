#!/usr/bin/env python3
"""Generate a skills reference table from SKILL.md frontmatter."""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
OUTPUT_FILE = REPO_ROOT / "docs" / "skills.md"

MARKER_START = "<!-- skills-table-start -->"
MARKER_END = "<!-- skills-table-end -->"


def parse_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip()
    return fields


def collect_skills():
    skills = []
    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        folder = skill_file.parent.name
        text = skill_file.read_text()
        meta = parse_frontmatter(text)
        name = meta.get("name", folder)
        description = meta.get("description", "").strip("|").strip()
        if not description:
            description = "_no description_"
        skills.append((folder, name, description))
    return skills


def build_table(skills):
    lines = [
        "| Skill | Invocation | Description |",
        "| ----- | ---------- | ----------- |",
    ]
    for folder, name, description in skills:
        invocation = f"`/agent-tools:{folder}`"
        lines.append(f"| {name} | {invocation} | {description} |")
    return "\n".join(lines)


def write_output(table):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = f"# Skills\n\n{MARKER_START}\n{table}\n{MARKER_END}\n"
    OUTPUT_FILE.write_text(content)
    print(f"Written to {OUTPUT_FILE.relative_to(REPO_ROOT)}")


def main():
    skills = collect_skills()
    if not skills:
        print("No skills found.", file=sys.stderr)
        sys.exit(1)
    table = build_table(skills)
    write_output(table)


if __name__ == "__main__":
    main()
