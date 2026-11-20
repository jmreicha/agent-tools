# Voice

Apply after the rules in SKILL.md. Where this file conflicts with them, this file wins.

- Open with the goal or the problem in one line. Give the number when there is one: "Reduce critical vulnerabilities by 80% by the end of the year."
- Follow a fact or decision with its effect: "This means…", "The goal is…", "This helps…".
- State the scope and the reason for it: "This applies to new vulnerabilities only. The existing backlog would blow up the scope."
- Name who owns each piece of work: "The infrastructure team is responsible for…".
- Split large work into phases, such as the immediate fix and the long-term fix.
- End plans and designs with an open questions section. Say plainly what isn't known yet.
- Use real names and numbers: tools, accounts, counts, and deadlines.
- Say what you tested on, with versions: "Tested on macOS with Docker 18.03.1."
- Call out each gotcha or workaround where it bites, and say why the clean path didn't work.
- Link the canonical upstream doc instead of restating it.
- Be plain and candid. Name the pain directly ("cumbersome", "the barrier to entry is high"), but never insult people or their requests in shared docs.
- Put periods and commas outside quotation marks: `set it to "true".`
- Keep comparison lists as short fragment bullets: "Only supports Terraform." "Python based, a little slow." Rank the options and recommend one.
- Write troubleshooting as the path taken: the exact error, what you checked, what fixed it, and what is still unconfirmed.
- List prerequisites and assumptions before the first step: required access, existing setup, and placeholder values.
- After a snippet, say what to replace and what the important flags do.
- After each step that changes state, show the expected output or a command that verifies it.
- Label insecure or costly shortcuts as test-only, and give the production alternative.
- Back performance and reliability claims with a before-and-after number.
- End a how-to with cleanup and next steps, such as hardening and common failures.
- Match detail to how often a procedure runs. Rare procedures get every step, and common ones can be a link.
- Test a runbook by having a teammate follow it, or reread it a week later.
- Use "we" in docs the team owns: plans, proposals, charters, and ADRs. Use "you" in tutorials, how-tos, and reference.
- Proposals and design docs count as explanation mode, so recommendations and opinions belong there.
