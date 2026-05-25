#!/usr/bin/env python3
"""Generate a skills reference doc from SKILL.md files."""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

MARKER_START = "<!-- skills-table-start -->"
MARKER_END = "<!-- skills-table-end -->"
DETAILS_MARKER_START = "<!-- skills-details-start -->"
DETAILS_MARKER_END = "<!-- skills-details-end -->"


def parse_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}, text
    fields = {}
    current_key = None
    block_lines = []
    for line in match.group(1).splitlines():
        if line.startswith(" ") or line.startswith("\t"):
            # Continuation of a block scalar
            if current_key:
                block_lines.append(line.strip())
        elif ":" in line:
            # Save previous block scalar if any
            if current_key and block_lines:
                fields[current_key] = " ".join(block_lines).strip()
                block_lines = []
            key, _, val = line.partition(":")
            current_key = key.strip()
            val = val.strip()
            if val in ("|", ">", "|-", ">-"):
                block_lines = []
            else:
                fields[current_key] = val
                current_key = None
    if current_key and block_lines:
        fields[current_key] = " ".join(block_lines).strip()
    body = text[match.end():].strip()
    return fields, body


def extract_intro(body):
    """Return text between H1 and the first H2, stripped."""
    # Drop the H1 line
    body = re.sub(r"^#[^#].*\n", "", body, count=1)
    # Take everything up to the next ## heading
    match = re.search(r"\n##\s", body)
    intro = body[:match.start()].strip() if match else body.strip()
    return intro or None


def extract_section(body, heading):
    """Return content of a specific ## section, or None."""
    pattern = rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, body, re.DOTALL)
    return match.group(1).strip() if match else None


def collect_skills():
    skills = []
    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        folder = skill_file.parent.name
        text = skill_file.read_text()
        meta, body = parse_frontmatter(text)
        name = meta.get("name", folder)
        description = meta.get("description", "").strip("|").strip()
        if not description:
            description = "_no description_"
        intro = extract_intro(body) if body else None
        when_to_use = extract_section(body, "When to Use This Skill") if body else None
        skills.append((folder, name, description, intro, when_to_use))
    return skills


def build_table(skills):
    rows = []
    for folder, name, description, _intro, _when in skills:
        invocation = f"`/agent-tools:{folder}`"
        desc_oneline = " ".join(description.splitlines()).strip()
        rows.append((name, invocation, desc_oneline))

    col_widths = [
        max(len(h), max(len(r[i]) for r in rows))
        for i, h in enumerate(("Skill", "Invocation", "Description"))
    ]

    def fmt_row(cells):
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, col_widths)) + " |"

    sep = "| " + " | ".join("-" * w for w in col_widths) + " |"
    lines = [fmt_row(("Skill", "Invocation", "Description")), sep]
    lines += [fmt_row(r) for r in rows]
    return "\n".join(lines)


def build_details(skills):
    sections = []
    for folder, name, description, intro, when_to_use in skills:
        lines = [f"### {name}", "", f"**Invocation:** `/agent-tools:{folder}`", ""]
        if intro:
            lines += [intro, ""]
        if when_to_use:
            lines += ["**When to use:**", "", when_to_use, ""]
        if not intro and not when_to_use:
            lines += ["_No documentation yet._", ""]
        sections.append("\n".join(lines))
    return "\n---\n\n".join(sections)


def inject_between_markers(text, start_marker, end_marker, content):
    pattern = rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}\n\n{content.strip()}\n\n{end_marker}"
    return re.sub(pattern, replacement, text, flags=re.DOTALL)


def update_readme(table, details):
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        print("README.md not found", file=sys.stderr)
        return
    text = readme.read_text()
    text = inject_between_markers(text, MARKER_START, MARKER_END, table)
    text = inject_between_markers(text, DETAILS_MARKER_START, DETAILS_MARKER_END, details)
    readme.write_text(text)
    print(f"Updated README.md")


def main():
    skills = collect_skills()
    if not skills:
        print("No skills found.", file=sys.stderr)
        sys.exit(1)
    table = build_table(skills)
    details = build_details(skills)
    update_readme(table, details)


if __name__ == "__main__":
    main()
