# arbiter reference

Every field of an arbiter rule file and how arbiter evaluates it. For what arbiter is and why
you'd use it, start with the [guide](../../hooks/arbiter/README.md). The normative behavior lives
in the yass specs under `hooks/arbiter/`; this page describes the same rules for people writing
them. For commented rules you can copy, see
[`examples/rules.yaml`](../../hooks/arbiter/examples/rules.yaml). Editors can validate rule files against
[`rule.schema.json`](../../hooks/arbiter/rule.schema.json).

## Rule file

A YAML mapping with two optional keys and no others.

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/jmreicha/agent-tools/main/hooks/arbiter/rule.schema.json
disable: [general/ask-reset-hard]
rules:
  - id: aws/requires-vault
    match: { cmd: aws }
    unless: { wrapped_by: aws-vault }
```

| Key       | Type          | Meaning                                |
| --------- | ------------- | -------------------------------------- |
| `disable` | list of ids   | Turn off rules defined in lower layers |
| `rules`   | list of rules | The rules this file defines            |

An empty file, or one with only comments, is fine.

## Rule

| Field         | Required                         | Type                          | Default | Meaning                                                                                                                 |
| ------------- | -------------------------------- | ----------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------- |
| `id`          | yes                              | string                        |         | Unique within a layer. Lowercase, `<area>/<name>` by convention.                                                        |
| `tool`        |                                  | pattern or list of patterns   | `Bash`  | Tool names the rule applies to. Exact names, or `/regex/`.                                                              |
| `match`       | yes, unless `tool` excludes Bash | matcher or list of matchers   |         | When the rule applies. Left out, the rule fires on every call to its tools. See [Tool-only rules](#tool-only-rules).    |
| `unless`      |                                  | matcher or list of matchers   |         | What excuses a match.                                                                                                   |
| `action`      |                                  | `deny` `ask` `warn` `rewrite` | `deny`  | What happens when the rule fires.                                                                                       |
| `to`          | with `rewrite`                   | mapping                       |         | The edits a rewrite makes. See [Rewrite](#rewrite).                                                                     |
| `repeat`      |                                  | mapping                       |         | Fire only after several matching calls. Not with `rewrite`. See [Repeat](#repeat).                                      |
| `description` |                                  | string                        |         | What the rule enforces and why. Claude reads it.                                                                        |
| `hint`        |                                  | string                        |         | What to do instead. Claude reads it.                                                                                    |
| `enabled`     |                                  | boolean                       | `true`  | `false` turns the rule off in place. `/arbiter list` marks it `[enabled: false]`; `/arbiter test` still runs its tests. |
| `tests`       |                                  | mapping                       |         | Expected outcome to list of inputs. See [Tests](#tests).                                                                |

`id` must match `^[a-z0-9][a-z0-9._-]*(/[a-z0-9._-]+)*$`. A rule using the old `reason` key is
rejected with `unknown key reason (renamed to description)`.

## Matcher

A mapping of one or more of these keys. Every key in a matcher must match. A list of matchers
under `match` or `unless` means any of them.

| Key          | Type                       | Matches                                                                             |
| ------------ | -------------------------- | ----------------------------------------------------------------------------------- |
| `cmd`        | pattern or list            | The program, with any directory stripped (`/usr/bin/aws` is `aws`).                 |
| `args`       | list of patterns or lists  | Positional arguments, in this order but not necessarily adjacent.                   |
| `flags`      | list of strings            | All of these flags present. `--context` also matches `--context=x`.                 |
| `wrapped_by` | string or list             | The command runs inside any of these [wrappers](#wrappers).                         |
| `env`        | mapping of name to pattern | Leading `NAME=value` assignments, e.g. `{ AWS_PROFILE: "prod*" }`.                  |
| `regex`      | `/regex/flags`             | Searched in the simple command's raw text.                                          |
| `path`       | pattern or list            | The tool call's `file_path`, and Bash redirect targets. A leading `~` is your home. |
| `piped_to`   | matcher of command keys    | A later stage of the same pipeline, e.g. `{ cmd: [sh, bash] }`.                     |

`cmd`, `args`, `flags`, `wrapped_by`, `env`, `regex`, and `piped_to` are command keys and only
match Bash calls. `path` matches a call's `file_path` (Edit, Write, Read) and, on Bash, every
file redirection target (`>`, `>>`, `<`, `&>`, ...) and positional argument, so with `Bash` in
`tool` it catches `echo x > ~/.kube/config`, `cp x ~/.kube/config`, and `cat .env`. `$HOME` and
`${HOME}` count as `~`, and a relative word is matched as `./word`, so `*/.env` catches `.env`.
Bash can't tell reading from writing, so such a rule blocks both. Other tools, such as `Grep`
or MCP tools, have nothing to match yet; a [tool-only rule](#tool-only-rules) covers every call to
them. The two kinds can't share a matcher.

### Tool-only rules

A rule with no `match` fires on every call to the tools in `tool`. Use it to steer whole tools:

```yaml
- id: search/use-codegraph
  tool: [Grep, Glob]
  action: warn
  hint: Run `codegraph search "<query>"` instead.
  tests:
    warn: [Grep, Glob]
    allow: [Read]
- id: mcp/no-prod-db
  tool: /^mcp__prod_db__/
```

`tool` must not name `Bash` or be a `/regex/` that matches `Bash`, since that would block every
shell command. `unless` needs a `match`. Test inputs are tool names. To steer the shell side of the
same habit, add a normal rule such as `{ cmd: [grep, rg] }`.

**args.** Flags are removed before matching, but flag _values_ stay, so
`kubectl --context prod delete pod web` has positionals `[prod, delete, pod, web]`. That is why
`args` matches in order rather than as a prefix. A nested list is any-of at that position:
`[config, [set-context, set-cluster]]`.

**piped_to.** Fires when the matched command's output feeds a later stage of the same pipeline,
through `|` or `|&`, directly or not: `curl x | tee f | sh` matches
`{ cmd: curl, piped_to: { cmd: sh } }`. Wrapped stages count (`| sudo bash`). A `$(…)`, backtick,
or `<(…)` substitution feeds the command it sits in, so `bash <(curl …)` and
`sh -c "$(curl …)"` match too. A `bash -c` script is its own pipeline.

**flags.** Compared exactly as written, so `-f` doesn't match `-rf`. List both spellings when a
tool accepts them, as separate matchers if needed.

## Patterns

A pattern is a string. Written `/body/` or `/body/flags` (flags from `i`, `m`, `s`, `u`), it's a
JavaScript regular expression matched by search. Anything else is a glob matched against the whole
value: `*` matches any run of characters, `?` one character.

```yaml
cmd: [terraform, tofu] # exact names
args: ["delete-*"] # glob
env: { AWS_PROFILE: "prod*" } # glob
tool: /^mcp__prod__/ # regex
regex: "/drop\\s+table/i" # regex, case-insensitive
```

## Evaluation

For each tool call:

1. Rules whose `tool` matches the call's tool name are considered.
2. A Bash command is [parsed](#shell-parsing) into simple commands. A rule fires when, for some
   simple command, `match` matches and `unless` does not match that same simple command. Path
   rules do the same with `file_path`.
3. The strictest action among fired rules wins: `deny`, then `rewrite`, then `ask`, then `warn`.
   A rewrite comes before `ask` so that what you are asked about is the rewritten command.

| Action    | Effect                                                                                                   |
| --------- | -------------------------------------------------------------------------------------------------------- |
| `deny`    | The call doesn't run. Claude reads one line per fired deny rule.                                         |
| `ask`     | The call waits for you to pick Allow or Refuse. Dismissing it, or `claude -p`, denies.                   |
| `rewrite` | The command is edited per `to`, checked again, and run if that check allows it. See [Rewrite](#rewrite). |
| `warn`    | The call runs, a line is logged to the transcript, and Claude gets the same line with the call's result. |

Each line Claude reads has the form `arbiter <id>: <description> <hint>`, sorted by id, with a
missing description or hint left out. A [repeat](#repeat) rule's line ends with
` (<n> matching calls in the last <within>)`.

If arbiter itself throws or times out while deciding, the call is denied with
`arbiter failed (<kind>): <message>`. If it fails after the call was already passed on, the
tool has run, so the call keeps its real result instead.

## Shell parsing

- Commands split on unquoted `&&`, `||`, `;`, `|`, `|&`, `&`, newlines, and subshell parentheses.
- Quoted text is data: `echo "aws s3 ls"` contains one command, `echo`.
- `$(...)`, backticks, `<(...)`, `>(...)`, the script of `bash -c` / `sh -c` / `zsh -c`, the
  arguments of `eval`, and a `<<<` here-string given to a shell are parsed as commands.
  Substitutions come before the command that contains them.
- `find … -exec cmd … ;` (also `-execdir`, `-ok`, `-okdir`, ending in `;` or `+`) yields `cmd` as
  a command wrapped by `find`.
- Redirect targets are recorded for `path` rules; fd duplications like `2>&1` are not.
- Heredoc bodies are data, so commit messages written with `<<'EOF'` never trigger rules.
- Comments, redirections, and leading reserved words (`if`, `then`, `do`, `!`,
  ...) are ignored. A bare `--` ends flags.
- If a command can't be parsed (an unclosed quote or substitution, a heredoc with no end), the
  whole command becomes one simple command with only raw text, so only `regex` rules can match.

### Wrappers

A wrapper and the command it runs become two simple commands. The wrapped one records the wrapper
name, outermost first, and inherits wrappers through `bash -c` and substitutions.

| Wrapper     | Consumes before the wrapped command                                                    |
| ----------- | -------------------------------------------------------------------------------------- |
| `sudo`      | flags, with values for `-u -g -U -C -h -p -r -t -D`                                    |
| `env`       | flags, with values for `-u -C -S`; `NAME=value` words go to the wrapped env            |
| `time`      | flags, with values for `-f -o`                                                         |
| `nice`      | flags, with a value for `-n`                                                           |
| `timeout`   | flags, with values for `-s -k --signal --kill-after`; then the duration                |
| `xargs`     | flags, with values for `-I -n -P -L -d -E -s -a`                                       |
| `aws-vault` | `exec` only: everything through `--`, or `exec`, its flags, and the profile            |
| `op`        | `run` only, with a `--`: everything through `--`                                       |
| `uv`        | `run` only: `run` and its flags, with values for `--with -w --python -p --project ...` |
| `nohup`     | flags                                                                                  |
| `doas`      | flags, with values for `-u -C`                                                         |
| `exec`      | flags, with a value for `-a`                                                           |
| `watch`     | flags, with values for `-n --interval`; one quoted argument is parsed as a command     |
| `command`   | flags; not a wrapper with `-v`/`-V`, which only look the name up                       |
| `builtin`   | flags                                                                                  |

So `aws-vault exec lytxread -- aws s3 ls` gives `aws-vault` with args `[exec, lytxread]` and
`aws` with args `[s3, ls]` and `wrapped_by: aws-vault`.

## Layers

| Order | Layer   | Folder                          |
| ----- | ------- | ------------------------------- |
| 1     | plugin  | `<plugin>/rules/`               |
| 2     | user    | `~/.claude/rules/arbiter/`      |
| 3     | project | `<repo>/.claude/rules/arbiter/` |

- Every `*.yaml` and `*.yml` file directly in a layer's folder loads, in alphabetical order.
- Subfolders are not loaded; each one shows a warning in the pane.
- A rule in a higher layer replaces a lower rule with the same id.
- `disable` removes rules from lower layers only. An id no lower layer defines is a warning.
- Two files in the same layer defining the same id is an error: the second file is skipped.
- A file with any error is skipped as a whole and reported. Other files still load.
- The project layer is skipped when it's the same folder as the user layer (a session started in
  your home directory).

## Rewrite

A `rewrite` rule fixes the command and runs the fixed version instead of denying it. Use it for
mechanical fixes with one right answer; keep `deny` with a `hint` when the fix needs a choice.

```yaml
- id: aws/requires-vault
  match: { cmd: aws }
  unless: { wrapped_by: aws-vault }
  action: rewrite
  to:
    prefix: "aws-vault exec {--profile|AWS_PROFILE|lytxread} --"
    flags: { --profile: null }
    env: { AWS_PROFILE: null }
  tests:
    rewrite:
      "aws s3 ls": "aws-vault exec lytxread -- aws s3 ls"
      "aws s3 ls --profile prod": "aws-vault exec prod -- aws s3 ls"
```

| `to` key | Edit                                                                               |
| -------- | ---------------------------------------------------------------------------------- |
| `prefix` | Inserted before the command word (after leading `NAME=value` words), then a space. |
| `cmd`    | Replaces the command word: `{ cmd: prek }`.                                        |
| `flags`  | Flag to a new flag (`{ -f: --force-with-lease }`), or `null` to drop it.           |
| `env`    | `NAME: null` drops that leading assignment.                                        |

`prefix` and `cmd` may hold templates `{a|b|...}`. Each alternative is a flag (its value), an
upper-case env name (its assigned value), or a literal; the first one present wins. Values read
from the command are single-quoted when they hold anything beyond letters, digits, and
`@%+=:,./_-`. A dropped flag whose value a template read loses that value too.

Edits are spliced into the original text at the matched simple command, so the rest of the
command line (`cd x && … | head`) is untouched. Then:

- The rewritten command is evaluated again against every rule, and handled as that verdict: an
  `ask` rule still asks, and so on. If it would be rewritten again, the call is denied.
- A command arbiter can't splice safely (inside `bash -c '…'` or `eval`), overlapping edits from
  two rules, or a template nothing fills, denies the call with the reason.
- Claude reads `arbiter <ids> rewrote this command; it ran as: <rewritten>` after the result.
  You get a toast and a `rewritten` count in the status line, and history records the rewrite.

## Repeat

```yaml
- id: test/no-blind-rerun
  match: { cmd: pytest }
  repeat: { count: 3, within: 10, reset_on: [Edit, Write], same: true }
  action: warn
```

| Key        | Required | Type                        | Default | Meaning                                                           |
| ---------- | -------- | --------------------------- | ------- | ----------------------------------------------------------------- |
| `count`    | yes      | integer, 2 or more          |         | Matching calls, this one included, needed before the rule fires.  |
| `within`   |          | integer, `count` to 200     | `20`    | Recent tool calls, this one included, to count in.                |
| `reset_on` |          | pattern or list of patterns |         | Tools whose call starts the count over. Exact names or `/regex/`. |
| `same`     |          | boolean                     | `false` | Count only earlier calls with the same command text or file path. |

`within` is required when `count` is over 20. `repeat` can't be combined with `action: rewrite`.

A repeat rule fires when its `match` and `unless` hold for the call, as usual, and the call plus
the earlier calls that matched reach `count`. Earlier calls are counted back from the most recent
through `within - 1` of them, stopping at a `reset_on` call. Once it fires it fires on each further
matching call until a reset or the window slides past.

The window holds the last 200 tool calls that ran in this session, matched or not. A denied or
refused call didn't run and isn't recorded; a rewritten one is recorded as what ran. Subagent
calls share the window. It is cleared when a session starts. `/arbiter check` evaluates against
the current window without adding to it.

## Tests

```yaml
tests:
  deny: ["kubectl get pods"]
  ask: []
  warn: []
  allow: ["kubectl --context prod get pods"]
```

Each input is evaluated against that rule alone. Inputs are Bash commands, or paths for rules
whose matchers use `path` (a leading `~` is expanded). An input passes when the outcome equals its
key; `allow` means the rule didn't fire. `rewrite` maps each input to the exact command it must
become: `rewrite: { "pre-commit run": "prek run" }`.

A [repeat](#repeat) rule lists sequences instead: each entry is a list of calls run through a
fresh window, and the outcome is the last call's. A step is an input as above, or
`{ tool: <name> }` for a bare call to that tool, to place a reset or fill the window.

```yaml
tests:
  warn: [[pytest -x, pytest -x, pytest -x]]
  allow: [[pytest -x, { tool: Edit }, pytest -x, pytest -x]]
```

## Commands

| Command                         | Output                                                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `/arbiter`, `/arbiter help`     | Rule and error counts, then the command list.                                                                                               |
| `/arbiter init`                 | Each layer's folder and rule count, an example rule file, and next steps.                                                                   |
| `/arbiter list [filter]`        | Rules whose id contains `filter`, sorted by id, as an ID/ACTION/LAYER/DESCRIPTION table.                                                    |
| `/arbiter list <id>`            | That rule's YAML.                                                                                                                           |
| `/arbiter check "<command>"`    | The verdict (with `-> "<rewritten>"` for a rewrite), then each fired rule with its file, description, and hint.                             |
| `/arbiter test`                 | Passed/total, then skipped files by path and failures by id.                                                                                |
| `/arbiter reload`               | Re-reads rule files and prints counts per layer.                                                                                            |
| `/arbiter pane`                 | Opens a pane with counts, load errors, and the last 100 verdicts.                                                                           |
| `/arbiter history`              | Hits and sessions in the last 90 days, a per-rule ID/HITS/DENY/ASK/WARN/ALLOWED/REFUSED/LAST table sorted by hits, then rules with no hits. |
| `/arbiter history prune [days]` | Removes history files older than `days` (default 90) and prints the count.                                                                  |

Quotes around the `check` command are optional; one surrounding pair is removed.

## History

Every `deny`, `ask`, and `warn` verdict (never `allow`) appends one JSON line to
`~/.claude/arbiter/history/<session-id>.jsonl`:

```json
{
  "ts": "2026-10-04T14:02:11.000Z",
  "session": "…",
  "project": "/repo",
  "tool": "Bash",
  "action": "ask",
  "rules": [{ "id": "k8s/ask-delete", "action": "ask" }],
  "outcome": "allowed",
  "target": "kubectl delete pod"
}
```

| Field     | Value                                                                                  |
| --------- | -------------------------------------------------------------------------------------- |
| `action`  | The verdict's action.                                                                  |
| `rules`   | Every fired rule with its own action, so a shadowed `warn` still counts.               |
| `outcome` | `allowed` or `refused`, for `ask` only. A dismissed ask, or `claude -p`, is `refused`. |
| `target`  | See below.                                                                             |

`target` is redacted best effort. For `Bash` it is each sub-command's name plus at most two
leading words matching `^[a-z][a-z0-9-]*$` (`aws sso login AKIA… --profile p` → `aws sso login`),
joined with `;`. For `Read`, `Edit`, and `Write` it is the file path. Other tools have none.

One file per session means one writer, so concurrent sessions never lose lines. A failed write
shows one toast and never blocks the call. Files older than 90 days are pruned at session start
(the current session's file and symbolic links never are); `/arbiter history prune [days]` prunes
on demand. Query the raw log with `jq`, e.g.
`jq -s 'map(select(.action=="deny"))' ~/.claude/arbiter/history/*.jsonl`.

## Indicators

A denied call, or an ask you refuse, shows a toast such as
`arbiter denied aws sso login (aws/no-sso-login)`, using the [history](#history) target. The status
line keeps a per-session count, e.g. `arbiter: 2 denied · 1 asked`, and stays empty until
something fires. Warnings already log a line (and reach Claude), and asks already prompt.
