# arbiter: warn feedback and repeat rules

Two additions borrowed from captain-hook
([Less prompts, more guardrails](https://yasyf.com/writing/less-prompts-more-guardrails)):

1. **Warn reaches Claude.** A `warn` verdict adds its message to the call's result as context,
   not only to the transcript.
2. **Repeat rules.** A rule with `repeat:` fires only once its `match` has hit N times within the
   last M tool calls, optionally reset by a call to another tool. It catches patterns no single
   call shows, like rerunning the same failing test with no edits in between.

Everything else from the comparison (content rules, Stop gates, LLM judges, transcript mining) is
out of scope here. See [decisions](decisions.md#warn-reaches-claude) and
[decisions](decisions.md#repeat-rules).

## 1. Warn reaches Claude

**Problem.** `warn` logs to the transcript and runs the call. Claude never sees the line, so it
repeats the behavior. Feeding the line back is what makes a hook steer the next call rather than
only judge this one.

**Change.** In `guardCall`, a `warn` verdict still logs the message, then runs the call and adds
`message` to the result's `context`, exactly as a rewrite adds its note. A rewritten call whose
second verdict is `warn` gets both notes, rewrite note first. A refusal result gets no notes.

**Files.**

- `index.ts`: `run()` takes a list of notes; the warn branch passes `v.message`.
- `index.yass.yaml`, `root.yass.yaml`: warn MUST add the message as context.
- `index.test.ts`: warn result carries `context`; rewrite+warn carries both.
- `README.md`, `reference.md`: the warn row says Claude reads the line.

## 2. Repeat rules

### Syntax

```yaml
- id: test/no-blind-rerun
  match: { cmd: [pytest, go], args: [[test]] }
  repeat:
    count: 3 # fire on the 3rd matching call...
    within: 10 # ...among the last 10 tool calls (this one included). Default 20.
    reset_on: [Edit, Write] # a call to one of these tools starts the count over
    same: true # count only calls with the same command (or file path)
  action: warn
  description: The same test ran 3 times with no code change in between.
  hint: Narrow to the failing case and read the failure before running it again.
  tests:
    warn:
      - [pytest -x, pytest -x, pytest -x]
    allow:
      - [pytest -x, pytest -x]
      - [pytest -x, { tool: Edit }, pytest -x, pytest -x]
      - [pytest -k a, pytest -k b, pytest -k c]
```

| Key        | Required | Type                        | Default | Meaning                                                             |
| ---------- | -------- | --------------------------- | ------- | ------------------------------------------------------------------- |
| `count`    | yes      | integer, 2 or more          |         | Matching calls, this one included, needed before the rule fires.    |
| `within`   |          | integer, `count` to 200     | `20`    | How many recent tool calls, this one included, the count looks at.  |
| `reset_on` |          | pattern or list of patterns |         | Tools whose call clears every earlier match. Exact name or /regex/. |
| `same`     |          | boolean                     | `false` | Count only earlier calls with the same command text or file path.   |

`repeat` is not allowed with `action: rewrite`.

### Semantics

- "Matches" means the rule's `match`/`unless` hold for the call, as today. A repeat rule then
  fires only when `1 + (earlier matching calls)` reaches `count`, counting back through the last
  `within - 1` recorded calls and stopping at the most recent `reset_on` call.
- Once it fires it keeps firing on each further matching call until a reset or the window slides
  past the earlier hits. Each fire repeats the nudge, which is what you want while it continues.
- Every tool call that **runs** is recorded, matched or not, because `within` counts all calls.
  A denied or refused call did not run and is not recorded. A rewritten call is recorded as the
  command that ran.
- The message line adds the count: `arbiter <id>: <description> <hint> (<n> matching calls in
the last <within>)`.
- History is per session and in memory: at most 200 calls, cleared at `session.start`. Calls
  from subagents share it, so interleaved subagent work counts toward the same window.

### Engine (pure)

The engine stays free of state; the caller passes history in.

```ts
export type Call = { tool: string; key: string; matched: string[] };

// Bash: the command text; file tools: file_path; otherwise "".
export function callKey(tool: string, input: Record<string, unknown>): string;

// Ids of repeat rules whose match/unless hold for this call, ignoring count.
export function matchedRepeat(tool, input, rules, home): string[];

// New optional last argument: recorded calls, oldest first. Default [].
export function evaluate(tool, input, rules, home, past?: Call[]): Verdict;
```

### Mod (`index.ts`)

- A module-level `calls: Call[]`, capped at 200, cleared on `session.start`.
- `run()` pushes `{ tool, key, matched }` for the call actually passed on, before running it.
- `guardCall` and the rewrite re-check pass `calls` to `evaluate`. `/arbiter check` does too,
  so it shows what would happen right now in this session.

### Rule file and schema

- `rules.ts`: `repeat` in `RULE_KEYS`; validate keys, types, ranges, `reset_on` regexes, and the
  rewrite exclusion. Parsed rules carry `repeat` with `within` and `same` defaulted.
- `rule.schema.json`: `repeat` object; test entries may be sequences.
- `script/arbiter-test` keeps checking key lists against the schema.

### Inline tests

For a repeat rule each test input is a **sequence** of calls, and the outcome is checked on the
last one. An element is a string (a command, a path for path rules, or a tool name for rules
without `match`) or `{ tool: <name> }` for a call to that tool with no arguments, used to place
resets or fill the window. A repeat rule with plain string inputs is a file error, as is a
sequence on a rule without `repeat`. Results print a sequence as its elements joined by `->`.

### Tests to add

- engine: count reached and not; `within` slides past early hits; `reset_on` clears;
  `same` separates commands; message carries the count; `matchedRepeat` ignores count;
  `runRuleTests` runs sequences.
- rules: `repeat` validation errors (count < 2, within < count or > 200, unknown key,
  bad regex in `reset_on`, with rewrite, string inputs on a repeat rule, sequences without one).
- index: a third rerun warns with context; an Edit in between resets; denied calls don't count;
  `session.start` clears history.

### Docs

`reference.md` (Rule table, new Repeat section, Tests), `README.md` (recipe), `examples/rules.yaml`
(tested example), `decisions.md` (two entries), yass specs (`engine`, `rules`, `index`, `root`).

## Out of scope

- Classifier/LLM judge behind the repeat counter (the natural next step; see open items).
- Per-agent windows, once the call event exposes an agent id.
- Persisting the window across sessions.
