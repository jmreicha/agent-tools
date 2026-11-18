# Step numbers and emphasis

## Step numbers

Number the steps when order matters and the layout doesn't make it obvious: sequences, branches, loops, roughly 4+ steps.
- Badge: `ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#1e1e1e;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=11;` at 22×22. Every badge is the same size.
- **Placement:** put the badge on the top-left corner of the node that performs the step, offset about 14px. A step with no node of its own (a return trip, a hand-off) gets its badge on its arrow, just above the line. Never put a badge on a line or a label.
- **Order:**
  - Count in reading order: left to right, top to bottom, or clockwise.
  - A return trip keeps counting.
  - Parallel steps share the same number, with no letters.
- **Labels:** the badge replaces an edge label that would be self-explanatory.
- **Key:** if steps need explaining, add one numbered key as free text in a corner, one short line per step.

## Emphasis

When a busy diagram has one detail that matters most (the request path, the failing part, what's changing), color only that detail.
- Use one accent color, `#F62E00`. Add a second accent only to contrast two things.
- Boxes get `strokeColor=#F62E00;strokeWidth=2;`, plus `fillColor=#FDECEA;` if the stroke alone doesn't stand out. Arrows get `strokeColor=#F62E00;strokeWidth=2;fontColor=#F62E00;`.
- Color a whole path end to end, and the badges on it. Color only a few elements. If most of the diagram is red, take the color out.
- Always add a sticky note next to the path, saying what it shows: a bold 1–3 word title plus one line.
- In styled mode, use the brand guide's accent color.
