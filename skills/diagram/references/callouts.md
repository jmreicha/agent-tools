# Step numbers and emphasis

## Step numbers

Number the steps when order matters and the layout doesn't make it obvious: sequences, branches, loops, roughly 4+ steps.
- Badge: `Diagram.badge(n, target)` (style `BADGE`: a 22×22 dark circle with `light-dark()` colors). Every badge is the same size.
- **Placement:** center the badge on the top-left corner of the node that performs the step. A step with no node of its own (a return trip, a hand-off) gets its badge on its arrow, just above the line. Never put a badge on a line or a label.
- **Order:**
  - Count in reading order: left to right, top to bottom, or clockwise.
  - A return trip keeps counting.
  - Parallel steps share the same number, with no letters.
- **Labels:** the badge replaces an edge label that would be self-explanatory.
- **Key:** if steps need explaining, add one numbered key in the note style, in the key row centered below the diagram (see the Key row in SKILL.md), one short line per step.

## Emphasis

When a busy diagram has one detail that matters most (the request path, the failing part, what's changing), color only that detail.
- Use one accent color, `#F62E00`. Add a second accent only to contrast two things.
- Boxes and cards get `strokeColor=#F62E00;strokeWidth=2;`, plus `fillColor=#FDECEA;` if the stroke alone doesn't stand out. Icons keep their color and get a red bold label instead. Arrows get `RED_EDGE` (`strokeColor=#F62E00;strokeWidth=2;` plus red text). Red text, including labels and note titles, uses `RED_TEXT` (`light-dark(#C42500,#FF6A3D)`), because `#F62E00` is too faint for small text.
- Color a whole path end to end, and the badges on it. Color only a few elements. If most of the diagram is red, take the color out.
- Always add a note next to the path (`Diagram.note(..., accent=ACCENT)`), saying what it shows: a 1–3 word title in the accent color plus one line.
- In styled mode, use the brand guide's accent color.
