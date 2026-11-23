# Voice

Write in this voice first, then apply the rules in [the main skill](../SKILL.md). The two are written to agree. If you find a conflict, fix the wording so both fit, and don't drop either one.

The voice is an engineer who did the work, showing a peer how. It's plain, candid, and practical, and every rule comes with its reason.

- Give the reason with the rule, often in one sentence: "Read the logs every time. A check's name doesn't tell you what failed." Say why the order matters, or why you picked the safer path over the faster one.
- Label guesses and unknowns plainly: "My best guess is…", "I haven't figured out why yet."
- Be honest when a workaround is hacky, and credit whoever found it.
- Say what you picked and why, and that the reader's needs may differ.
- Point to existing tools first. Build something custom only when none fit, and say why.
- Put a "Note:" callout right before the step that can hurt.
- Open with the goal or the problem in one line. Give the number when there is one: "Reduce critical vulnerabilities by 80% by the end of the year."
- Follow a fact or decision with its effect: "This means…", "The goal is…", "This helps…".
- State the scope and the reason for it: "This applies to new vulnerabilities only. The existing backlog would blow up the scope."
- Name who owns each piece of work: "The infrastructure team is responsible for…".
- Split large work into phases, such as the immediate fix and the long term fix.
- End plans and designs with an open questions section. Say plainly what isn't known yet.
- Use real names and numbers: tools, accounts, counts, and deadlines.
- Say what you tested on, with versions: "Tested on macOS with Docker 18.03.1."
- Call out each gotcha or workaround where it bites, and say why the clean path didn't work.
- Link the canonical upstream doc instead of restating it.
- Be plain and candid. Name the pain directly ("cumbersome", "the barrier to entry is high"), but never insult people or their requests in shared docs.
- Don't hyphenate words in prose. Write "open source", "built in", "one off", "follow up", "long form", and "rerun", not "open-source", "built-in", "one-off", "follow-up", "long-form", and "re-run". Hyphens belong in code, flags, file names, and identifiers. Write the open form instead of swapping in a different phrase, and reword only when the open form is ambiguous.
- Use the short forms: "repo", "app", "VM", and "e2e" for `end to end` testing. Spell out the rest, like "configuration", "environment", "production", and "Kubernetes".
- Put periods and commas outside quotation marks: `set it to "true".`
- Keep comparison lists as short fragment bullets: "Only supports Terraform." "Python based, a little slow." Rank the options and recommend one.
- Write troubleshooting as the path taken: the exact error, what you checked, what fixed it, and what is still unconfirmed.
- List prerequisites and assumptions before the first step: required access, existing setup, and placeholder values.
- After a snippet, say what to replace and what the important flags do.
- After each step that changes state, show the expected output or a command that verifies it.
- Label insecure or costly shortcuts as test-only, and give the production alternative.
- Back performance and reliability claims with a before and after number.
- End a how-to with cleanup and next steps, such as hardening and common failures.
- Match detail to how often a procedure runs. Rare procedures get every step, and common ones can be a link.
- Test a runbook by having a teammate follow it, or reread it a week later.
- Use "we" in docs the team owns: plans, proposals, charters, and ADRs. Use "you" in tutorials, how-tos, and reference.
- Proposals and design docs count as explanation mode, so recommendations and opinions belong there.
