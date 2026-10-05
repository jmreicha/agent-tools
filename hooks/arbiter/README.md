# arbiter

arbiter turns the "always do X, never do Y" lines in your `CLAUDE.md` into rules Claude Code
actually enforces. It checks every tool call Claude is about to make against a set of YAML rules
and denies it, asks you first, or lets it through with a warning.

```
You:     list the s3 buckets in prod
Claude:  aws s3 ls --profile prod
arbiter: arbiter aws/requires-vault: AWS access goes through aws-vault.
         Run `aws-vault exec lytxread -- aws ...`, not `aws --profile`.
Claude:  aws-vault exec lytxread -- aws s3 ls
```

## Why use it

Instructions in `CLAUDE.md` are suggestions. Claude follows them most of the time, and the times it
doesn't tend to be the ones that matter: a profile with plaintext credentials, a command against
the wrong Kubernetes cluster, a force push.

Claude Code's built-in [permission rules](https://code.claude.com/docs/en/permissions) can block
commands, but they only glob-match the raw text, can't say why or what to do instead, and can't be
tested. arbiter fills those gaps:

- **Claude learns the fix.** A denied call returns your `description` and `hint`, so Claude retries
  the right way instead of stopping.
- **Rules understand shell.** Commands are parsed, not regex-matched, so `echo "aws s3 ls"` or a
  commit message that mentions `aws sso login` won't trip a rule, while `cd infra && aws s3 ls`
  or `bash -c 'aws s3 ls'` will.
- **"X requires Y" is one rule.** `match` says when a rule applies; `unless` says what excuses it.
  "kubectl must pass `--context`" doesn't need a regex.
- **Rules carry their own tests.** Every rule can list inputs it must deny or allow, and
  `/arbiter test` checks them all.
- **Hundreds of rules stay manageable.** Rules have ids, live in plugin, user, and project layers,
  and can be turned off by id from any higher layer.

### Built on Claude Code mods

arbiter is a [Claude Code mod](https://code.claude.com/docs/en/plugins/mods/overview): functions
that run inside Claude Code and sit directly in the path of every tool call. That's what makes the
rest possible. The usual alternatives work from outside:

|                                   | `CLAUDE.md` | Permission rules       | Settings hooks (`PreToolUse`) | arbiter (mod)                         |
| --------------------------------- | ----------- | ---------------------- | ----------------------------- | ------------------------------------- |
| Enforced                          | No          | Yes                    | Yes                           | Yes                                   |
| Matches                           | n/a         | Globs on raw text      | Whatever your script does     | Parsed shell, paths, tools            |
| Tells Claude why and what instead | n/a         | No                     | Via stderr/JSON               | Yes, per rule                         |
| Asks you mid-call                 | n/a         | Allow/deny prompt only | Can return "ask"              | Yes, with the rule's reason           |
| Commands and UI                   | n/a         | No                     | No                            | `/arbiter`, colored output, live pane |
| Runs                              | n/a         | In Claude Code         | A process per call            | In process, no spawn                  |
| Fails safe if it breaks           | n/a         | n/a                    | Your script's job             | Yes: a crash denies the call          |

Because it runs in process, arbiter adds no process spawn per tool call, covers subagents and
`claude -p` runs too, can pause a call to ask you, answers `/arbiter` commands without starting a
Claude turn, and reloads its rules without a restart. Settings hooks can block calls as well, but
each check is a separate program you write, parse JSON for, and debug on your own.

arbiter is a guardrail for habits and honest mistakes, not a security boundary. An agent set on
getting around it can (`eval`, scripts on disk, base64).

## Quick start

1. Load the plugin. Either install `agent-tools`, or point Claude Code at a checkout in
   `~/.claude/settings.json`:

   ```json
   { "env": { "CLAUDE_CODE_PLUGIN_DIRS": "/path/to/agent-tools" } }
   ```

2. Start a session and run `/arbiter init` to see where rule files go.

3. Create `~/.claude/rules/arbiter/rules.yaml`, or copy rules from the commented
   [examples](examples/rules.yaml):

   ```yaml
   # yaml-language-server: $schema=https://raw.githubusercontent.com/jmreicha/agent-tools/main/hooks/arbiter/rule.schema.json
   rules:
     - id: k8s/require-context
       match: { cmd: kubectl }
       unless: { flags: [--context] }
       description: kubectl must target an explicit context.
       hint: Pass `--context <existing-context>`.
       tests:
         deny: ["kubectl get pods"]
         allow: ["kubectl --context prod get pods"]
   ```

   The first line gives editors with the YAML language server autocomplete and validation.

4. Run `/arbiter reload`, then `/arbiter check "kubectl get pods"` to see the verdict, and
   `/arbiter test` to run the rule's tests.

## Where rules live

| Layer   | Folder                          | Use it for                            |
| ------- | ------------------------------- | ------------------------------------- |
| plugin  | `<plugin>/rules/`               | Defaults that ship with arbiter       |
| user    | `~/.claude/rules/arbiter/`      | Your personal rules, in every repo    |
| project | `<repo>/.claude/rules/arbiter/` | Rules for one repo, committed with it |

Every `*.yaml` file in those folders loads at session start and on `/arbiter reload`. A higher
layer wins: redefining an id replaces the lower rule, and `disable: [id, ...]` turns lower rules
off.

```yaml
# <repo>/.claude/rules/arbiter/repo.yaml
disable: [general/ask-reset-hard] # this repo resets often
```

A file with a mistake is skipped as a whole, never silently: you get a toast, and `/arbiter`,
`/arbiter test`, and the pane list the error. Every other file keeps working.

## Recipes

Each of these, with comments and tests, is in [examples/rules.yaml](examples/rules.yaml). Copy
the whole file or just the rules you want, and rename the `example/` ids.

**Forbid a command.** A rule with no `unless` fires whenever `match` does.

```yaml
- id: aws/no-sso-login
  match: { cmd: aws, args: [sso, login] }
  description: aws sso login leaves plaintext credentials on disk.
  hint: Use `aws-vault exec <profile> -- aws ...`.
```

**Require a wrapper.** `wrapped_by` sees through `aws-vault exec`, `op run`, `sudo`, `env`, and
friends.

```yaml
- id: aws/requires-vault
  match: { cmd: aws }
  unless: { wrapped_by: aws-vault }
  hint: Run `aws-vault exec <profile> -- aws ...`.
```

**Ask before something risky.** `action: ask` pauses the call until you pick Allow or Refuse. In
`claude -p`, where nobody can answer, it denies.

```yaml
- id: k8s/ask-destructive
  match: { cmd: kubectl, args: [[delete, drain, scale, apply]] }
  action: ask
  description: This kubectl command changes cluster state.
```

**Several exceptions.** A list under `match` or `unless` means any of them.

```yaml
- id: gcloud/require-project
  match: { cmd: gcloud }
  unless:
    - { flags: [--project] }
    - { args: [[auth, config, version, projects]] }
  hint: Pass `--project <project-id>`.
```

**Protect a file.** Path rules apply to file tools such as Edit and Write.

```yaml
- id: k8s/kubeconfig-readonly
  tool: [Edit, Write]
  match: { path: "~/.kube/config" }
  description: Claude must not edit ~/.kube/config.
```

**Fall back to a regex** when structure can't express it. `regex` searches one simple command's
text.

```yaml
- id: db/no-drop
  match: { cmd: psql, regex: "/drop\\s+table/i" }
  action: ask
```

## Commands

| Command                         | What it does                                           |
| ------------------------------- | ------------------------------------------------------ |
| `/arbiter`, `/arbiter help`     | Rule and error counts, and this list                   |
| `/arbiter init`                 | Where rule files go and an example to start from       |
| `/arbiter list [filter\|id]`    | Rules sorted by id, or one rule's YAML                 |
| `/arbiter check "<command>"`    | The verdict a Bash command would get; nothing runs     |
| `/arbiter test`                 | Every rule's inline tests, plus skipped files          |
| `/arbiter reload`               | Re-read rule files                                     |
| `/arbiter pane`                 | Live pane of recent verdicts and load errors           |
| `/arbiter history`              | Hits per rule over 90 days, and rules that never fired |
| `/arbiter history prune [days]` | Remove history files older than `days` (default 90)    |

Every deny, ask, and warn is logged to `~/.claude/arbiter/history/<session-id>.jsonl` for tuning
and audit. Use `/arbiter history` to find dead rules, noisy rules, and asks you always allow.
Arguments are left out of the log; see the [reference](../../docs/arbiter/reference.md#history).

## Testing your rules

Give every rule a `tests:` block. Keys are the expected outcome, values are inputs: a Bash command,
or a path for path rules. `allow` means the rule must not fire.

```yaml
tests:
  deny: ["aws s3 ls", "cd x && aws s3 ls | head"]
  allow: ["aws-vault exec dev -- aws s3 ls", 'echo "aws s3 ls"']
```

Run them with `/arbiter test`, or from a shell with `script/arbiter-test`, which fails on any
failing test or skipped file (handy in CI, but it needs a signed-in `claude`).

## Limits

- Rules see one simple command at a time, so pipelines (`curl ... | sh`) can't be expressed yet.
- Wrappers outside the built-in list (for example `stdbuf`, `ionice`, `script`) hide the command
  from `cmd`-based rules. The list covers `sudo`, `doas`, `env`, `time`, `nice`, `nohup`,
  `timeout`, `xargs`, `watch`, `exec`, `command`, `builtin`, `aws-vault exec`, and `op run`.
- Heredoc bodies are treated as data, even unquoted ones that would expand `$(...)`.
- `action: rewrite` is accepted but acts as `deny` until it's implemented.
- Rules only fire on Bash commands and on file tools' `file_path`. A rule for an MCP tool can name
  it in `tool`, but has nothing to match yet.

## More

- [Examples](examples/rules.yaml): commented, tested rules to copy from.
- [Rule reference](../../docs/arbiter/reference.md): every field, matcher, and evaluation detail.
- [Specs](root.yass.yaml): the normative behavior, in [yass](https://github.com/shakefu/yass).
- [Design](../../docs/arbiter/design.md) and [decisions](../../docs/arbiter/decisions.md).
