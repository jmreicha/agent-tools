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
files still apply. A guard that throws or times out before passing the call on denies via
`.catch`; one that fails after the tool ran replays the tool's real result (the handler's
replay-safe `next`), since a refusal would be a lie. `ask` with no one to answer denies.

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

---

## Personal rules live only in the user layer

**Status:** accepted · 2026-10-04

**Context.** The rules codified from `~/.claude/CLAUDE.md` (aws-vault, lytxread, kubectl
context) were briefly shipped in the plugin's `rules/`, which would turn them on for anyone who
installs the plugin.

**Decision.** The plugin ships only the small `general/*` pack. Personal rules go in
`~/.claude/rules/arbiter/`, in one `rules.yaml`; ids are the namespace, so no per-topic files.

**Consequences.** New users start with three rules and `/arbiter init` to show where theirs go.

---

## `description` replaces `reason`

**Status:** accepted · 2026-10-04

**Context.** "Reason" read awkwardly in `/arbiter list` and in the deny line Claude sees.

**Decision.** The field is `description`. A file still using `reason` is rejected with
`unknown key reason (renamed to description)` rather than accepted silently.

**Consequences.** Old rule files fail loudly once and are fixed by renaming the key.

---

## `/arbiter` is help; output is sorted and quoted

**Status:** accepted · 2026-10-04

**Context.** A bare `/arbiter` opened a pane, which was surprising, and long outputs were hard to
scan.

**Decision.** `/arbiter` and `/arbiter help` print counts and the command list; the pane moved to
`/arbiter pane`. Each reply starts with a summary line so Claude Code's `<plugin>: ` prefix
doesn't break table alignment. `list`, fired rules, test failures, and skipped files are sorted;
help, layers, and pane verdicts keep their meaningful order. `check` takes an optionally quoted
command and echoes it back.

**Consequences.** Output is plain text that Claude can still read; layout tricks stay minimal.

---

## Colored output through the `CommandOutput` render site

**Status:** accepted · 2026-10-04

**Context.** Command replies are plain transcript text with no color field.

**Decision.** A `ui.render` hook on `CommandOutput` rows for `arbiter` redraws the same text with
color: verdicts (deny red, ask/warn yellow, allow green), failures red, error handling (skipped
files, unknown subcommands, usage) yellow, labels and paths dim. Other commands' rows pass through.

**Consequences.** Color is display-only; the recorded text Claude reads is unchanged. Surfaces
that don't draw mods (e.g. `claude -p`) show plain text.

---

## JSON Schema for editors, kept in sync by script

**Status:** accepted · 2026-10-04

**Context.** Rule authors had no autocomplete or validation until `/arbiter reload`.

**Decision.** Ship `hooks/arbiter/rule.schema.json` and reference it from rule files with a
`yaml-language-server` modeline. `rules.ts` stays the validator; `script/arbiter-test` fails if
the schema's keys drift from it (test files can't import JSON).

**Consequences.** The modeline URL only resolves once `main` is pushed and public.

---

## Tested, commented examples

**Status:** accepted · 2026-10-04

**Context.** Doc snippets go stale silently, and most users start from a working file.

**Decision.** `hooks/arbiter/examples/rules.yaml` holds commented recipes with inline tests,
using `example/` ids. It never loads by default; `script/arbiter-test` loads it as a temp project
layer so a broken example fails the check. Overrides are documented but have no example.

**Consequences.** Examples and docs can disagree only in prose, not in behavior.

---

## Hit history as per-session JSONL files

**Status:** accepted · 2026-10-04

**Context.** Rules need tuning (dead rules, noisy rules, asks that are always allowed) and hits
need an audit trail. `$.fs.write` replaces a whole file (no append, no delete, 4 MiB read cap) and
`$.store` caps at 4 MiB in all.

**Decision.** Record every `deny`, `ask`, and `warn` verdict (never `allow`) as one JSON line in
`~/.claude/arbiter/history/<session-id>.jsonl`: time, session, project, tool, verdict action, the
fired rules' ids and actions, the ask's outcome, and a redacted target. One file per session means
one writer, so concurrent sessions never lose lines. Each session keeps its lines in memory (read
back once after a reload) and rewrites its file in order. `/arbiter history` aggregates files from
the last 90 days by mtime. Files older than 90 days are pruned at session start, and
`/arbiter history prune [days]` prunes on demand; `$.fs` has no delete, so pruning runs `rm -f`
via `$.process.run` on an explicit list of regular files, never the current session's. A failed write warns once and
never blocks the call. No tamper protection.

**Consequences.** The target is redacted best effort: a Bash call keeps each sub-command's name and
up to two leading lowercase word arguments (`aws s3 rm`), never other arguments; file tools keep
the path; other tools keep nothing beyond their name. Automatic pruning means hits older than 90
days are gone; keep copies elsewhere if an audit needs longer.

---

## `enabled` field and blocked-call indicators

**Status:** accepted · 2026-10-04

**Context.** Turning a rule off meant commenting it out or using `disable:` from a higher layer.
And a denied call left no visible trace for the user; only Claude saw the message.

**Decision.** Rules take `enabled` (default `true`); `false` moves the rule to the disabled list
after layers merge, so a higher layer can still redefine it and a `disable:` entry for it is no
warning. Its tests keep running. A deny or refused ask shows one toast with the redacted target;
the status line counts denied and asked calls per session. Warn and ask get nothing new.

**Consequences.** Toasts are per blocked call; if that proves noisy, drop them and keep the status
line.

---

## Pipelines and redirect targets in the parser

**Status:** accepted · 2026-10-04

**Context.** `curl … | sh` parsed as two unrelated commands, and `echo x > ~/.kube/config` dropped
its target, so path rules never saw writes made through Bash.

**Decision.** Each sub-command carries `pipe` (an id per pipeline) and `stage` (its position), and
`redirects` (file redirection targets). A `piped_to` matcher fires when a later stage of the same
pipeline matches it. `path` matchers on Bash also test redirect targets, with `$HOME` treated as
`~` and relative targets prefixed `./`.

**Consequences.** `bash <(curl …)`, `sh -c "$(curl …)"`, and other non-pipe ways of feeding a
shell don't match `piped_to`. Ordinary arguments (`cat ~/.aws/credentials`) still aren't paths to
`path` rules. Inline tests of a path rule exercise `file_path` only, not redirects.

---

## Shell edge cases: only what honest use produces

**Status:** accepted · 2026-10-05

**Context.** Shell offers endless spellings of one action; chasing all of them is whack-a-mole,
and arbiter is not a security boundary.

**Decision.** Handle a form only when Claude would write it in normal work. Added: Bash arguments
as `path` candidates (`cat .env`, `cp x ~/.kube/config`), `eval`, here-strings to a shell,
`find -exec`, and substitutions feeding their command's pipeline (`bash <(curl …)`). Skipped:
`ssh host '<cmd>'` (runs elsewhere), heredocs fed to a shell, variables as command names.

**Consequences.** A Bash path rule blocks reads and writes alike, and matches any argument word,
so a broad pattern can fire on unrelated text; keep path patterns specific. New cases are added
when seen, with a test.
