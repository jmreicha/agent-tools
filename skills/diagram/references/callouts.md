# Step numbers and emphasis

## Step numbers

Number the steps when order matters and the layout doesn't make it obvious: sequences, branches, loops, roughly 4+ steps.
Also number pieces a reader can't work out from their labels (jobs, sync loops, schedules, ownership or retry rules), even when order doesn't matter.

- **Which pages:** badges go on any page whose numbered `How it works` note explains them (Brief, Network, Full). Security uses severity chips instead, so it has no badges.
- Badge: `Diagram.badge(n, target)` (style `BADGE`: a 22×22 dark circle with `light-dark()` colors). Every badge is the same size.
- **Placement:** center the badge on the top-left corner of the node that performs the step (bottom-left when its label is on top). `badge()` does this, and check-layout flags a badge on a label). A step with no node of its own (a return trip, a handoff) gets its badge on its arrow, just above the line. Never put a badge on a line or a label.
- **Order:**
  - Count in reading order: left to right, top to bottom, or clockwise.
  - A return trip keeps counting.
  - Parallel steps share the same number, with no letters.
- **Labels:** the badge replaces an edge label that would be self explanatory.
- **How it works:** explain the numbered pieces in one note titled `How <it> works`, beside the diagram on the right, level with the pieces it explains. Pass the steps to `note()` as `(number, text)` pairs, one sentence or two each: it renders a numbered list with hanging indents that wraps to the box, keeps the badge numbers (3, 4, 7…), and leaves a blank line under the title. Don't break lines by hand. Give the facts a reader can't see: schedule, what it reads and writes, what it decides, and where failures go.
- **Every page:** if a piece is numbered on one page, number it the same way on every page that shows it (Brief and Full alike).

## Emphasis

When a busy diagram has one detail that matters most (the request path, the failing part, what's changing), color only that detail. Network diagrams skip color emphasis: their line colors already mean traffic types, so mark the detail with a label (`(new)`) or a note.

- Use one accent color, `#F62E00`. Add a second accent only to contrast two things.
- Boxes and cards get `strokeColor=#F62E00;strokeWidth=2;`, plus `fillColor=#FDECEA;` if the stroke alone doesn't stand out. Icons keep their color and get a red bold label instead. Arrows get `RED_EDGE` (`strokeColor=#F62E00;strokeWidth=2;` plus red text). Red text, including labels and note titles, uses `RED_TEXT` (`light-dark(#C42500,#FF6A3D)`), because `#F62E00` is too faint for small text.
- Color a whole path from start to finish, and the badges on it. Color only a few elements. If most of the diagram is red, take the color out.
- Always add a note next to the path (`Diagram.note(..., accent=ACCENT)`), saying what it shows: a 1-3 word title in the accent color plus one line.
- In styled mode, use the brand guide's accent color.
