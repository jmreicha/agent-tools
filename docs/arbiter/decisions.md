# arbiter: Decisions

Lightweight ADRs. Newest last. Status is one of: accepted, superseded, proposed.

---

## Build as a mod, not settings hooks

**Status:** accepted · 2026-10-04

**Context.** Settings `PreToolUse` hooks can block tool calls but spawn a process per call and
can't draw UI or register commands. Native permission rules only glob-match and give Claude no
reason or alternative. Mods run in-process, can deny with a message, ask the user
(`$.ui.ask`), add commands, draw panes, and fail closed via `.catch`.

**Decision.** Implement arbiter as a mod inside the existing `agent-tools` plugin.

**Consequences.** Requires Claude Code ≥ v2.1.287. Managed-settings hooks still run first and
win. A user mod can't override a managed deny, which is fine.

---

## YAML DSL

**Status:** accepted · 2026-10-04

**Context.** Options were YAML, TypeScript rules (captain-hook style), or YAML plus a TS escape
hatch. Every enforceable rule in the current CLAUDE.md fits declaratively.

**Decision.** Rules are YAML only. Add a TS `check:` escape hatch only when a real rule needs it.

**Consequences.** Rules are reviewable data, easy to diff and to generate. Needs a YAML parser in
the mod (open item).

---

## Parsed shell matching with regex fallback

**Status:** accepted · 2026-10-04

**Context.** Regex on the raw command misfires on quoted text and can't express "aws must run
inside aws-vault". Captain-hook parses commands into an AST.

**Decision.** Parse Bash into sub-commands, unwrap known wrappers, match on structured fields.
Keep `regex` as a per-matcher fallback.

**Consequences.** A ~100–200 line tokenizer to own and test. Still evadable by a determined agent
(`eval`, base64, scripts on disk); arbiter targets habits, not adversaries.

---

## `match` + `unless` instead of forbid/require verbs

**Status:** accepted · 2026-10-04

**Context.** Half the existing rules are "X requires Y" (aws needs aws-vault; kubectl needs
`--context`).

**Decision.** One rule shape: `match` says when it applies, optional `unless` excuses it.

**Consequences.** One concept to learn. "Forbid" is a rule without `unless`.

---

## Three layers, override and disable by id

**Status:** accepted · 2026-10-04

**Context.** Want shipped defaults, personal global rules, and per-repo rules, without forking a
pack to turn off one rule.

**Decision.** Layers: plugin `rules/` → `~/.claude/rules/arbiter/` → `<repo>/.claude/rules/arbiter/`.
Higher layers `disable:` ids or redefine an id to replace it. Ids are global, not namespaced by
file; convention `<area>/<name>`.

**Consequences.** `.claude/rules/` is shared with Claude Code's markdown memory rules, but only
`.md` is auto-loaded, so YAML in the `arbiter/` subdir is invisible to context.

---

## Skip broken files, fail closed at runtime

**Status:** accepted · 2026-10-04

**Context.** Failing closed on a rules-file typo would block every Bash call. Failing open on a
guard crash would silently drop enforcement.

**Decision.** A file that fails to parse or validate is skipped with a toast and pane entry; other
files still apply. A guard that throws or times out denies via `.catch`. `ask` with no one to
answer denies.

**Consequences.** A broken file means its rules are off until fixed, but never silently.

---

## Defer rewrite, gates, and classifier

**Status:** accepted · 2026-10-04

**Context.** Rewrite has quoting/pipe edge cases; deny + hint covers most value. Gates are a
different event and DSL shape. A classifier adds latency and cost.

**Decision.**

- `rewrite`: schema accepts `action: rewrite` and `to:`; behaves as `deny` until implemented.
- Gates: open, not in v1.
- Classifier: later. Candidates are `$.model.classify` and Jev (TypeSafe AI, typed outputs with
  probabilities, 70–500 ms, proprietary early access). Opt-in per rule only, never on every call.
- Transcript mining (captain-hook's reviewer): dropped.

**Consequences.** Rules written today keep working when rewrite ships.

---

## `/arbiter check` instead of `why`

**Status:** accepted · 2026-10-04

**Decision.** The dry-run command is `/arbiter check <command>`. It prints the verdict Claude
would get (reason + hint) and the matching rules with layer and file, not raw YAML.
`/arbiter list <id>` prints a rule's YAML when the source is needed.

---

## yass specs are the normative behavior

**Status:** accepted · 2026-10-04

**Context.** Markdown requirements drift and can't be validated. [yass](https://github.com/shakefu/yass)
expresses behavior as MUST/MUST-NOT obligations per public symbol, validated by `yass validate`
and `yass lint`, which map directly onto tests.

**Decision.** One `.yass.yaml` per code file under `hooks/arbiter/`, rooted at
`hooks/arbiter/root.yass.yaml` so the rest of the repo is not governed by it. Markdown keeps the
overview and the why; specs win on conflict.

**Consequences.** yass is early-stage, so its format may change. Writing the specs surfaced two
design gaps that were fixed: heredoc bodies must be data, and `args` matches positionals in order
rather than as a prefix, because flag values (`--context x`) land among positionals.

---

## `match` and `unless` accept a list (any-of)

**Status:** accepted · 2026-10-04

**Context.** Real rules needed OR: `kubectl` is excused by `--context` _or_ `config` subcommands;
"no new contexts" covers both `kubectl config set-context` and `aws eks update-kubeconfig`.

**Decision.** `match` and `unless` take a matcher or a list of matchers, meaning any of them.
Fields within one matcher stay ANDed.

**Consequences.** No general boolean expression language. Revisit only if a real rule needs
nesting.

---

## Rules see one simple command at a time

**Status:** accepted · 2026-10-04

**Context.** `curl … | sh` was planned for the shipped pack, but the parser splits pipelines
into separate sub-commands and `regex` matches each sub-command's own `raw`.

**Decision.** v1 rules match single sub-commands. Pipeline-aware matching (e.g. a `piped_to`
field) waits for a real rule that needs it. `general/no-curl-pipe-sh` was dropped.

**Consequences.** Rules about what a command's output is fed into can't be written yet.

---

## Vendored js-yaml; pack tests run through the real mod

**Status:** accepted · 2026-10-04

**Context.** A hooks module may import only its own files and `claude-code`; test files can't
import `node:fs`.

**Decision.** Vendor js-yaml 4.1.0's single-file ESM build at `hooks/arbiter/vendor/`
(excluded from pre-commit). Run every rule file's inline tests with `script/arbiter-test`,
which calls `/arbiter test` via `claude -p`.

**Consequences.** Pack tests need an authenticated `claude` CLI, so they're not part of
`claude plugin test`.
