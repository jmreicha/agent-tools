# arbiter: Requirements

## Problem

Behavioral rules live in `~/.claude/CLAUDE.md` ("always use aws-vault", "never `aws sso login`",
"always pass `kubectl --context`"). They are guidance: nothing guarantees Claude follows them.
Native permission `deny` rules help but only glob-match, carry no "why / do this instead" message,
have no tests, and get unmanageable past a handful.

## Goal

A Claude Code mod, shipped in the `agent-tools` plugin, that enforces rules written in a small YAML
DSL at every tool call. Rules must stay easy to read, review, test, and switch off as they grow
into the hundreds.

## Non-goals

- Replacing CLAUDE.md for style guidance (brevity, comment length, "use context7"). Those cannot be
  gated at a tool call and stay as guidance.
- Being a security boundary. Matching shell text can be evaded by a determined agent; arbiter
  catches honest mistakes and habits, not adversaries.
- Mining transcripts to propose rules (captain-hook's session reviewer).

## Requirements (v1)

Summary only; the yass specs in `hooks/arbiter/` are normative.

| #   | Requirement                                                                                                                                                                                                                                                                        |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1  | Rules are YAML files loaded from three layers: plugin-shipped, user (`~/.claude/rules/arbiter/*.yaml`), project (`<repo>/.claude/rules/arbiter/*.yaml`).                                                                                                                           |
| R2  | A higher layer can disable a lower-layer rule by `id`, or replace it by redefining the same `id`.                                                                                                                                                                                  |
| R3  | Bash commands are parsed into sub-commands (split on `&&`, `\|\|`, `;`, `\|`, `$(…)`) and known wrappers are unwrapped before matching.                                                                                                                                            |
| R4  | Rules express "forbid X" (`match`) and "X requires Y" (`match` + `unless`).                                                                                                                                                                                                        |
| R5  | Matchers cover `cmd`, `args`, `flags`, `wrapped_by`, `env`, `regex` (raw-text fallback), `path` (Edit/Write/Read), and rule-level `tool` (incl. MCP tool names).                                                                                                                   |
| R6  | Actions: `deny` (default), `ask`, `warn`. `rewrite` is accepted by the schema and behaves as `deny` until implemented.                                                                                                                                                             |
| R7  | Deny messages give Claude the `description` and `hint` so it can self-correct; all matching deny hints are returned together.                                                                                                                                                      |
| R8  | Each rule can carry inline `tests:`; they run via `/arbiter test` and `claude plugin test` (CI).                                                                                                                                                                                   |
| R9  | A broken rules file is skipped loudly (toast + pane), never silently; a runtime guard failure denies (fails closed).                                                                                                                                                               |
| R10 | Commands: `/arbiter` (help), `/arbiter init`, `/arbiter pane`, `/arbiter check "<command>"`, `/arbiter list [filter\|id]`, `/arbiter test`, `/arbiter reload`, `/arbiter history [prune [days]]`.                                                                                  |
| R11 | A pane shows recent verdicts, rule counts per layer, and load errors.                                                                                                                                                                                                              |
| R12 | Ship a small `general` pack (≈3–5 rules) that users can disable by id.                                                                                                                                                                                                             |
| R13 | Every `deny`/`ask`/`warn` hit is logged per session with rule ids, action, tool, ask outcome, and a redacted target; `/arbiter history` reports per-rule counts for tuning and audit; files older than 90 days are pruned at session start and by `/arbiter history prune [days]`. |
| R14 | A rule can be switched off in place with `enabled: false` (default `true`); its tests still run.                                                                                                                                                                                   |
| R15 | A blocked call shows a toast, and the status line counts denied and asked calls per session.                                                                                                                                                                                       |
| R16 | Rules can match a command piped into another (`piped_to`), and `path` rules see Bash redirect targets.                                                                                                                                                                             |

## Success criteria

- Every enforceable line in the current `~/.claude/CLAUDE.md` (aws-vault, no `aws sso login`,
  lytxread role, `kubectl --context`, no new kube contexts, ask before destructive cloud changes)
  is expressed as an arbiter rule with passing inline tests.
- A repo can opt out of any rule with a one-line `disable:` entry.
- A typo in one rules file never disables the others, and is visible within the session.

## Later / open

- **Matching MCP tool calls.** `tool` can name an MCP tool, but no matcher applies to its
  arguments, so such a rule can never fire. Needs an `input` matcher (or similar) over call args.

- `rewrite` action (stubbed in v1).
- Session gates, e.g. "ran tests before finishing" (`classic.Stop`): undecided.
- Classifier for fuzzy rules: compare `$.model.classify` (built in, uses the Claude plan) with
  [Jev](<https://en.wikipedia.org/wiki/Jev_(AI_model)>) (TypeSafe AI; typed choice/score/yes-no
  outputs with probabilities, 70–500 ms, proprietary, limited early access).
- File-watch auto-reload of rules.
- Configurable wrapper list.
- Bash arguments as paths for `path` rules (`cat ~/.aws/credentials`); `eval`, `find -exec`, and
  here-strings fed to a shell; `bash <(curl …)` as a pipe.
