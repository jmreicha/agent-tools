# Skill evals

These cases check that the skills fire on the right requests and make the output better than Claude does without them. Each case runs twice, once with the plugin and once without, and the report shows the score difference (`Δ`).

## Run the suite

Run every case from the repo root. Scaffold scripts create the fixture files, so pass `--scaffold`.

```bash
claude plugin eval . --scaffold --trust-plugin --no-publish \
  --allow-tools Write Edit Bash --max-cost-usd 20
```

Run one case, once, while you work on a skill:

```bash
claude plugin eval . --case docs-readme --runs 1 --scaffold --trust-plugin --no-publish \
  --allow-tools Write Edit Bash
```

Run only the cases for skills you changed since `main`, once each. A case runs when its `tags` name a changed skill, or when its own files changed:

```bash
script/eval-changed.py
script/eval-changed.py --base origin/main --runs 3 -- --threshold 0.8
pre-commit run eval-changed --hook-stage manual
```

Add `--dry-run` to print the commands without running them. Flags after `--` go straight to `claude plugin eval`. The script exits 1 when a case scores below the threshold, which defaults to 1.0.

Results and the HTML report go to `evals/results/`, which git ignores. Each run is a full Claude session on your account, so the cost is cases × runs × 2 arms. A single run of one case costs about $0.20.

## Compare two versions of a skill

The default comparison is the plugin against no plugin. To compare the old and new versions of a skill, run the same case on both git refs and compare the scores:

```bash
git worktree add /tmp/agent-tools-old main
claude plugin eval /tmp/agent-tools-old --case 'docs-*' --scaffold --trust-plugin --no-publish --allow-tools Write Edit Bash
claude plugin eval . --case 'docs-*' --scaffold --trust-plugin --no-publish --allow-tools Write Edit Bash
git worktree remove /tmp/agent-tools-old
```

Pin `--model` and `--judge-model` when you compare runs, so a model change doesn't look like a skill change.

## Cases

| Case                             | Checks                                                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `docs-readme`                    | A README for a small CLI: real flags only, a copyable first run, and no filler words                                            |
| `docs-pr-body`                   | A PR description that reads as a one-minute briefing                                                                            |
| `docs-skips-code-fix`            | A code-only bug fix, where neither `docs` nor `diagram` fires                                                                   |
| `diagram-aws-drawio`             | An AWS draw.io diagram from a short description: one page, AWS icons, the style contract, and `check-layout.py`                 |
| `diagram-mermaid`                | A short Mermaid flowchart with terse labels and no color styling                                                                |
| `diagram-adapt-key`              | Extend someone else's diagram: every line stays in its key, nothing else changes, and existing problems get reported, not fixed |
| `conventions-strta`              | A repo with code but no entry points: a `script/` dir with verbs and CI that calls it                                           |
| `conventions-make`               | A repo on make: the lint step goes in the `Makefile` in its style, with no `script/` dir, and one offer to migrate              |
| `conventions-skips-bug-fix`      | A code-only bug fix, where the conventions skill must not fire                                                                  |
| `conventions-release-greenfield` | No release tooling: cocogitto with `cog.toml`, a `cog verify` commit-msg hook, and `script/release`                             |
| `conventions-release-match`      | An existing semantic-release config is kept, with no cocogitto added                                                            |
| `terraform-count-to-foreach`     | A deployed module switched from `count` to `for_each`: `moved` blocks keep every subnet, no state commands                      |
| `terraform-db-secret`            | A new RDS instance: the password stays out of state, and the instance is locked down                                            |
| `terraform-optional-defaults`    | New module settings become an object variable with `optional()` defaults, read directly in `main.tf`                            |
| `terraform-tofu-enabled`         | An OpenTofu 1.11 on/off resource uses `lifecycle { enabled }`, not `count`                                                      |
| `terraform-emulator-test`        | An apply test for a bucket module runs against AWS Emulator, not a real account                                                 |
| `adr-greenfield`                 | No ADRs yet: the first one lands in `docs/adrs` with `adrs.toml`, and records the rejected option and the costs                 |
| `adr-match`                      | Existing MADR records in `docs/decisions`: the new one takes the next number, the same folder, and the MADR sections            |
| `spec-greenfield`                | No specs yet: the yass process starts with proposed answers, and no code before the user approves                               |
| `spec-match`                     | Existing Gherkin features: the new behavior is a `.feature` file in their style, with no yass files                             |
| `review-risky-migration`         | A one-way-door migration with no tests: review grades merge risk high and names each risk                                       |
| `review-docs-only`               | A README typo fix: review grades it low and doesn't invent risk                                                                 |
| `refactor-pins-bug`              | A dedupe that hides a `>` versus `>=` mismatch: behavior stays, the bug gets a pinned and a skipped test                        |

## Write a new case

- Write the prompt the way a user would ask. Don't use words like "eval", "test", or "rubric" in it, because a model that knows it's being graded behaves differently.
- Prefer free graders (`regex`, `tool_used`, `file_exists`) for anything a pattern can check. Use an `llm` grader for judgment, and spell out the PASS and FAIL conditions.
- Give each skill at least one case where it must not fire, with `min: 0`, `max: 0`, and `arm: both`.
- Give each case one requirement. A case that bundles several fails more often than any of them, and its failure doesn't say which one broke. Split it into one grader per criterion at least.
- Check each thing with the cheapest grader that can decide it. A judge asked what a regex could decide costs a call and adds noise. A regex that guesses at meaning fails good replies.
- Give an `llm` judge everything it needs to decide: the source, the config, and the facts. A judge that can't see the source marks true claims as invented.
- One requirement per `llm` grader. A judge that checks four things in a long file splits its votes. When a file runs past a few thousand characters, pass `--judge-model sonnet`.
- `file_exists` globs skip dotfiles, and the eval sandbox blocks writes to `.pre-commit-config.yaml`. Check either through the trace instead.
- `--case` takes one glob, and a repeated `--case` keeps only the last. It doesn't support `[...]` classes.
- Read the outputs yourself when a score surprises you. A judge can be wrong, and a vague grader is worse than none.

See the [plugin evals docs](https://code.claude.com/docs/en/plugin-evals) for every grader option.
