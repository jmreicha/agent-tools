// Bash command string -> simple commands. Spec: shell.yass.yaml
export type SubCommand = {
  raw: string;
  cmd: string;
  args: string[];
  flags: string[];
  env: Record<string, string>;
  wrappers: string[];
  words: string[];
  pipe: number;
  stage: number;
  redirects: string[];
};

// Pipeline ids, unique within one parse() call.
let pipes = 0;

// What one simple command's words yield besides the words themselves.
type Extras = { redirects: string[]; herestrings: string[]; outputs: SubCommand[] };

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
  nohup: flagsThen([]),
  doas: flagsThen(["-u", "-C"]),
  exec: flagsThen(["-a"]),
  watch: flagsThen(["-n", "--interval"]),
  // `command -v aws` only looks the name up; nothing runs.
  command: (rest) => {
    const n = flagsThen([])(rest)!;
    return rest.slice(0, n).some((f) => f === "-v" || f === "-V") ? null : n;
  },
  builtin: flagsThen([]),
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
  pipes = 0;
  try {
    return new Lexer(command).list(false, []);
  } catch {
    return [
      {
        raw: command,
        cmd: "",
        args: [],
        flags: [],
        env: {},
        wrappers: [],
        words: [],
        pipe: 0,
        stage: 0,
        redirects: [],
      },
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
    let pipe = pipes++;
    let stage = 0;
    for (;;) {
      this.blanks();
      const start = this.i;
      const words: string[] = [];
      const x: Extras = { redirects: [], herestrings: [], outputs: [] };
      const fed = out.length;
      this.words(words, out, wrappers, x);
      feed(out.slice(fed), pipe, stage);
      out.push(...x.outputs);
      const built = build(words, this.s.slice(start, this.i).trim(), wrappers);
      // pipe -1 marks this simple command's own subs; nested scripts are already numbered.
      const own = built.filter((b) => b.pipe === -1);
      for (const b of own) Object.assign(b, { pipe, stage });
      const last = own.at(-1);
      last?.redirects.push(...x.redirects);
      out.push(...built);
      if (last && SHELLS.has(last.cmd))
        for (const h of x.herestrings) out.push(...new Lexer(h).list(false, wrappers));
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
      let piped = false;
      if (c === "&" || c === "|") {
        const next = this.s[this.i];
        // `|` and `|&` continue a pipeline; `||`, `&&`, and `&` end it.
        piped = c === "|" && next !== "|";
        if (next === c || (c === "|" && next === "&")) this.i++;
      }
      if (piped) stage++;
      else {
        pipe = pipes++;
        stage = 0;
      }
    }
  }

  private blanks() {
    while (this.i < this.s.length) {
      if (this.s[this.i] === " " || this.s[this.i] === "\t") this.i++;
      else if (this.s.startsWith("\\\n", this.i)) this.i += 2;
      else return;
    }
  }

  private words(
    words: string[],
    out: SubCommand[],
    wrappers: string[],
    x: Extras,
  ) {
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
        this.redirect(out, wrappers, x);
      } else if (c === "<" || c === ">") this.redirect(out, wrappers, x);
      else if (c === "#")
        while (this.i < this.s.length && this.s[this.i] !== "\n") this.i++;
      else {
        const w = this.word(out, wrappers);
        const next = this.s[this.i];
        if (/^\d+$/.test(w) && (next === "<" || next === ">"))
          this.redirect(out, wrappers, x);
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

  private redirect(out: SubCommand[], wrappers: string[], x: Extras) {
    REDIRECT.lastIndex = this.i;
    const op = REDIRECT.exec(this.s)![0];
    this.i += op.length;
    if ((op === "<" || op === ">") && this.s[this.i] === "(") {
      this.i++;
      // <(…) feeds the command; >(…) is fed by it, so it stays its own pipeline.
      (op === "<" ? out : x.outputs).push(...this.list(true, wrappers));
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
    else if (op === "<<<") x.herestrings.push(target);
    else x.redirects.push(target);
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
  // A substitution in command position isn't a path; keep it whole.
  const cmd = /[$`]/.test(words[i]) ? words[i] : words[i].split("/").pop()!;
  const rest = words.slice(i + 1);
  const n = WRAPPERS[cmd]?.(rest) ?? null;
  if (n !== null) {
    const inner = rest.slice(n);
    // watch runs a single quoted argument through sh -c.
    const nested =
      cmd === "watch" && inner.length === 1 && /\s/.test(inner[0])
        ? new Lexer(inner[0]).list(false, [...wrappers, cmd])
        : build(inner, raw, [...wrappers, cmd]);
    return [make(raw, cmd, rest.slice(0, n), env, wrappers), ...nested];
  }
  const sub = make(raw, cmd, rest, env, wrappers);
  if (cmd === "find") return [sub, ...findExec(rest, raw, wrappers)];
  const script = SHELLS.has(cmd)
    ? cScript(rest)
    : cmd === "eval"
      ? rest.join(" ")
      : null;
  return script === null
    ? [sub]
    : [sub, ...new Lexer(script).list(false, wrappers)];
}

const EXEC = new Set(["-exec", "-execdir", "-ok", "-okdir"]);

// Commands find runs: the words after -exec up to `;` or `+`.
function findExec(rest: string[], raw: string, wrappers: string[]): SubCommand[] {
  const out: SubCommand[] = [];
  for (let i = 0; i < rest.length; i++) {
    if (!EXEC.has(rest[i])) continue;
    let j = i + 1;
    while (j < rest.length && rest[j] !== ";" && rest[j] !== "+") j++;
    out.push(...build(rest.slice(i + 1, j), raw, [...wrappers, "find"]));
    i = j;
  }
  return out;
}

// Substitution output feeds the command it sits in: move those subs into its
// pipeline between the previous stage and its own, keeping their order.
function feed(subs: SubCommand[], pipe: number, stage: number) {
  const max = new Map<number, number>();
  for (const s of subs) max.set(s.pipe, Math.max(max.get(s.pipe) ?? 0, s.stage));
  for (const s of subs)
    Object.assign(s, {
      stage: stage - 1 + (s.stage + 1) / (max.get(s.pipe)! + 2),
      pipe,
    });
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
  return { raw, cmd, args, flags, env, wrappers, words, pipe: -1, stage: 0, redirects: [] };
}

// The script of `bash -c script`, or null.
function cScript(rest: string[]): string | null {
  const c = rest.findIndex((w) => /^-[a-zA-Z]*c[a-zA-Z]*$/.test(w));
  if (c < 0) return null;
  return rest.slice(c + 1).find((w) => !w.startsWith("-")) ?? null;
}
