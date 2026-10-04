# arbiter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship arbiter, a Claude Code mod in the `agent-tools` plugin that enforces YAML rules at every tool call.

**Architecture:** Three pure TypeScript modules (`shell.ts` parses Bash, `rules.ts` loads and merges YAML rule files, `engine.ts` decides verdicts) plus one hooks module (`index.ts`) that is the only code touching the mods API `$`. YAML parsing uses a vendored single-file js-yaml build.

**Tech Stack:** TypeScript ES modules loaded directly by Claude Code ≥ 2.1.287 (no build step), `claude-code/testing` test kit via `claude plugin test`, js-yaml 4.1.0 (vendored), yass for specs.

**Spec:** `hooks/arbiter/*.yass.yaml` (normative; start at `root.yass.yaml`, browse with `yass list` / `yass query <target>` from `hooks/arbiter/`). Overview: `docs/arbiter/design.md`. Decisions: `docs/arbiter/decisions.md`.

## Global Constraints

- Claude Code ≥ v2.1.287 (developed against 2.1.289).
- Hooks module: `hooks/arbiter/index.ts`, listed in `hooks/hooks.json` as `"modules": ["./arbiter/index.ts"]`.
- `shell.ts`, `rules.ts`, `engine.ts` are pure: no `$`, no I/O, no clock. Only `index.ts` touches `$`.
- Imports: relative paths inside the plugin only; the one bare import allowed is `claude-code`. No npm runtime dependencies; js-yaml is vendored at `hooks/arbiter/vendor/js-yaml.mjs`.
- Mods static-analysis rules: write every API call in full (`$.fs.read(...)`), never alias or destructure `$`; pass `$` only to functions declared at top level of `index.ts`; event names in `on()` are string literals.
- Tests: files ending `.test.ts`, run from the repo root with `claude plugin test`. Each file has at least one `test()`.
- Rule file layers, lowest to highest: `<plugin>/rules/*.yaml`, `~/.claude/rules/arbiter/*.yaml`, `<project>/.claude/rules/arbiter/*.yaml`.
- Deny message line form: `arbiter <id>: <reason> <hint>` (missing parts omitted).
- Verdict precedence: deny > ask > warn > allow; `rewrite` behaves as `deny`.
- After changing any `*.yass.yaml`: `cd hooks/arbiter && yass validate && yass lint`.
- Commits: conventional commits (`feat:`, `test:`, `docs:`), ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Commit messages and heredocs** — `git commit -m "$(cat <<'EOF' … aws sso login … EOF)"` must not be denied. Pinned in Task 2 (`heredoc body is data`) and Task 5 (`text inside heredoc does not fire`).
2. **Quoted text mentioning a command** — `echo "aws s3 ls"` or `grep 'kubectl delete' notes.md` must be allowed. Pinned in Task 2 (`quotes are data`) and Task 5 (`quoted mention does not fire`).
3. **Session started in `$HOME`** — project root equals home, so the user layer would load twice and every rule would hit "duplicate id". Pinned in Task 6 (`project layer skipped when it is the user layer`).
4. **One broken rule file** — a typo must skip only that file and surface in the toast and pane, never disable the rest. Pinned in Task 6 (`broken file is skipped and reported`).
5. **Non-interactive runs** — in `claude -p` an `ask` rule has no one to ask and must deny, not hang or allow. Pinned in Task 6 (`ask with nobody to answer denies`).

---

### Task 1: Scaffold the mod and verify toolchain assumptions

**Files:**

- Create: `hooks/hooks.json`
- Create: `hooks/arbiter/index.ts`
- Create: `hooks/arbiter/vendor/js-yaml.mjs` (downloaded)
- Create: `hooks/arbiter/smoke.test.ts`

**Interfaces:**

- Consumes: nothing.
- Produces: a loadable mod; confirmed import specifier style (`./x.ts`); confirmed `claude-code` type name for `$`; confirmed whether test files can import `node:fs`.

- [ ] **Step 1: Vendor js-yaml**

```bash
mkdir -p hooks/arbiter/vendor
curl -fsSL -o hooks/arbiter/vendor/js-yaml.mjs https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.mjs
shasum -a 256 hooks/arbiter/vendor/js-yaml.mjs
```

Expected hash: `16f210b939b359b6ec8dde581eb62c157185711dc7b719b33779c43db5c31a91`. Stop if it differs.

- [ ] **Step 2: Write `hooks/hooks.json`**

```json
{
  "description": "arbiter: enforce YAML rules at every tool call",
  "modules": ["./arbiter/index.ts"]
}
```

- [ ] **Step 3: Write a minimal `hooks/arbiter/index.ts`**

```ts
import { load } from "./vendor/js-yaml.mjs";

export function register(on) {
  on("session.start", async ($, e, next) => {
    await $.command.register({
      name: "arbiter",
      description: "Show and test arbiter rules",
    });
    return next(e);
  });
  on("command.run", { command: "arbiter" }, async () => {
    return { text: "yaml ok: " + JSON.stringify(load("a: [1, 2]")) };
  });
}
```

- [ ] **Step 4: Write the smoke test `hooks/arbiter/smoke.test.ts`**

```ts
import { expect, test } from "claude-code/testing";
import { readFileSync } from "node:fs";
import { load } from "./vendor/js-yaml.mjs";

test("vendored yaml parses", () => {
  expect(load("a: [1, 2]")).toEqual({ a: [1, 2] });
});

test("test files can read the repo", () => {
  expect(readFileSync("hooks/hooks.json", "utf8")).toContain(
    "arbiter/index.ts",
  );
});

test("mod command answers", async ($, on) => {
  on("command.register", () => ({ value: undefined }));
  on("session.start", () => ({ cwd: "/work" }));
  await $.session.start({
    surface: "terminal",
    isInteractive: true,
    cwd: "/work",
  });
  const answer = await $.command.run({ command: "arbiter", args: "" });
  expect(answer.text).toBe('yaml ok: {"a":[1,2]}');
});
```

- [ ] **Step 5: Validate and run**

```bash
claude plugin validate .
claude plugin test
```

Expected: validate prints `hooks: session.start, command.run{command=arbiter}` and `✔ Validation passed`; 3 tests pass.

Record the outcome of each assumption in the commit message body:

- If `test files can read the repo` fails because `node:fs` is unavailable or cwd differs: delete that test and use the **fallback** in Task 7 Step 3.
- If validate rejects the vendored file, stop and report the exact error; do not hand-edit js-yaml.

- [ ] **Step 6: Confirm import style and the `$` type name**

```bash
claude --plugin-dir . -p "/arbiter"
ls .claude-plugin/types/claude-code/
grep -n "interface EngineInterface" .claude-plugin/types/claude-code/index.d.ts | head -3
```

Expected: `agent-tools: yaml ok: {"a":[1,2]}`, and a match for `interface EngineInterface`. If the name differs, use the name found wherever later tasks write `EngineInterface`. Add `.claude-plugin/types/` and any generated root `tsconfig.json` to `.gitignore`.

- [ ] **Step 7: Commit**

```bash
git add hooks/hooks.json hooks/arbiter/index.ts hooks/arbiter/vendor/js-yaml.mjs hooks/arbiter/smoke.test.ts .gitignore
git commit -m "feat(arbiter): scaffold mod with vendored js-yaml"
```

---

### Task 2: Shell parser (`shell.ts`)

Implements `shell@parse` and `shell@Wrappers` (`yass query shell@parse`).

**Files:**

- Create: `hooks/arbiter/shell.ts`
- Test: `hooks/arbiter/shell.test.ts`

**Interfaces:**

- Consumes: nothing.
- Produces:

  ```ts
  export type SubCommand = {
    raw: string;
    cmd: string;
    args: string[];
    flags: string[];
    env: Record<string, string>;
    wrappers: string[];
  };
  export function parse(command: string): SubCommand[];
  ```

- [ ] **Step 1: Write the failing tests `hooks/arbiter/shell.test.ts`**

```ts
import { expect, test } from "claude-code/testing";
import { parse } from "./shell.ts";

const cmds = (s: string) => parse(s).map((c) => c.cmd);
const raw = (s: string) => [
  { raw: s, cmd: "", args: [], flags: [], env: {}, wrappers: [] },
];

test("splits on control operators", () => {
  expect(cmds("a && b || c; d | e & f\ng |& h")).toEqual([
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
  ]);
});

test("fills every field", () => {
  const s =
    "AWS_PROFILE=prod /usr/bin/aws --region us-east-1 s3 ls --recursive=true";
  expect(parse(s)).toEqual([
    {
      raw: s,
      cmd: "aws",
      args: ["us-east-1", "s3", "ls"],
      flags: ["--region", "--recursive"],
      env: { AWS_PROFILE: "prod" },
      wrappers: [],
    },
  ]);
});

test("quotes are data", () => {
  expect(cmds(`echo "aws s3 ls; kubectl" 'a && b'`)).toEqual(["echo"]);
  expect(parse(`echo "a b" 'c d' e\\ f`)[0].args).toEqual([
    "a b",
    "c d",
    "e f",
  ]);
});

test("substitutions are parsed and come first", () => {
  expect(
    cmds("echo $(aws sts get-caller-identity) `kubectl get pods`"),
  ).toEqual(["aws", "kubectl", "echo"]);
  expect(cmds('echo "$(aws s3 ls)"')).toEqual(["aws", "echo"]);
  expect(cmds("diff <(aws s3 ls) x")).toEqual(["aws", "diff"]);
  expect(cmds("echo $((1 + 2)) ${HOME}")).toEqual(["echo"]);
});

test("bash -c script is parsed", () => {
  expect(cmds(`bash -c 'aws s3 ls | head'`)).toEqual(["bash", "aws", "head"]);
  expect(cmds(`sh -lc "kubectl get pods"`)).toEqual(["sh", "kubectl"]);
});

test("heredoc body is data", () => {
  const c = `git commit -m "$(cat <<'EOF'\nfix(arbiter): never run aws sso login\nEOF\n)"`;
  expect(cmds(c)).toEqual(["cat", "git"]);
  expect(cmds("cat <<-END\n\taws s3 ls\n\tEND\npwd")).toEqual(["cat", "pwd"]);
});

test("comments are ignored", () => {
  expect(cmds("ls # aws s3 ls\npwd")).toEqual(["ls", "pwd"]);
  expect(parse("echo a#b")[0].args).toEqual(["a#b"]);
});

test("redirections are neither args nor flags", () => {
  const [c] = parse("aws s3 ls > out.txt 2>&1 < in.txt &>> log");
  expect(c.args).toEqual(["s3", "ls"]);
  expect(c.flags).toEqual([]);
});

test("bare -- ends flags and is dropped", () => {
  const [c] = parse("git checkout -- -weird");
  expect(c.flags).toEqual([]);
  expect(c.args).toEqual(["checkout", "-weird"]);
});

test("aws-vault exec is unwrapped", () => {
  const out = parse("aws-vault exec lytxread -- aws s3 ls").map(
    ({ cmd, args, wrappers }) => ({ cmd, args, wrappers }),
  );
  expect(out).toEqual([
    { cmd: "aws-vault", args: ["exec", "lytxread"], wrappers: [] },
    { cmd: "aws", args: ["s3", "ls"], wrappers: ["aws-vault"] },
  ]);
  expect(parse("aws-vault exec lytxread aws s3 ls")[1]).toMatchObject({
    cmd: "aws",
    wrappers: ["aws-vault"],
  });
  expect(cmds("aws-vault list")).toEqual(["aws-vault"]);
});

test("wrappers nest and are inherited through bash -c", () => {
  const subs = parse(`sudo -u root aws-vault exec p -- bash -c 'aws s3 ls'`);
  expect(subs.find((s) => s.cmd === "aws")!.wrappers).toEqual([
    "sudo",
    "aws-vault",
  ]);
});

test("other wrappers", () => {
  expect(parse("env FOO=1 aws s3 ls")[1]).toMatchObject({
    cmd: "aws",
    env: { FOO: "1" },
    wrappers: ["env"],
  });
  expect(parse("timeout 5 kubectl get pods")[1]).toMatchObject({
    cmd: "kubectl",
    wrappers: ["timeout"],
  });
  expect(parse("xargs -n 1 aws s3 rm")[1]).toMatchObject({
    cmd: "aws",
    args: ["s3", "rm"],
    wrappers: ["xargs"],
  });
  expect(parse("op run -- terraform apply")[1]).toMatchObject({
    cmd: "terraform",
    wrappers: ["op"],
  });
  expect(cmds("op read op://vault/item")).toEqual(["op"]);
  expect(cmds("sudo")).toEqual(["sudo"]);
});

test("subshells and reserved words", () => {
  expect(
    cmds("(cd x && aws s3 ls); if kubectl get ns; then echo ok; fi"),
  ).toEqual(["cd", "aws", "kubectl", "echo"]);
});

test("empty input and empty segments", () => {
  expect(parse("")).toEqual([]);
  expect(parse("   ")).toEqual([]);
  expect(parse(" ;; ; ")).toEqual([]);
  expect(parse("FOO=bar")).toEqual([]);
});

test("unterminated input falls back to one raw sub-command", () => {
  for (const s of [
    `echo 'x`,
    'echo "x',
    "echo $(ls",
    "echo `ls",
    "cat <<EOF\nbody",
    "cat <<EOF",
  ]) {
    expect(parse(s)).toEqual(raw(s));
  }
});
```

- [ ] **Step 2: Run to verify failure**

Run: `claude plugin test`
Expected: `shell.test.ts` fails to import `./shell.ts`.

- [ ] **Step 3: Implement `hooks/arbiter/shell.ts`**

```ts
// Bash command string -> simple commands. Spec: shell.yass.yaml
export type SubCommand = {
  raw: string;
  cmd: string;
  args: string[];
  flags: string[];
  env: Record<string, string>;
  wrappers: string[];
};

class ShellError extends Error {}

const RESERVED = new Set([
  "!",
  "{",
  "}",
  "if",
  "then",
  "else",
  "elif",
  "fi",
  "do",
  "done",
  "while",
  "until",
]);
const SHELLS = new Set(["bash", "sh", "zsh"]);
const STOP = new Set([" ", "\t", "\n", ";", "&", "|", "<", ">", "(", ")"]);
const REDIRECT = /&>>|&>|<<<|<<-|<<|>>|>&|<&|<>|>\||>|</y;

// Number of leading words a wrapper consumes, or null when it isn't acting as a wrapper.
type Unwrap = (rest: string[]) => number | null;

const flagsThen =
  (valued: string[]): Unwrap =>
  (rest) => {
    let i = 0;
    while (i < rest.length && rest[i].startsWith("-") && rest[i] !== "-") {
      if (rest[i] === "--") return i + 1;
      i += valued.includes(rest[i]) ? 2 : 1;
    }
    return Math.min(i, rest.length);
  };

const WRAPPERS: Record<string, Unwrap> = {
  sudo: flagsThen(["-u", "-g", "-U", "-C", "-h", "-p", "-r", "-t", "-D"]),
  env: flagsThen(["-u", "-C", "-S"]),
  time: flagsThen(["-f", "-o"]),
  nice: flagsThen(["-n"]),
  timeout: (rest) =>
    Math.min(
      flagsThen(["-s", "-k", "--signal", "--kill-after"])(rest)! + 1,
      rest.length,
    ),
  xargs: flagsThen(["-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a"]),
  "aws-vault": (rest) => {
    if (rest[0] !== "exec") return null;
    const dd = rest.indexOf("--");
    if (dd >= 0) return dd + 1;
    let i = 1;
    while (i < rest.length && rest[i].startsWith("-")) i++;
    return Math.min(i + 1, rest.length);
  },
  op: (rest) => {
    if (rest[0] !== "run") return null;
    const dd = rest.indexOf("--");
    return dd >= 0 ? dd + 1 : null;
  },
};

export function parse(command: string): SubCommand[] {
  try {
    return new Lexer(command).list(false, []);
  } catch {
    return [
      { raw: command, cmd: "", args: [], flags: [], env: {}, wrappers: [] },
    ];
  }
}

class Lexer {
  i = 0;
  heredocs: { delim: string; strip: boolean }[] = [];
  constructor(private s: string) {}

  // Commands until EOF, or until the `)` closing a `$(` / `<(` when inSub.
  list(inSub: boolean, wrappers: string[]): SubCommand[] {
    const out: SubCommand[] = [];
    let depth = 0;
    for (;;) {
      this.blanks();
      const start = this.i;
      const words: string[] = [];
      this.words(words, out, wrappers);
      out.push(...build(words, this.s.slice(start, this.i).trim(), wrappers));
      if (this.i >= this.s.length) {
        if (inSub || depth > 0) throw new ShellError("unterminated (");
        if (this.heredocs.length)
          throw new ShellError("heredoc has no terminator");
        return out;
      }
      const c = this.s[this.i++];
      if (c === ")") {
        if (depth > 0) depth--;
        else if (inSub) return out;
      } else if (c === "(") depth++;
      else if (c === "\n") this.readHeredocs();
      else if (
        (c === "&" || c === "|") &&
        (this.s[this.i] === c || (c === "|" && this.s[this.i] === "&"))
      )
        this.i++;
    }
  }

  private blanks() {
    while (this.i < this.s.length) {
      if (this.s[this.i] === " " || this.s[this.i] === "\t") this.i++;
      else if (this.s.startsWith("\\\n", this.i)) this.i += 2;
      else return;
    }
  }

  private words(words: string[], out: SubCommand[], wrappers: string[]) {
    for (;;) {
      this.blanks();
      const c = this.s[this.i];
      if (
        c === undefined ||
        c === "\n" ||
        c === ";" ||
        c === "|" ||
        c === "(" ||
        c === ")"
      )
        return;
      if (c === "&") {
        if (this.s[this.i + 1] !== ">") return;
        this.redirect(out, wrappers);
      } else if (c === "<" || c === ">") this.redirect(out, wrappers);
      else if (c === "#")
        while (this.i < this.s.length && this.s[this.i] !== "\n") this.i++;
      else {
        const w = this.word(out, wrappers);
        const next = this.s[this.i];
        if (/^\d+$/.test(w) && (next === "<" || next === ">"))
          this.redirect(out, wrappers);
        else words.push(w);
      }
    }
  }

  private word(out: SubCommand[], wrappers: string[]): string {
    let w = "";
    while (this.i < this.s.length && !STOP.has(this.s[this.i])) {
      const c = this.s[this.i];
      if (c === "\\") {
        if (this.s[this.i + 1] !== "\n") w += this.s[this.i + 1] ?? "";
        this.i += 2;
      } else if (c === "'") {
        const j = this.s.indexOf("'", this.i + 1);
        if (j < 0) throw new ShellError("unterminated single quote");
        w += this.s.slice(this.i + 1, j);
        this.i = j + 1;
      } else if (c === '"') w += this.dquote(out, wrappers);
      else w += this.dollar(out, wrappers) ?? this.s[this.i++];
    }
    return w;
  }

  private dquote(out: SubCommand[], wrappers: string[]): string {
    let w = "";
    this.i++;
    while (this.i < this.s.length) {
      const c = this.s[this.i];
      if (c === '"') {
        this.i++;
        return w;
      }
      if (c === "\\" && '"\\$`\n'.includes(this.s[this.i + 1] ?? "x")) {
        if (this.s[this.i + 1] !== "\n") w += this.s[this.i + 1];
        this.i += 2;
      } else w += this.dollar(out, wrappers) ?? this.s[this.i++];
    }
    throw new ShellError("unterminated double quote");
  }

  // Substitutions at this.i: parses command bodies into out, returns the source text consumed.
  private dollar(out: SubCommand[], wrappers: string[]): string | null {
    const start = this.i;
    if (this.s[this.i] === "`") {
      let j = this.i + 1;
      while (j < this.s.length && this.s[j] !== "`")
        j += this.s[j] === "\\" ? 2 : 1;
      if (j >= this.s.length) throw new ShellError("unterminated backtick");
      out.push(...new Lexer(this.s.slice(this.i + 1, j)).list(false, wrappers));
      this.i = j + 1;
    } else if (this.s.startsWith("$((", this.i)) {
      let depth = 0;
      let j = this.i + 1;
      for (; j < this.s.length; j++) {
        if (this.s[j] === "(") depth++;
        else if (this.s[j] === ")" && --depth === 0) break;
      }
      if (j >= this.s.length) throw new ShellError("unterminated $((");
      this.i = j + 1;
    } else if (this.s.startsWith("$(", this.i)) {
      this.i += 2;
      out.push(...this.list(true, wrappers));
    } else if (this.s.startsWith("${", this.i)) {
      const j = this.s.indexOf("}", this.i);
      if (j < 0) throw new ShellError("unterminated ${");
      this.i = j + 1;
    } else return null;
    return this.s.slice(start, this.i);
  }

  private redirect(out: SubCommand[], wrappers: string[]) {
    REDIRECT.lastIndex = this.i;
    const op = REDIRECT.exec(this.s)![0];
    this.i += op.length;
    if ((op === "<" || op === ">") && this.s[this.i] === "(") {
      this.i++;
      out.push(...this.list(true, wrappers));
      return;
    }
    if ((op === ">&" || op === "<&") && /[0-9-]/.test(this.s[this.i] ?? "")) {
      while (/[0-9-]/.test(this.s[this.i] ?? "")) this.i++;
      return;
    }
    this.blanks();
    const target = this.word(out, wrappers);
    if (target === "") throw new ShellError(`missing target after ${op}`);
    if (op === "<<" || op === "<<-")
      this.heredocs.push({ delim: target, strip: op === "<<-" });
  }

  private readHeredocs() {
    for (const h of this.heredocs.splice(0)) {
      for (;;) {
        if (this.i >= this.s.length)
          throw new ShellError(`heredoc ${h.delim} has no terminator`);
        let j = this.s.indexOf("\n", this.i);
        if (j < 0) j = this.s.length;
        const line = this.s.slice(this.i, j);
        this.i = Math.min(j + 1, this.s.length);
        if ((h.strip ? line.replace(/^\t+/, "") : line) === h.delim) break;
      }
    }
  }
}

function build(words: string[], raw: string, wrappers: string[]): SubCommand[] {
  let i = 0;
  while (i < words.length && RESERVED.has(words[i])) i++;
  const env: Record<string, string> = {};
  for (; i < words.length; i++) {
    const m = /^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/s.exec(words[i]);
    if (!m) break;
    env[m[1]] = m[2];
  }
  if (i >= words.length) return [];
  const cmd = words[i].split("/").pop()!;
  const rest = words.slice(i + 1);
  const n = WRAPPERS[cmd]?.(rest) ?? null;
  if (n !== null)
    return [
      make(raw, cmd, rest.slice(0, n), env, wrappers),
      ...build(rest.slice(n), raw, [...wrappers, cmd]),
    ];
  const sub = make(raw, cmd, rest, env, wrappers);
  const script = SHELLS.has(cmd) ? cScript(rest) : null;
  return script === null
    ? [sub]
    : [sub, ...new Lexer(script).list(false, wrappers)];
}

function make(
  raw: string,
  cmd: string,
  words: string[],
  env: Record<string, string>,
  wrappers: string[],
): SubCommand {
  const args: string[] = [];
  const flags: string[] = [];
  let positional = false;
  for (const w of words) {
    if (!positional && w === "--") positional = true;
    else if (!positional && w.length > 1 && w.startsWith("-"))
      flags.push(w.split("=")[0]);
    else args.push(w);
  }
  return { raw, cmd, args, flags, env, wrappers };
}

// The script of `bash -c script`, or null.
function cScript(rest: string[]): string | null {
  const c = rest.findIndex((w) => /^-[a-zA-Z]*c[a-zA-Z]*$/.test(w));
  if (c < 0) return null;
  return rest.slice(c + 1).find((w) => !w.startsWith("-")) ?? null;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `claude plugin test`
Expected: all `shell.test.ts` tests pass. If one fails, fix `shell.ts`, not the test, unless the test contradicts `shell.yass.yaml`.

- [ ] **Step 5: Commit**

```bash
git add hooks/arbiter/shell.ts hooks/arbiter/shell.test.ts
git commit -m "feat(arbiter): parse bash into sub-commands"
```

---

### Task 3: Rule file parsing and validation (`rules.ts`, part 1)

Implements `rules@parseRuleFile` and `rules@RuleFormat`.

**Files:**

- Create: `hooks/arbiter/rules.ts`
- Test: `hooks/arbiter/rules.test.ts`

**Interfaces:**

- Consumes: `load`, `YAMLException` from `./vendor/js-yaml.mjs`.
- Produces:

  ```ts
  export type Layer = "plugin" | "user" | "project";
  export type Action = "deny" | "ask" | "warn" | "rewrite";
  export type Outcome = "deny" | "ask" | "warn" | "allow";
  export type Matcher = {
    cmd?: string | string[];
    args?: (string | string[])[];
    flags?: string[];
    wrapped_by?: string | string[];
    env?: Record<string, string>;
    regex?: string;
    path?: string | string[];
  };
  export type Rule = {
    id: string;
    tool: string | string[];
    match: Matcher[];
    unless: Matcher[];
    action: Action;
    to?: string;
    reason?: string;
    hint?: string;
    tests: Partial<Record<Outcome, string[]>>;
    layer: Layer;
    path: string;
    source: Record<string, unknown>;
  };
  export type Problem = {
    path: string;
    id?: string;
    line?: number;
    message: string;
  };
  export type ParsedFile = {
    path: string;
    layer: Layer;
    rules: Rule[];
    disable: string[];
    errors: Problem[];
  };
  export function parseRuleFile(
    text: string,
    path: string,
    layer: Layer,
  ): ParsedFile;
  ```

- [ ] **Step 1: Write the failing tests `hooks/arbiter/rules.test.ts`**

```ts
import { expect, test } from "claude-code/testing";
import { parseRuleFile } from "./rules.ts";

const P = "/r/a.yaml";
const parse = (text: string) => parseRuleFile(text, P, "user");
const messages = (text: string) => parse(text).errors.map((e) => e.message);

test("parses a valid file with defaults", () => {
  const f = parse(`
disable: [general/x]
rules:
  - id: aws/requires-vault
    match: { cmd: aws }
    unless: { wrapped_by: aws-vault }
    hint: Use aws-vault.
    tests:
      deny: ["aws s3 ls"]
`);
  expect(f.errors).toEqual([]);
  expect(f.disable).toEqual(["general/x"]);
  expect(f.rules[0]).toMatchObject({
    id: "aws/requires-vault",
    tool: "Bash",
    action: "deny",
    match: [{ cmd: "aws" }],
    unless: [{ wrapped_by: "aws-vault" }],
    hint: "Use aws-vault.",
    tests: { deny: ["aws s3 ls"] },
    layer: "user",
    path: P,
  });
});

test("match and unless lists stay lists", () => {
  const f = parse(`rules:\n  - id: a/b\n    match: [{ cmd: x }, { cmd: y }]\n`);
  expect(f.rules[0].match).toEqual([{ cmd: "x" }, { cmd: "y" }]);
  expect(f.rules[0].unless).toEqual([]);
});

test("empty and comment-only files are fine", () => {
  expect(parse("")).toMatchObject({ rules: [], errors: [] });
  expect(parse("# nothing yet\n")).toMatchObject({ rules: [], errors: [] });
});

test("invalid yaml reports the line", () => {
  const f = parse("rules:\n  - id: a/b\n    match: { cmd: aws\n");
  expect(f.rules).toEqual([]);
  expect(f.errors.length).toBe(1);
  expect(f.errors[0].line).toBeDefined();
});

test("schema problems reject the whole file", () => {
  const bad = `
rules:
  - id: ok/one
    match: { cmd: ls }
  - id: Bad Id
    match: { cmd: ls, path: "~/x" }
    action: block
    colour: red
  - id: ok/one
    match: { regex: "/(/" }
`;
  const f = parse(bad);
  expect(f.rules).toEqual([]);
  const m = f.errors.map((e) => e.message).join("\n");
  expect(m).toContain("id must match");
  expect(m).toContain("path cannot be combined with command fields");
  expect(m).toContain("action must be one of");
  expect(m).toContain("unknown key colour");
  expect(m).toContain("duplicate id ok/one");
  expect(m).toContain("invalid regex");
  expect(f.errors.find((e) => e.message.startsWith("duplicate"))!.line).toBe(9);
});

test("more schema checks", () => {
  expect(messages("rules:\n  - id: a/b\n")).toContain("match is required");
  expect(messages("rules:\n  - id: a/b\n    match: {}\n")).toContain(
    "match must be a non-empty mapping",
  );
  expect(
    messages("rules:\n  - id: a/b\n    match: { cmd: x }\n    to: y\n"),
  ).toContain("to must be a string and needs action: rewrite");
  expect(
    messages(
      "rules:\n  - id: a/b\n    match: { cmd: x }\n    tests: { block: [x] }\n",
    ),
  ).toContain("tests: unknown outcome block");
  expect(messages("other: 1\n")).toContain("unknown top-level key other");
  expect(messages("- just a list\n")).toContain(
    "top level must be a mapping with disable and/or rules",
  );
});

test("rewrite with to is accepted", () => {
  const f = parse(
    "rules:\n  - id: a/b\n    match: { cmd: rm }\n    action: rewrite\n    to: trash\n",
  );
  expect(f.errors).toEqual([]);
  expect(f.rules[0]).toMatchObject({ action: "rewrite", to: "trash" });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `claude plugin test`
Expected: `rules.test.ts` fails to import `./rules.ts`.

- [ ] **Step 3: Implement `hooks/arbiter/rules.ts`**

```ts
// Rule files: parse, validate, merge layers. Spec: rules.yass.yaml
import { load, YAMLException } from "./vendor/js-yaml.mjs";

export type Layer = "plugin" | "user" | "project";
export type Action = "deny" | "ask" | "warn" | "rewrite";
export type Outcome = "deny" | "ask" | "warn" | "allow";
export type Matcher = {
  cmd?: string | string[];
  args?: (string | string[])[];
  flags?: string[];
  wrapped_by?: string | string[];
  env?: Record<string, string>;
  regex?: string;
  path?: string | string[];
};
export type Rule = {
  id: string;
  tool: string | string[];
  match: Matcher[];
  unless: Matcher[];
  action: Action;
  to?: string;
  reason?: string;
  hint?: string;
  tests: Partial<Record<Outcome, string[]>>;
  layer: Layer;
  path: string;
  source: Record<string, unknown>;
};
export type Problem = {
  path: string;
  id?: string;
  line?: number;
  message: string;
};
export type ParsedFile = {
  path: string;
  layer: Layer;
  rules: Rule[];
  disable: string[];
  errors: Problem[];
};
export type RuleSet = {
  rules: Rule[];
  disabled: { rule: Rule; by: Layer }[];
  errors: Problem[];
  warnings: Problem[];
};

const RULE_KEYS = [
  "id",
  "tool",
  "match",
  "unless",
  "action",
  "to",
  "reason",
  "hint",
  "tests",
];
const MATCHER_KEYS = [
  "cmd",
  "args",
  "flags",
  "wrapped_by",
  "env",
  "regex",
  "path",
];
const ACTIONS = ["deny", "ask", "warn", "rewrite"];
const OUTCOMES = ["deny", "ask", "warn", "allow"];
const ID = /^[a-z0-9][a-z0-9._-]*(\/[a-z0-9._-]+)*$/;
const REGEX = /^\/(.*)\/([imsu]*)$/s;

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const isStr = (v: unknown): v is string => typeof v === "string";
const isStrs = (v: unknown): v is string[] =>
  Array.isArray(v) && v.every(isStr);
const strOrStrs = (v: unknown): v is string | string[] => isStr(v) || isStrs(v);

function badRegex(p: string): string | null {
  const m = REGEX.exec(p);
  if (!m) return null;
  try {
    new RegExp(m[1], m[2]);
    return null;
  } catch (e) {
    return `invalid regex ${p}: ${(e as Error).message}`;
  }
}

function checkMatcher(m: unknown, where: string, out: string[]) {
  if (!isObj(m) || Object.keys(m).length === 0) {
    out.push(`${where} must be a non-empty mapping`);
    return;
  }
  for (const k of Object.keys(m))
    if (!MATCHER_KEYS.includes(k)) out.push(`${where}: unknown key ${k}`);
  if ("path" in m && MATCHER_KEYS.some((k) => k !== "path" && k in m))
    out.push(`${where}: path cannot be combined with command fields`);
  const patterns: string[] = [];
  if ("cmd" in m) {
    if (strOrStrs(m.cmd)) patterns.push(...[m.cmd].flat());
    else out.push(`${where}.cmd must be a string or list of strings`);
  }
  if ("args" in m) {
    if (Array.isArray(m.args) && m.args.every(strOrStrs))
      patterns.push(...(m.args.flat() as string[]));
    else
      out.push(`${where}.args must be a list of strings or lists of strings`);
  }
  if ("flags" in m && !isStrs(m.flags))
    out.push(`${where}.flags must be a list of strings`);
  if ("wrapped_by" in m && !strOrStrs(m.wrapped_by))
    out.push(`${where}.wrapped_by must be a string or list of strings`);
  if ("env" in m) {
    if (isObj(m.env) && Object.values(m.env).every(isStr))
      patterns.push(...(Object.values(m.env) as string[]));
    else out.push(`${where}.env must map names to strings`);
  }
  if ("regex" in m) {
    if (isStr(m.regex) && REGEX.test(m.regex)) patterns.push(m.regex);
    else out.push(`${where}.regex must be written /body/flags`);
  }
  if ("path" in m) {
    if (strOrStrs(m.path)) patterns.push(...[m.path].flat());
    else out.push(`${where}.path must be a string or list of strings`);
  }
  for (const p of patterns) {
    const bad = badRegex(p);
    if (bad) out.push(`${where}: ${bad}`);
  }
}

function checkRule(r: unknown, i: number, out: string[]) {
  if (!isObj(r)) {
    out.push(`rules[${i}] must be a mapping`);
    return;
  }
  for (const k of Object.keys(r))
    if (!RULE_KEYS.includes(k)) out.push(`unknown key ${k}`);
  if (!isStr(r.id) || !ID.test(r.id)) out.push(`id must match ${ID.source}`);
  if ("tool" in r) {
    if (!strOrStrs(r.tool))
      out.push("tool must be a string or list of strings");
    else
      for (const t of [r.tool].flat()) {
        const bad = badRegex(t);
        if (bad) out.push(bad);
      }
  }
  if (!("match" in r)) out.push("match is required");
  for (const key of ["match", "unless"] as const) {
    if (!(key in r)) continue;
    const value = r[key];
    if (Array.isArray(value)) {
      if (value.length === 0) out.push(`${key} must not be empty`);
      value.forEach((m, j) => checkMatcher(m, `${key}[${j}]`, out));
    } else checkMatcher(value, key, out);
  }
  if ("action" in r && !ACTIONS.includes(r.action as string))
    out.push(`action must be one of ${ACTIONS.join(", ")}`);
  if ("to" in r && (r.action !== "rewrite" || !isStr(r.to)))
    out.push("to must be a string and needs action: rewrite");
  for (const k of ["reason", "hint"] as const)
    if (k in r && !isStr(r[k])) out.push(`${k} must be a string`);
  if ("tests" in r) {
    if (!isObj(r.tests)) out.push("tests must be a mapping");
    else
      for (const [k, v] of Object.entries(r.tests)) {
        if (!OUTCOMES.includes(k)) out.push(`tests: unknown outcome ${k}`);
        else if (!isStrs(v)) out.push(`tests.${k} must be a list of strings`);
      }
  }
}

// 1-based line of the nth `id: <id>`, so errors point somewhere useful.
function lineOf(text: string, id: string, nth: number): number | undefined {
  const esc = id.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
  const re = new RegExp(`\\bid:\\s*["']?${esc}["']?\\s*(#.*)?$`);
  let seen = 0;
  const lines = text.split("\n");
  for (let i = 0; i < lines.length; i++)
    if (re.test(lines[i]) && ++seen === nth) return i + 1;
  return undefined;
}

export function parseRuleFile(
  text: string,
  path: string,
  layer: Layer,
): ParsedFile {
  const fail = (errors: Problem[]): ParsedFile => ({
    path,
    layer,
    rules: [],
    disable: [],
    errors,
  });
  let doc: unknown;
  try {
    doc = load(text);
  } catch (e) {
    if (e instanceof YAMLException)
      return fail([
        {
          path,
          line: e.mark ? e.mark.line + 1 : undefined,
          message: e.reason ?? e.message,
        },
      ]);
    return fail([{ path, message: String(e) }]);
  }
  if (doc === undefined || doc === null)
    return { path, layer, rules: [], disable: [], errors: [] };
  if (!isObj(doc))
    return fail([
      {
        path,
        message: "top level must be a mapping with disable and/or rules",
      },
    ]);

  const errors: Problem[] = [];
  for (const k of Object.keys(doc))
    if (k !== "disable" && k !== "rules")
      errors.push({ path, message: `unknown top-level key ${k}` });
  if ("disable" in doc && !isStrs(doc.disable))
    errors.push({ path, message: "disable must be a list of rule ids" });
  if ("rules" in doc && !Array.isArray(doc.rules))
    errors.push({ path, message: "rules must be a list" });
  const raw: unknown[] = Array.isArray(doc.rules) ? doc.rules : [];
  const seen = new Map<string, number>();
  raw.forEach((r, i) => {
    const msgs: string[] = [];
    checkRule(r, i, msgs);
    const id = isObj(r) && isStr(r.id) ? r.id : undefined;
    const nth = id === undefined ? 0 : (seen.get(id) ?? 0) + 1;
    if (id !== undefined) seen.set(id, nth);
    if (nth > 1) msgs.push(`duplicate id ${id}`);
    const line = id === undefined ? undefined : lineOf(text, id, nth);
    for (const message of msgs) errors.push({ path, id, line, message });
  });
  if (errors.length) return fail(errors);

  const rules = (raw as Record<string, unknown>[]).map(
    (r): Rule => ({
      id: r.id as string,
      tool: (r.tool as string | string[] | undefined) ?? "Bash",
      match: [r.match].flat() as Matcher[],
      unless: r.unless === undefined ? [] : ([r.unless].flat() as Matcher[]),
      action: (r.action as Action | undefined) ?? "deny",
      to: r.to as string | undefined,
      reason: r.reason as string | undefined,
      hint: r.hint as string | undefined,
      tests: (r.tests as Rule["tests"] | undefined) ?? {},
      layer,
      path,
      source: r,
    }),
  );
  return {
    path,
    layer,
    rules,
    disable: (doc.disable as string[] | undefined) ?? [],
    errors: [],
  };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `claude plugin test`
Expected: all `rules.test.ts` tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/arbiter/rules.ts hooks/arbiter/rules.test.ts
git commit -m "feat(arbiter): parse and validate rule files"
```

---

### Task 4: Layer merging (`rules.ts`, part 2)

Implements `rules@loadLayers`.

**Files:**

- Modify: `hooks/arbiter/rules.ts` (append `loadLayers`)
- Test: `hooks/arbiter/rules.test.ts` (append)

**Interfaces:**

- Consumes: `ParsedFile`, `Rule`, `Layer`, `RuleSet` from Task 3.
- Produces: `export function loadLayers(files: ParsedFile[]): RuleSet`

- [ ] **Step 1: Append failing tests to `hooks/arbiter/rules.test.ts`**

```ts
import { loadLayers } from "./rules.ts";

const file = (
  path: string,
  layer: "plugin" | "user" | "project",
  body: string,
) => parseRuleFile(body, path, layer);
const rule = (id: string, cmd = "x") =>
  `  - id: ${id}\n    match: { cmd: ${cmd} }\n`;

test("higher layer replaces same id; order is plugin, user, project", () => {
  const set = loadLayers([
    file("/p/b.yaml", "project", `rules:\n${rule("a/one", "proj")}`),
    file("/u/a.yaml", "user", `rules:\n${rule("a/two")}`),
    file(
      "/g/a.yaml",
      "plugin",
      `rules:\n${rule("a/one", "plug")}${rule("a/three")}`,
    ),
  ]);
  expect(set.rules.map((r) => [r.id, r.layer])).toEqual([
    ["a/one", "project"],
    ["a/three", "plugin"],
    ["a/two", "user"],
  ]);
  expect(set.rules[0].match).toEqual([{ cmd: "proj" }]);
});

test("disable removes lower-layer rules only", () => {
  const set = loadLayers([
    file("/g/a.yaml", "plugin", `rules:\n${rule("g/x")}`),
    file(
      "/u/a.yaml",
      "user",
      `disable: [g/x, u/own, nope/missing]\nrules:\n${rule("u/own")}`,
    ),
  ]);
  expect(set.rules.map((r) => r.id)).toEqual(["u/own"]);
  expect(set.disabled.map((d) => [d.rule.id, d.by])).toEqual([["g/x", "user"]]);
  expect(set.warnings.map((w) => w.id)).toEqual(["u/own", "nope/missing"]);
});

test("broken file is left out and its errors kept", () => {
  const set = loadLayers([
    file("/u/a.yaml", "user", `rules:\n${rule("u/ok")}`),
    file("/u/b.yaml", "user", "rules:\n  - id: u/bad\n"),
  ]);
  expect(set.rules.map((r) => r.id)).toEqual(["u/ok"]);
  expect(set.errors.map((e) => e.path)).toEqual(["/u/b.yaml"]);
});

test("same id in two files of one layer keeps the first file", () => {
  const set = loadLayers([
    file("/u/b.yaml", "user", `rules:\n${rule("u/dup")}${rule("u/other")}`),
    file("/u/a.yaml", "user", `rules:\n${rule("u/dup")}`),
  ]);
  expect(set.rules.map((r) => [r.id, r.path])).toEqual([
    ["u/dup", "/u/a.yaml"],
  ]);
  expect(set.errors[0].message).toContain("/u/a.yaml");
  expect(set.errors[0].path).toBe("/u/b.yaml");
});
```

- [ ] **Step 2: Run to verify failure**

Run: `claude plugin test`
Expected: FAIL, `loadLayers` is not exported.

- [ ] **Step 3: Append `loadLayers` to `hooks/arbiter/rules.ts`**

```ts
const ORDER: Layer[] = ["plugin", "user", "project"];

export function loadLayers(files: ParsedFile[]): RuleSet {
  const errors: Problem[] = [];
  const warnings: Problem[] = [];
  const disabled: RuleSet["disabled"] = [];
  const byId = new Map<string, Rule>();
  for (const layer of ORDER) {
    const layerFiles = files
      .filter((f) => f.layer === layer)
      .sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
    const owner = new Map<string, string>();
    const added: Rule[] = [];
    const disables: { id: string; path: string }[] = [];
    for (const f of layerFiles) {
      if (f.errors.length) {
        errors.push(...f.errors);
        continue;
      }
      const clash = f.rules.find((r) => owner.has(r.id));
      if (clash) {
        errors.push({
          path: f.path,
          id: clash.id,
          message: `id ${clash.id} is already defined in ${owner.get(clash.id)}; file skipped`,
        });
        continue;
      }
      for (const r of f.rules) owner.set(r.id, f.path);
      added.push(...f.rules);
      disables.push(...f.disable.map((id) => ({ id, path: f.path })));
    }
    // byId holds only lower layers here, so disable never touches this layer's rules.
    for (const { id, path } of disables) {
      const r = byId.get(id);
      if (r) {
        byId.delete(id);
        disabled.push({ rule: r, by: layer });
      } else if (!disabled.some((d) => d.rule.id === id))
        warnings.push({
          path,
          id,
          message: `disable: no lower layer defines ${id}`,
        });
    }
    for (const r of added) byId.set(r.id, r);
  }
  return { rules: [...byId.values()], disabled, errors, warnings };
}
```

Note the first test's expected order: `Map` keeps first-insertion position when a key is replaced, so `a/one` stays first.

- [ ] **Step 4: Run tests to verify they pass**

Run: `claude plugin test`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/arbiter/rules.ts hooks/arbiter/rules.test.ts
git commit -m "feat(arbiter): merge rule layers with disable and override"
```

---

### Task 5: Verdict engine (`engine.ts`)

Implements `engine@evaluate` and `engine@runRuleTests`.

**Files:**

- Create: `hooks/arbiter/engine.ts`
- Test: `hooks/arbiter/engine.test.ts`

**Interfaces:**

- Consumes: `parse`, `SubCommand` (Task 2); `Rule`, `Matcher`, `Outcome`, `parseRuleFile` (Task 3).
- Produces:

  ```ts
  export type Verdict = { action: Outcome; fired: Rule[]; message: string };
  export type TestResult = {
    id: string;
    input: string;
    expected: Outcome;
    actual: Outcome;
    pass: boolean;
  };
  export function evaluate(
    tool: string,
    input: Record<string, unknown>,
    rules: Rule[],
    home: string,
  ): Verdict;
  export function runRuleTests(rule: Rule, home: string): TestResult[];
  export function expandHome(p: string, home: string): string;
  ```

- [ ] **Step 1: Write the failing tests `hooks/arbiter/engine.test.ts`**

```ts
import { expect, test } from "claude-code/testing";
import { evaluate, runRuleTests } from "./engine.ts";
import { parseRuleFile, type Rule } from "./rules.ts";

const HOME = "/home/u";
const rules = (yaml: string): Rule[] => {
  const f = parseRuleFile(yaml, "/r.yaml", "user");
  if (f.errors.length) throw new Error(JSON.stringify(f.errors));
  return f.rules;
};
const bash = (command: string, rs: Rule[]) =>
  evaluate("Bash", { command }, rs, HOME);

const VAULT = rules(`
rules:
  - id: aws/requires-vault
    match: { cmd: aws }
    unless: { wrapped_by: aws-vault }
    reason: AWS goes through aws-vault.
    hint: Use aws-vault exec lytxread -- aws.
  - id: aws/no-sso-login
    match: { cmd: aws, args: [sso, login] }
    hint: Never.
  - id: k8s/ask-delete
    match: { cmd: kubectl, args: [[delete, drain]] }
    action: ask
  - id: k8s/warn-get
    match: { cmd: kubectl, args: [get] }
    action: warn
  - id: fs/kubeconfig
    tool: [Edit, Write]
    match: { path: "~/.kube/config" }
  - id: mcp/no-prod
    tool: /^mcp__prod__/
    match: { regex: "/x/" }
`);

test("no match allows", () => {
  expect(bash("ls -la", VAULT)).toEqual({
    action: "allow",
    fired: [],
    message: "",
  });
});

test("deny lists every fired deny rule in rule order", () => {
  const v = bash("aws sso login", VAULT);
  expect(v.action).toBe("deny");
  expect(v.message).toBe(
    "arbiter aws/requires-vault: AWS goes through aws-vault. Use aws-vault exec lytxread -- aws.\narbiter aws/no-sso-login: Never.",
  );
});

test("unless excuses the same sub-command", () => {
  expect(bash("aws-vault exec lytxread -- aws s3 ls", VAULT).action).toBe(
    "allow",
  );
  expect(
    bash("aws-vault exec lytxread -- true && aws s3 ls", VAULT).action,
  ).toBe("deny");
});

test("quoted mention does not fire", () => {
  expect(
    bash(`echo "aws s3 ls" && grep 'kubectl delete' notes.md`, VAULT).action,
  ).toBe("allow");
});

test("text inside heredoc does not fire", () => {
  expect(
    bash(
      `git commit -m "$(cat <<'EOF'\nnever run aws sso login\nEOF\n)"`,
      VAULT,
    ).action,
  ).toBe("allow");
});

test("strictest action wins and fired lists all", () => {
  const v = bash(
    "kubectl --context p delete pod x && kubectl --context p get pods",
    VAULT,
  );
  expect(v.action).toBe("ask");
  expect(v.fired.map((r) => r.id)).toEqual(["k8s/ask-delete", "k8s/warn-get"]);
  expect(v.message).toBe("arbiter k8s/ask-delete");
  expect(bash("kubectl get pods", VAULT).action).toBe("warn");
});

test("args match in order across flag values", () => {
  expect(bash("kubectl --context prod delete pod web", VAULT).action).toBe(
    "ask",
  );
  expect(bash("kubectl logs deploy/delete-worker", VAULT).action).toBe("allow");
});

test("path rules use file_path and expand ~", () => {
  expect(
    evaluate("Edit", { file_path: "/home/u/.kube/config" }, VAULT, HOME).action,
  ).toBe("deny");
  expect(
    evaluate("Read", { file_path: "/home/u/.kube/config" }, VAULT, HOME).action,
  ).toBe("allow");
  expect(
    evaluate("Edit", { file_path: "/home/u/.kube/config2" }, VAULT, HOME)
      .action,
  ).toBe("allow");
});

test("command matchers never fire for non-Bash tools; tool regex works", () => {
  expect(evaluate("Write", { command: "aws s3 ls" }, VAULT, HOME).action).toBe(
    "allow",
  );
  expect(evaluate("mcp__prod__query", {}, VAULT, HOME).action).toBe("allow");
});

test("rewrite behaves as deny", () => {
  const rs = rules(
    "rules:\n  - id: rm/trash\n    match: { cmd: rm }\n    action: rewrite\n    to: trash\n",
  );
  expect(bash("rm a", rs).action).toBe("deny");
});

test("flags, env, wrapped_by lists, globs and regex", () => {
  const rs = rules(`
rules:
  - id: t/flags
    match: { cmd: git, flags: [--force] }
  - id: t/env
    match: { env: { AWS_PROFILE: "prod*" } }
  - id: t/wrap
    match: { cmd: terraform, wrapped_by: [sudo, op] }
  - id: t/regex
    match: { regex: "/DROP\\\\s+TABLE/i" }
`);
  expect(bash("git push --force", rs).action).toBe("deny");
  expect(bash("git push -f", rs).action).toBe("allow");
  expect(bash("AWS_PROFILE=prod-admin true", rs).action).toBe("deny");
  expect(bash("AWS_PROFILE=dev true", rs).action).toBe("allow");
  expect(bash("op run -- terraform plan", rs).action).toBe("deny");
  expect(bash('psql -c "drop   table x"', rs).action).toBe("deny");
});

test("unparsable command still meets regex rules only", () => {
  const rs = rules(
    `rules:\n  - id: t/r\n    match: { regex: "/aws/" }\n  - id: t/c\n    match: { cmd: aws }\n`,
  );
  const v = bash(`aws s3 ls 'oops`, rs);
  expect(v.fired.map((r) => r.id)).toEqual(["t/r"]);
});

test("runRuleTests passes and fails per input", () => {
  const [r] = rules(`
rules:
  - id: t/k
    match: { cmd: kubectl }
    unless: { flags: [--context] }
    tests:
      deny: ["kubectl get pods", "kubectl --context p get pods"]
      allow: ["kubectl --context p get pods"]
`);
  expect(
    runRuleTests(r, HOME).map((t) => [t.input, t.expected, t.actual, t.pass]),
  ).toEqual([
    ["kubectl get pods", "deny", "deny", true],
    ["kubectl --context p get pods", "deny", "allow", false],
    ["kubectl --context p get pods", "allow", "allow", true],
  ]);
});

test("runRuleTests uses Edit and expands ~ for path rules, ignoring tool", () => {
  const [r] = rules(
    'rules:\n  - id: t/p\n    tool: /^Write$/\n    match: { path: "~/.kube/config" }\n    tests:\n      deny: ["~/.kube/config"]\n      allow: ["~/other"]\n',
  );
  expect(runRuleTests(r, HOME).every((t) => t.pass)).toBe(true);
  expect(
    runRuleTests(
      rules("rules:\n  - id: t/n\n    match: { cmd: x }\n")[0],
      HOME,
    ),
  ).toEqual([]);
});
```

- [ ] **Step 2: Run to verify failure**

Run: `claude plugin test`
Expected: `engine.test.ts` fails to import `./engine.ts`.

- [ ] **Step 3: Implement `hooks/arbiter/engine.ts`**

```ts
// Verdict for one tool call. Spec: engine.yass.yaml
import { parse, type SubCommand } from "./shell.ts";
import type { Matcher, Outcome, Rule } from "./rules.ts";

export type Verdict = { action: Outcome; fired: Rule[]; message: string };
export type TestResult = {
  id: string;
  input: string;
  expected: Outcome;
  actual: Outcome;
  pass: boolean;
};

const REGEX = /^\/(.*)\/([imsu]*)$/s;
// ponytail: unbounded cache keyed by pattern text; fine for hundreds of rules
const compiled = new Map<string, RegExp>();

function pattern(p: string): RegExp {
  let re = compiled.get(p);
  if (!re) {
    const m = REGEX.exec(p);
    re = m
      ? new RegExp(m[1], m[2])
      : new RegExp(
          "^" +
            p
              .replace(/[.+^${}()|[\]\\]/g, "\\$&")
              .replace(/\*/g, ".*")
              .replace(/\?/g, ".") +
            "$",
          "s",
        );
    compiled.set(p, re);
  }
  return re;
}

const list = <T>(v: T | T[]): T[] => (Array.isArray(v) ? v : [v]);
const like = (p: string | string[], v: string) =>
  list(p).some((x) => pattern(x).test(v));
const toolIs = (t: string | string[], tool: string) =>
  list(t).some((p) => (REGEX.test(p) ? pattern(p).test(tool) : p === tool));

export const expandHome = (p: string, home: string) =>
  p.replace(/^~(?=\/|$)/, home);

// Each wanted element matches a later positional than the previous one.
function inOrder(want: (string | string[])[], have: string[]): boolean {
  let j = 0;
  for (const w of want) {
    while (j < have.length && !like(w, have[j])) j++;
    if (j++ >= have.length) return false;
  }
  return true;
}

function matchSub(m: Matcher, s: SubCommand): boolean {
  if (m.cmd !== undefined && !like(m.cmd, s.cmd)) return false;
  if (m.args !== undefined && !inOrder(m.args, s.args)) return false;
  if (m.flags !== undefined && !m.flags.every((f) => s.flags.includes(f)))
    return false;
  if (
    m.wrapped_by !== undefined &&
    !list(m.wrapped_by).some((w) => s.wrappers.includes(w))
  )
    return false;
  if (
    m.env !== undefined &&
    !Object.entries(m.env).every(([k, p]) => k in s.env && like(p, s.env[k]))
  )
    return false;
  if (m.regex !== undefined && !pattern(m.regex).test(s.raw)) return false;
  return true;
}

function fires(
  r: Rule,
  subs: SubCommand[],
  file: string | undefined,
  home: string,
): boolean {
  const onSub = (ms: Matcher[], s: SubCommand) =>
    ms.some((m) => m.path === undefined && matchSub(m, s));
  const onFile = (ms: Matcher[], f: string) =>
    ms.some(
      (m) =>
        m.path !== undefined &&
        list(m.path).some((p) => pattern(expandHome(p, home)).test(f)),
    );
  if (subs.some((s) => onSub(r.match, s) && !onSub(r.unless, s))) return true;
  return file !== undefined && onFile(r.match, file) && !onFile(r.unless, file);
}

function line(r: Rule): string {
  const text = [r.reason, r.hint].filter(Boolean).join(" ");
  return text ? `arbiter ${r.id}: ${text}` : `arbiter ${r.id}`;
}

export function evaluate(
  tool: string,
  input: Record<string, unknown>,
  rules: Rule[],
  home: string,
): Verdict {
  const subs =
    tool === "Bash" && typeof input.command === "string"
      ? parse(input.command)
      : [];
  const file =
    typeof input.file_path === "string" ? input.file_path : undefined;
  const fired = rules.filter(
    (r) => toolIs(r.tool, tool) && fires(r, subs, file, home),
  );
  for (const action of ["deny", "ask", "warn"] as const) {
    const hits = fired.filter(
      (r) => (r.action === "rewrite" ? "deny" : r.action) === action,
    );
    if (hits.length)
      return { action, fired, message: hits.map(line).join("\n") };
  }
  return { action: "allow", fired: [], message: "" };
}

export function runRuleTests(rule: Rule, home: string): TestResult[] {
  const usesPath = [...rule.match, ...rule.unless].some(
    (m) => m.path !== undefined,
  );
  const tool = usesPath ? "Edit" : "Bash";
  const solo = [{ ...rule, tool }];
  const out: TestResult[] = [];
  for (const [expected, inputs] of Object.entries(rule.tests) as [
    Outcome,
    string[],
  ][]) {
    for (const input of inputs) {
      const arg = usesPath
        ? { file_path: expandHome(input, home) }
        : { command: input };
      const actual = evaluate(tool, arg, solo, home).action;
      out.push({
        id: rule.id,
        input,
        expected,
        actual,
        pass: actual === expected,
      });
    }
  }
  return out;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `claude plugin test`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/arbiter/engine.ts hooks/arbiter/engine.test.ts
git commit -m "feat(arbiter): evaluate tool calls against rules"
```

---

### Task 6: Hooks module: load, guard, command, pane (`index.ts`)

Implements `index@load`, `index@guard`, `index@command`, `index@pane`.

**Files:**

- Modify: `hooks/arbiter/index.ts` (replace the Task 1 scaffold)
- Delete: `hooks/arbiter/smoke.test.ts` (keep its `node:fs` finding in mind for Task 7)
- Test: `hooks/arbiter/index.test.ts`

**Interfaces:**

- Consumes: `parseRuleFile`, `loadLayers`, `ParsedFile`, `RuleSet`, `Layer`, `Problem` (Tasks 3–4); `evaluate`, `runRuleTests`, `Verdict` (Task 5); `dump` from the vendored js-yaml.
- Produces: the mod's behavior; no exports besides `register`.

- [ ] **Step 1: Write the failing tests `hooks/arbiter/index.test.ts`**

```ts
import { expect, mock, test } from "claude-code/testing";

const HOME = "/home/u";
const USER = `${HOME}/.claude/rules/arbiter`;

type Opts = {
  files?: Record<string, string>;
  root?: string;
  answer?: string;
  toasts?: string[];
  logs?: string[];
};

// Registers every stub the mod needs, then fires session.start.
async function boot($: any, on: any, o: Opts = {}) {
  const files = o.files ?? {};
  const under = (dir: string) =>
    Object.keys(files).filter(
      (p) => p.startsWith(dir + "/") && !p.slice(dir.length + 1).includes("/"),
    );
  mock.env(on, { HOME });
  on("session.root", () => ({ value: o.root ?? "/work" }));
  on("fs.exists", ($: any, e: any) => ({ value: under(e.path).length > 0 }));
  on("fs.list", ($: any, e: any) => ({
    value: under(e.path).map((p) => ({
      name: p.slice(e.path.length + 1),
      kind: "file",
      size: 0,
      isLink: false,
    })),
  }));
  on("fs.read", ($: any, e: any) =>
    e.path in files ? { value: files[e.path] } : { deny: "ENOENT" },
  );
  on("command.register", () => ({ value: undefined }));
  on("ui.open", () => ({ value: { isPlaced: true } }));
  on("ui.toast", ($: any, e: any) => {
    o.toasts?.push(e.text);
    return { value: undefined };
  });
  on("ui.log", ($: any, e: any) => {
    o.logs?.push(e.text);
    return { value: undefined };
  });
  on("tool.call", ($: any, e: any) => {
    if (e.tool !== "AskUserQuestion") return { result: "ran" };
    return o.answer
      ? { result: { answers: { [e.questions[0].question]: o.answer } } }
      : { deny: "dismissed" };
  });
  on("session.start", () => ({ cwd: o.root ?? "/work" }));
  await $.session.start({
    surface: "terminal",
    isInteractive: true,
    cwd: o.root ?? "/work",
  });
}

const RULES = {
  [`${USER}/cloud.yaml`]: `
rules:
  - id: aws/no-sso-login
    match: { cmd: aws, args: [sso, login] }
    reason: Plaintext creds.
    hint: Use aws-vault.
    tests:
      deny: ["aws sso login"]
  - id: k8s/ask-delete
    match: { cmd: kubectl, args: [delete] }
    action: ask
  - id: k8s/warn-get
    match: { cmd: kubectl, args: [get] }
    action: warn
`,
};

test("deny answers without running the tool", async ($, on) => {
  await boot($, on, { files: RULES });
  const out = await $.tool.call({ tool: "Bash", command: "aws sso login" });
  expect(out).toEqual({
    deny: "arbiter aws/no-sso-login: Plaintext creds. Use aws-vault.",
  });
  expect(await $.tool.call({ tool: "Bash", command: "ls" })).toEqual({
    result: "ran",
  });
});

test("ask runs the tool only on Allow", async ($, on) => {
  await boot($, on, { files: RULES, answer: "Allow" });
  expect(
    await $.tool.call({ tool: "Bash", command: "kubectl delete pod x" }),
  ).toEqual({ result: "ran" });
});

test("ask refused denies", async ($, on) => {
  await boot($, on, { files: RULES, answer: "Refuse" });
  expect(
    await $.tool.call({ tool: "Bash", command: "kubectl delete pod x" }),
  ).toEqual({ deny: "arbiter k8s/ask-delete" });
});

test("ask with nobody to answer denies", async ($, on) => {
  await boot($, on, { files: RULES });
  expect(
    await $.tool.call({ tool: "Bash", command: "kubectl delete pod x" }),
  ).toEqual({ deny: "arbiter k8s/ask-delete" });
});

test("warn logs and runs", async ($, on) => {
  const logs: string[] = [];
  await boot($, on, { files: RULES, logs });
  expect(
    await $.tool.call({ tool: "Bash", command: "kubectl get pods" }),
  ).toEqual({ result: "ran" });
  expect(logs).toEqual(["arbiter k8s/warn-get"]);
});

test("broken file is skipped and reported", async ($, on) => {
  const toasts: string[] = [];
  await boot($, on, {
    toasts,
    files: { ...RULES, [`${USER}/broken.yaml`]: "rules:\n  - id: x/y\n" },
  });
  expect(
    (await $.tool.call({ tool: "Bash", command: "aws sso login" })).deny,
  ).toBeDefined();
  expect(toasts).toEqual([
    "arbiter: 1 rule file skipped. Run /arbiter for details.",
  ]);
});

test("project layer skipped when it is the user layer", async ($, on) => {
  const toasts: string[] = [];
  await boot($, on, { files: RULES, root: HOME, toasts });
  expect(toasts).toEqual([]);
  const answer = await $.command.run({ command: "arbiter", args: "reload" });
  expect(answer.text).toBe(
    "rules: plugin 0, user 3, project 0; disabled 0; errors 0",
  );
});

test("/arbiter check", async ($, on) => {
  await boot($, on, { files: RULES });
  const answer = await $.command.run({
    command: "arbiter",
    args: "check aws sso login",
  });
  expect(answer.text).toBe(
    `DENY\n  aws/no-sso-login  (user: ${USER}/cloud.yaml)\n    reason: Plaintext creds.\n    hint: Use aws-vault.`,
  );
  expect(
    (await $.command.run({ command: "arbiter", args: "check ls" })).text,
  ).toBe("ALLOW  no rule fired");
});

test("/arbiter list and list <id>", async ($, on) => {
  await boot($, on, { files: RULES });
  expect(
    (await $.command.run({ command: "arbiter", args: "list k8s" })).text,
  ).toBe("k8s/ask-delete  ask  user\nk8s/warn-get  warn  user");
  expect(
    (await $.command.run({ command: "arbiter", args: "list aws/no-sso-login" }))
      .text,
  ).toContain("id: aws/no-sso-login");
});

test("/arbiter test", async ($, on) => {
  await boot($, on, { files: RULES });
  expect((await $.command.run({ command: "arbiter", args: "test" })).text).toBe(
    "1/1 rule tests passed",
  );
});

test("/arbiter with unknown subcommand prints usage", async ($, on) => {
  await boot($, on, { files: RULES });
  expect(
    (await $.command.run({ command: "arbiter", args: "bogus" })).text,
  ).toContain("/arbiter check <command>");
});

test("pane shows counts, errors, and verdicts", async ($, on) => {
  await boot($, on, {
    files: { ...RULES, [`${USER}/broken.yaml`]: "rules: [" },
  });
  await $.tool.call({ tool: "Bash", command: "aws sso login" });
  const ui = await $.ui.mount({
    plugin: "agent-tools",
    component: "Pane",
    requestId: "arbiter",
    surface: "terminal",
    viewport: { columns: 100, rows: 30 },
    props: {
      title: "arbiter",
      isFocused: true,
      bodyColumns: 80,
      placement: "inline",
      scroll: { offset: 0, bodyRows: 20 },
      view: {},
    },
  });
  expect(
    await ui.find({
      type: "Text",
      text: "rules  plugin 0 · user 3 · project 0 · disabled 0",
    }),
  ).toBeDefined();
  expect(await ui.find({ type: "Text", text: /broken\.yaml/ })).toBeDefined();
  expect(
    await ui.find({
      type: "Text",
      text: /DENY  aws\/no-sso-login  aws sso login$/,
    }),
  ).toBeDefined();
});
```

- [ ] **Step 2: Run to verify failure**

Run: `claude plugin test`
Expected: `index.test.ts` tests fail (scaffold has no guard).

- [ ] **Step 3: Replace `hooks/arbiter/index.ts`**

Use the `$` type name confirmed in Task 1 Step 6 in place of `EngineInterface` if it differs.

```ts
// arbiter hooks module: the only file that touches $. Spec: index.yass.yaml
import type { EngineInterface } from "claude-code";
import { dump } from "./vendor/js-yaml.mjs";
import { evaluate, runRuleTests, type Verdict } from "./engine.ts";
import {
  loadLayers,
  parseRuleFile,
  type Layer,
  type ParsedFile,
  type Problem,
  type RuleSet,
} from "./rules.ts";

type Hit = {
  at: number;
  tool: string;
  action: string;
  ids: string[];
  target: string;
};

let rules: RuleSet = { rules: [], disabled: [], errors: [], warnings: [] };
let home = "";
const recent: Hit[] = [];

const USAGE = [
  "/arbiter                     open the pane",
  "/arbiter check <command>     dry-run a Bash command",
  "/arbiter list [filter|id]    list rules, or print one rule",
  "/arbiter test                run every rule's inline tests",
  "/arbiter reload              re-read rule files",
].join("\n");

async function load($: EngineInterface) {
  home = (await $.env.get("HOME")) ?? "";
  const user = `${home}/.claude/rules/arbiter`;
  const project = `${await $.session.root()}/.claude/rules/arbiter`;
  const dirs: [Layer, string][] = [
    ["plugin", `${$.plugin.root}/rules`],
    ["user", user],
  ];
  if (project !== user) dirs.push(["project", project]);
  const files: ParsedFile[] = [];
  for (const [layer, dir] of dirs) {
    if (!(await $.fs.exists(dir))) continue;
    for (const entry of await $.fs.list(dir)) {
      if (entry.kind !== "file" || !entry.name.endsWith(".yaml")) continue;
      const path = `${dir}/${entry.name}`;
      try {
        files.push(parseRuleFile(await $.fs.read(path), path, layer));
      } catch (err) {
        files.push({
          path,
          layer,
          rules: [],
          disable: [],
          errors: [{ path, message: `cannot read: ${String(err)}` }],
        });
      }
    }
  }
  rules = loadLayers(files);
  const skipped = new Set(rules.errors.map((e) => e.path)).size;
  if (skipped)
    $.ui.toast(
      `arbiter: ${skipped} rule file${skipped === 1 ? "" : "s"} skipped. Run /arbiter for details.`,
    );
  $.ui.invalidate("ui.render");
}

function remember(e: Record<string, unknown>, v: Verdict) {
  recent.unshift({
    at: Date.now(),
    tool: String(e.tool),
    action: v.action,
    ids: v.fired.map((r) => r.id),
    target: String(e.command ?? e.file_path ?? ""),
  });
  recent.length = Math.min(recent.length, 100);
}

function describe(p: Problem): string {
  return `${p.path}${p.line ? `:${p.line}` : ""}: ${p.id ? `${p.id}: ` : ""}${p.message}`;
}

function summary(): string {
  const n = (l: Layer) => rules.rules.filter((r) => r.layer === l).length;
  return `rules: plugin ${n("plugin")}, user ${n("user")}, project ${n("project")}; disabled ${rules.disabled.length}; errors ${rules.errors.length}`;
}

function check(command: string): string {
  const v = evaluate("Bash", { command }, rules.rules, home);
  if (v.action === "allow") return "ALLOW  no rule fired";
  const lines = [v.action.toUpperCase()];
  for (const r of v.fired) {
    lines.push(`  ${r.id}  (${r.layer}: ${r.path})`);
    if (r.reason) lines.push(`    reason: ${r.reason}`);
    if (r.hint) lines.push(`    hint: ${r.hint}`);
  }
  return lines.join("\n");
}

function list(filter: string): string {
  const exact = rules.rules.find((r) => r.id === filter);
  if (exact) return dump(exact.source).trimEnd();
  const rows = [
    ...rules.rules.map((r) => `${r.id}  ${r.action}  ${r.layer}`),
    ...rules.disabled.map(
      (d) =>
        `${d.rule.id}  ${d.rule.action}  ${d.rule.layer}  (disabled by ${d.by})`,
    ),
  ].filter((row) => row.split("  ")[0].includes(filter));
  return rows.length ? rows.join("\n") : "no rules match";
}

function testAll(): string {
  const results = rules.rules.flatMap((r) => runRuleTests(r, home));
  const failed = results.filter((t) => !t.pass);
  const head = `${results.length - failed.length}/${results.length} rule tests passed`;
  return [
    head,
    ...failed.map(
      (t) =>
        `FAIL ${t.id}: ${JSON.stringify(t.input)} expected ${t.expected}, got ${t.actual}`,
    ),
  ].join("\n");
}

async function guard($: EngineInterface, e: any, next: any) {
  const v = evaluate(e.tool, e, rules.rules, home);
  if (v.action === "allow") return next(e);
  remember(e, v);
  $.ui.invalidate("ui.render");
  if (v.action === "deny") return { deny: v.message };
  if (v.action === "warn") {
    $.ui.log(v.message);
    return next(e);
  }
  let answer = "Refuse";
  try {
    answer = await $.ui.ask(v.message, ["Allow", "Refuse"]);
  } catch {
    // dismissed, or claude -p with nobody to ask
  }
  return answer === "Allow" ? next(e) : { deny: v.message };
}

async function command($: EngineInterface, e: any) {
  const args = String(e.args ?? "").trim();
  const sub = args.split(/\s+/)[0];
  const rest = args.slice(sub.length).trim();
  if (!sub) {
    await $.ui.open({ id: "arbiter", title: "arbiter", closeOnEscape: true });
    return {};
  }
  if (sub === "check" && rest) return { text: check(rest) };
  if (sub === "list") return { text: list(rest) };
  if (sub === "test") return { text: testAll() };
  if (sub === "reload") {
    await load($);
    return { text: summary() };
  }
  return { text: USAGE };
}

async function pane($: EngineInterface, e: any) {
  const { Box, Text } = $.ui.resolve(e);
  const n = (l: Layer) => rules.rules.filter((r) => r.layer === l).length;
  const problems = [
    ...rules.errors.map((p) =>
      Text({ color: "red", wrap: "wrap", children: [describe(p)] }),
    ),
    ...rules.warnings.map((p) =>
      Text({ color: "yellow", wrap: "wrap", children: [describe(p)] }),
    ),
  ];
  const hits = recent.length
    ? recent.map((h) =>
        Text({
          wrap: "truncate-end",
          children: [
            `${new Date(h.at).toLocaleTimeString()}  ${h.action.toUpperCase()}  ${h.ids.join(",")}  ${h.target}`,
          ],
        }),
      )
    : [Text({ dimColor: true, children: ["no verdicts yet"] })];
  return Box({
    flexDirection: "column",
    children: [
      Text({
        bold: true,
        children: [
          `rules  plugin ${n("plugin")} · user ${n("user")} · project ${n("project")} · disabled ${rules.disabled.length}`,
        ],
      }),
      ...problems,
      Text({ children: [" "] }),
      ...hits,
    ],
  });
}

export function register(on) {
  on("session.start", async ($, e, next) => {
    await $.command.register({
      name: "arbiter",
      description: "Show and test arbiter rules",
      argumentHint: "[check <command> | list [filter|id] | test | reload]",
      immediate: true,
    });
    await load($);
    return next(e);
  });

  on("tool.call", async ($, e, next) => guard($, e, next)).catch(
    async ($, e, next) => ({
      deny: `arbiter failed (${next.error.kind}): ${next.error.message}`,
    }),
  );

  on("command.run", { command: "arbiter" }, async ($, e) => command($, e));

  on("ui.render", { component: "Pane", requestId: "arbiter" }, async ($, e) =>
    pane($, e),
  );
}
```

- [ ] **Step 4: Delete the smoke test, validate, and run**

```bash
git rm hooks/arbiter/smoke.test.ts
claude plugin validate .
claude plugin test
```

Expected: validate lists `hooks: session.start, tool.call, command.run{command=arbiter}, ui.render{component=Pane,requestId=arbiter}` and passes; all tests pass. If the AskUserQuestion stub shape is wrong (`ask runs the tool only on Allow` fails), read the `the engine reported:` block and adjust the stub to what `$.ui.ask` sends, per `.claude-plugin/types/claude-code/index.d.ts`.

- [ ] **Step 5: Manual fail-closed check**

The `.catch` path has no automated test. Verify once by hand:

```bash
claude --plugin-dir .
```

Temporarily add `if (e.command === 'boom') throw new Error('boom')` as the first line of `guard`, save (hot reload), ask Claude to run `boom`, and confirm Claude sees `arbiter failed (throw): boom`. Remove the line.

- [ ] **Step 6: Commit**

```bash
git add hooks/arbiter/index.ts hooks/arbiter/index.test.ts
git commit -m "feat(arbiter): guard tool calls, /arbiter command, and pane"
```

---

### Task 7: Shipped `general` pack and the all-rules test

Implements the shipped layer and the "every rule's inline tests run in CI" requirement.

**Files:**

- Create: `rules/general.yaml`
- Test: `hooks/arbiter/packs.test.ts`

**Interfaces:**

- Consumes: `parseRuleFile` (Task 3), `runRuleTests` (Task 5).
- Produces: plugin-layer rules `general/no-force-push`, `general/no-rm-rf-root`, `general/ask-reset-hard`.

- [ ] **Step 1: Write `rules/general.yaml`**

```yaml
# Shipped with arbiter. Disable any rule from a higher layer:
#   disable: [general/no-force-push]
rules:
  - id: general/no-force-push
    match:
      - { cmd: git, args: [push], flags: [--force] }
      - { cmd: git, args: [push], flags: [-f] }
    reason: Force-pushing rewrites shared history.
    hint: Use `git push --force-with-lease` instead.
    tests:
      deny:
        [
          "git push --force",
          "git push -f origin main",
          "git push origin main --force",
        ]
      allow:
        [
          "git push",
          "git push --force-with-lease",
          'git commit -m "no --force here"',
        ]

  - id: general/no-rm-rf-root
    match: { cmd: rm, args: ['/^(\/|~|\$HOME|\$\{HOME\})\/?\*?$/'] }
    reason: This deletes the root or home directory.
    hint: Name the specific path to delete.
    tests:
      deny:
        [
          "rm -rf /",
          "sudo rm -rf ~",
          "rm -rf $HOME/",
          "rm -rf /*",
          "rm -rf ${HOME}",
        ]
      allow: ["rm -rf ./build", "rm -rf /tmp/x", "rm -rf ~/scratch"]

  - id: general/ask-reset-hard
    match: { cmd: git, args: [reset], flags: [--hard] }
    action: ask
    reason: git reset --hard discards uncommitted work.
    tests:
      ask: ["git reset --hard HEAD~1"]
      allow: ["git reset --soft HEAD~1", "git reset HEAD file"]
```

- [ ] **Step 2: Write `hooks/arbiter/packs.test.ts`**

If Task 1 found that test files can use `node:fs`, use this version:

```ts
import { expect, test } from "claude-code/testing";
import { readdirSync, readFileSync } from "node:fs";
import { runRuleTests } from "./engine.ts";
import { parseRuleFile } from "./rules.ts";

// Rule files whose inline tests must pass in CI.
const FILES = [
  ...readdirSync("rules")
    .filter((f) => f.endsWith(".yaml"))
    .map((f) => `rules/${f}`),
  "docs/arbiter/examples/claude-md.yaml",
];

for (const path of FILES) {
  test(`rule file ${path} is valid and its inline tests pass`, () => {
    const parsed = parseRuleFile(readFileSync(path, "utf8"), path, "plugin");
    expect(parsed.errors).toEqual([]);
    const failed = parsed.rules
      .flatMap((r) => runRuleTests(r, "/home/u"))
      .filter((t) => !t.pass);
    expect(failed).toEqual([]);
  });
}
```

**Fallback** if `node:fs` is unavailable in tests: replace `packs.test.ts` with `script/arbiter-test`, which drives the real mod:

```bash
#!/usr/bin/env bash
# Runs every loaded rule's inline tests through the real mod.
set -euo pipefail
out=$(claude --plugin-dir "$(dirname "$0")/.." -p "/arbiter test")
echo "$out"
grep -q "^agent-tools: \([0-9]*\)/\1 rule tests passed$" <<<"$out"
```

`chmod +x script/arbiter-test`. In this mode the example file is only covered when copied to `~/.claude/rules/arbiter/`.

- [ ] **Step 3: Run**

Run: `claude plugin test` (or `script/arbiter-test`)
Expected: PASS for `rules/general.yaml` and `docs/arbiter/examples/claude-md.yaml`. If an example-file test fails, decide from `shell.yass.yaml`/`engine.yass.yaml` whether the rule or the code is wrong; fix the rule YAML if the spec agrees with the code.

- [ ] **Step 4: Commit**

```bash
git add rules/general.yaml hooks/arbiter/packs.test.ts
git commit -m "feat(arbiter): ship general rule pack and test all packs"
```

---

### Task 8: Docs and end-to-end check

**Files:**

- Modify: `README.md` (add an arbiter section after the skills section, outside the generated markers)
- Modify: `docs/arbiter/design.md` (shipped pack, pipeline limitation)
- Modify: `docs/arbiter/decisions.md` (append one decision)
- Modify: `.github/workflows/*` only if a CI workflow runs tests; otherwise skip.

**Interfaces:**

- Consumes: everything above.
- Produces: user-facing docs.

- [ ] **Step 1: Add to `README.md`**

````markdown
## arbiter

A mod that enforces YAML rules at every tool call. Rules load from three layers, lowest to highest:

| Layer   | Location                              |
| ------- | ------------------------------------- |
| plugin  | `rules/*.yaml` (ships `general/*`)    |
| user    | `~/.claude/rules/arbiter/*.yaml`      |
| project | `<repo>/.claude/rules/arbiter/*.yaml` |

```yaml
disable: [general/ask-reset-hard]
rules:
  - id: aws/requires-vault
    match: { cmd: aws }
    unless: { wrapped_by: aws-vault }
    hint: Run `aws-vault exec <profile> -- aws ...`.
    tests:
      deny: ["aws s3 ls"]
      allow: ["aws-vault exec dev -- aws s3 ls"]
```

Commands: `/arbiter` (pane), `/arbiter check <command>`, `/arbiter list [filter|id]`, `/arbiter test`, `/arbiter reload`.

Requires Claude Code ≥ 2.1.287. Spec: `hooks/arbiter/*.yass.yaml`. Design: `docs/arbiter/`. Not a security boundary: it catches habits, not an agent trying to evade it.
````

- [ ] **Step 2: Update `docs/arbiter/design.md`**

Replace the "Shipped `general` pack (initial)" section body with:

```markdown
`general/no-force-push` (`git push --force`/`-f`, hint `--force-with-lease`),
`general/no-rm-rf-root` (`rm` of `/`, `~`, `$HOME`), `general/ask-reset-hard` (ask before
`git reset --hard`). Kept small on purpose.
```

In the rule-schema example, change `disable: [general/no-curl-pipe-sh]` to `disable: [general/ask-reset-hard]`.

- [ ] **Step 3: Append to `docs/arbiter/decisions.md`**

```markdown
---

## Rules see one simple command at a time

**Status:** accepted · 2026-10-04

**Context.** `curl … | sh` was planned for the shipped pack, but the parser splits pipelines
into separate sub-commands and `regex` matches each sub-command's own `raw`.

**Decision.** v1 rules match single sub-commands. Pipeline-aware matching (e.g. a `piped_to`
field) waits for a real rule that needs it. `general/no-curl-pipe-sh` was dropped.

**Consequences.** Rules about what a command's output is fed into can't be written yet.
```

- [ ] **Step 4: End-to-end check in a real session**

```bash
mkdir -p ~/.claude/rules/arbiter
cp docs/arbiter/examples/claude-md.yaml ~/.claude/rules/arbiter/claude-md.yaml
claude --plugin-dir .
```

In the session, run and confirm:

- `/arbiter reload` → `rules: plugin 3, user 10, project 0; disabled 0; errors 0`
- `/arbiter test` → `N/N rule tests passed`
- `/arbiter check aws s3 ls --profile prod` → `DENY` with `aws/requires-vault`
- Ask Claude: "run `aws sso login`". Claude gets the deny text and does not run it.
- `/arbiter` opens the pane showing that verdict.

Only copy the example file if the user wants those rules active now; otherwise remove it afterwards.

- [ ] **Step 5: Run all checks and commit**

```bash
claude plugin validate .
claude plugin test
(cd hooks/arbiter && yass validate && yass lint)
pre-commit run --all-files
git add README.md docs/arbiter/design.md docs/arbiter/decisions.md
git commit -m "docs(arbiter): usage, shipped pack, pipeline limitation"
```
