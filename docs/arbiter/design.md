# arbiter: Design

See [requirements.md](requirements.md) for scope and [decisions.md](decisions.md) for the
reasoning behind each choice.

The normative behavior lives in the yass specs under `hooks/arbiter/*.yass.yaml` (start at
`root.yass.yaml`; browse with `yass list` / `yass query`). Where this overview and a spec
disagree, the spec wins. Worked rules from `~/.claude/CLAUDE.md` are in
[examples/claude-md.yaml](examples/claude-md.yaml).

## Architecture

```
agent-tools/
├── hooks/
│   ├── hooks.json              modules: ["./arbiter/index.ts"]
│   └── arbiter/
│       ├── index.ts            register(): load rules, tool.call guard, /arbiter command, pane
│       ├── shell.ts            "a && b | c" → [{ cmd, args, flags, env, wrappers, raw }]
│       ├── rules.ts            read + validate YAML, merge layers, apply disable/override
│       ├── engine.ts           evaluate(tool, input, rules) → verdict
│       ├── yaml.ts             parser (vendored lib or subset; see open items)
│       └── *.test.ts           unit tests + inline rule tests
└── rules/
    └── general.yaml            shipped pack
```

`shell.ts`, `rules.ts`, and `engine.ts` are pure: no `$`, no I/O. Only `index.ts` touches the
mods API (`$.fs.read`, `$.ui.*`, `$.command.register`).

## Data flow

1. `session.start` (and `/arbiter reload`): read every `*.yaml` from the three layers with
   `$.fs.read`, validate, merge into the effective rule set. Record load errors.
2. `tool.call`: `engine.evaluate(e.tool, e, rules)`.
   - Bash: parse `e.command` into sub-commands; test each rule against each sub-command.
   - Edit/Write/Read: test `path` against `e.file_path`.
   - Other tools (incl. MCP): only rule-level `tool` matching applies.
3. Strictest outcome wins: `deny` > `ask` > `warn` > none.
   - `deny` → `{ deny: <reasons + hints of every matching deny rule> }`
   - `ask` → `$.ui.ask(…)`; anything but explicit approval, including no one to ask, denies.
   - `warn` → `$.ui.log(…)`, then `next(e)`.
   - none → `next(e)`.
4. Each verdict goes into an in-memory ring buffer (last ~100) that the pane renders.

## Rule schema

```yaml
# ~/.claude/rules/arbiter/cloud.yaml
disable: [general/no-curl-pipe-sh] # ids from lower layers

rules:
  - id: aws/no-sso-login
    match: { cmd: aws, args: [sso, login] }
    reason: "aws sso login leaves plaintext credentials on disk."
    hint: "Use `aws-vault exec <profile> -- aws ...`."
    tests:
      deny: ["aws sso login --profile prod"]
      allow: ["aws s3 ls"]

  - id: aws/requires-vault
    match: { cmd: aws }
    unless: { wrapped_by: aws-vault }
    hint: "Wrap AWS calls: `aws-vault exec lytxread -- aws ...`."
    tests:
      deny: ["aws s3 ls --profile prod", "cd x && aws s3 ls | head"]
      allow: ["aws-vault exec lytxread -- aws s3 ls"]

  - id: aws/prefer-lytxread
    match: { cmd: aws-vault, args: [exec] }
    unless: { args: [exec, "lytxread*"] }
    action: ask
    reason: "Elevated AWS role requested."

  - id: k8s/require-context
    match: { cmd: kubectl }
    unless: { flags: [--context] }
    hint: "Pass `--context <existing-context>`."

  - id: k8s/no-new-contexts
    match:
      {
        cmd: kubectl,
        args: [config, [set-context, set-cluster, set-credentials]],
      }

  - id: k8s/kubeconfig-readonly
    tool: [Edit, Write]
    match: { path: "~/.kube/config" }

  - id: k8s/ask-destructive
    match: { cmd: kubectl, args: [[delete, drain, scale]] }
    action: ask
```

### Rule fields

| Field    | Required | Meaning                                                                                                                                                                       |
| -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`     | yes      | Unique within a layer. Same id in a higher layer replaces the rule. Convention: `<area>/<name>`.                                                                              |
| `tool`   | no       | String, list, or `/regex/`. Default `Bash`.                                                                                                                                   |
| `match`  | yes      | Matcher, or list of matchers (any-of): when the rule applies.                                                                                                                 |
| `unless` | no       | Matcher or list (any-of): if it also matches, the rule does not fire.                                                                                                         |
| `action` | no       | `deny` (default), `ask`, `warn`, `rewrite` (stub → deny, logs "not implemented").                                                                                             |
| `to`     | no       | Rewrite target; accepted, unused in v1.                                                                                                                                       |
| `reason` | no       | Why the rule exists; shown to Claude and in `/arbiter check`.                                                                                                                 |
| `hint`   | no       | What to do instead; shown to Claude.                                                                                                                                          |
| `tests`  | no       | Map of expected outcome (`deny`/`ask`/`warn`/`allow`) → list of inputs, evaluated against this rule alone. Input is a command string for Bash rules, a path for `path` rules. |

### Matcher fields

Fields in one matcher are ANDed; a list value means "any of".

| Field        | Matches against                                                                                                                                |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `cmd`        | argv[0] after unwrapping. String, list, or `/regex/`.                                                                                          |
| `args`       | Positionals in order, not necessarily adjacent (flag values count as positionals). Elements are literals or globs; a nested list means any-of. |
| `flags`      | All listed flags present. `--context` also matches `--context=x`.                                                                              |
| `wrapped_by` | A wrapper around this sub-command (`aws-vault`, `sudo`, `env`, `op`, …).                                                                       |
| `env`        | Inline assignments, e.g. `{ AWS_PROFILE: "*" }`.                                                                                               |
| `regex`      | Raw sub-command text. Fallback for anything structure can't express.                                                                           |
| `path`       | Glob against `file_path`; `~` expanded.                                                                                                        |

### Shell parsing

- Split on `&&`, `||`, `;`, `|`, newlines; recurse into `$(…)`, backticks, and `bash -c "…"`.
- Heredoc bodies and quoted text are data, never commands (so a commit message mentioning
  `aws sso login` is not denied).
- Tokenize respecting single/double quotes and escapes. Leading `VAR=val` → `env`.
- Unwrap built-in wrappers, recording each in `wrappers`: `sudo`, `env`, `time`, `nice`,
  `timeout <n>`, `xargs`, `aws-vault exec <profile> --`, `op run --`.
- On parse failure (e.g. unbalanced quote): treat the whole command as one sub-command with only
  `raw` set, so `regex` rules still apply; log the failure.

### Layers

Load order, lowest to highest: plugin `rules/*.yaml` → `~/.claude/rules/arbiter/*.yaml` →
`<repo>/.claude/rules/arbiter/*.yaml`. Within a layer, files load alphabetically. `disable:`
removes ids from all lower layers. Claude Code only auto-loads `.md` under `.claude/rules/`, so the
YAML files do not leak into context.

## Error handling

| Failure                                   | Behavior                                                       |
| ----------------------------------------- | -------------------------------------------------------------- |
| YAML syntax or schema error               | Skip that file; toast + pane entry with file, line, message.   |
| Duplicate id within a layer               | Load error; the second file is skipped.                        |
| `disable:` names an unknown id            | Warning only.                                                  |
| Shell parse failure                       | `raw`-only sub-command; `regex` rules still apply.             |
| Guard throws or times out                 | `.catch` handler returns `{ deny: "arbiter failed: <kind>" }`. |
| `ask` with no one to answer (`claude -p`) | Deny.                                                          |

## Commands and UI

| Command                      | Does                                                                                         |
| ---------------------------- | -------------------------------------------------------------------------------------------- |
| `/arbiter`                   | Open the pane: recent verdicts, rule counts per layer, load errors.                          |
| `/arbiter check <command>`   | Dry run. Prints the verdict Claude would get and each matching rule with its layer and file. |
| `/arbiter list [filter\|id]` | Effective rules with layer and disabled state; given an id, prints its YAML.                 |
| `/arbiter test`              | Run every rule's inline tests; print failures.                                               |
| `/arbiter reload`            | Re-read all layers.                                                                          |

Example:

```
/arbiter check aws s3 ls --profile prod
DENY  aws/requires-vault   (user: ~/.claude/rules/arbiter/cloud.yaml)
  hint: Wrap AWS calls: `aws-vault exec lytxread -- aws ...`.
```

## Testing

- Unit tests (`*.test.ts`, `claude plugin test`) for `shell.ts`, `rules.ts`, `engine.ts`.
- One test loads every layer and runs each rule's inline `tests:`, so CI fails on regression.
- `/arbiter test` runs the same check in-session.

## Shipped `general` pack (initial)

`general/no-force-push` (`git push --force`/`-f`, hint `--force-with-lease`),
`general/no-rm-rf-root` (`rm -rf /`, `~`, `$HOME`), `general/no-curl-pipe-sh`
(`curl|wget … | sh|bash`). Kept small on purpose.

## Open items

1. **YAML parser**: spike whether a mod can bundle a vendored parser (e.g. `yaml`) or needs a
   small subset parser.
2. **Local imports**: confirm a hooks module can import sibling `.ts` files; if not, build to a
   single file.
3. **Gates** (`classic.Stop`): undecided.
4. **Classifier**: compare `$.model.classify` and Jev (via `$.http.fetch`). Likely shape: an
   opt-in `judge:` matcher field with a yes/no question and a probability threshold, evaluated
   only after structural matching narrows the call. Jev sends command text to a third party, so
   it needs secret redaction first and must fail closed on timeout.
