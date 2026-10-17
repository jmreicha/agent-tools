// Verdict for one tool call. Spec: engine.yass.yaml
import { parse, type SubCommand } from "./shell.ts";
import type { Matcher, Outcome, Rule, Step } from "./rules.ts";

export type Verdict = { action: Outcome; fired: Rule[]; message: string };
// For rewrite tests, expected and actual are commands.
export type TestResult = {
  id: string;
  input: string;
  expected: string;
  actual: string;
  pass: boolean;
};
export type Rewritten = { command: string } | { error: string };
// A tool call that ran: its tool, its callKey, and the repeat rules it matched.
export type Call = { tool: string; key: string; matched: string[] };

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

function matchSub(m: Matcher, s: SubCommand, subs: SubCommand[]): boolean {
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
  if (
    m.piped_to !== undefined &&
    !subs.some(
      (t) =>
        t.pipe === s.pipe && t.stage > s.stage && matchSub(m.piped_to!, t, subs),
    )
  )
    return false;
  return true;
}

// A redirect target or argument as a path: home spelled out, relative made ./ so */x globs match.
const target = (t: string, home: string) => {
  const p = expandHome(t.replace(/^\$(\{HOME\}|HOME)(?=\/|$)/, "~"), home);
  return p.startsWith("/") ? p : `./${p}`;
};

const onSub = (ms: Matcher[], s: SubCommand, subs: SubCommand[]) =>
  ms.some((m) => m.path === undefined && matchSub(m, s, subs));
const firesOn = (r: Rule, s: SubCommand, subs: SubCommand[]) =>
  onSub(r.match, s, subs) && !onSub(r.unless, s, subs);

function fires(
  r: Rule,
  subs: SubCommand[],
  file: string | undefined,
  home: string,
): boolean {
  const onFile = (ms: Matcher[], f: string) =>
    ms.some(
      (m) =>
        m.path !== undefined &&
        list(m.path).some((p) => pattern(expandHome(p, home)).test(f)),
    );
  if (!r.match.length) return true;
  if (subs.some((s) => firesOn(r, s, subs))) return true;
  const files = [
    ...(file === undefined ? [] : [file]),
    ...subs.flatMap((s) =>
      [...s.redirects, ...s.args].map((t) => target(t, home)),
    ),
  ];
  return files.some((f) => onFile(r.match, f) && !onFile(r.unless, f));
}

function line(r: Rule, n?: number): string {
  const text = [r.description, r.hint].filter(Boolean).join(" ");
  const seen = n ? ` (${n} matching calls in the last ${r.repeat!.within})` : "";
  return (text ? `arbiter ${r.id}: ${text}` : `arbiter ${r.id}`) + seen;
}

// What a repeat rule's `same` compares: the Bash command, or the file path.
export function callKey(tool: string, input: Record<string, unknown>): string {
  if (tool === "Bash" && typeof input.command === "string")
    return input.command.trim();
  return typeof input.file_path === "string" ? input.file_path : "";
}

// Rules whose tool, match, and unless hold for the call, ignoring repeat counts.
function matching(
  tool: string,
  input: Record<string, unknown>,
  rules: Rule[],
  home: string,
): Rule[] {
  const subs =
    tool === "Bash" && typeof input.command === "string"
      ? parse(input.command)
      : [];
  const file =
    typeof input.file_path === "string" ? input.file_path : undefined;
  return rules.filter((r) => toolIs(r.tool, tool) && fires(r, subs, file, home));
}

// Ids of repeat rules the call matches, for the caller to record in its history.
export function matchedRepeat(
  tool: string,
  input: Record<string, unknown>,
  rules: Rule[],
  home: string,
): string[] {
  return matching(tool, input, rules.filter((r) => r.repeat), home).map(
    (r) => r.id,
  );
}

// This call plus earlier matching calls in the window, back to the latest reset.
function repeats(r: Rule, past: Call[], key: string): number {
  const rep = r.repeat!;
  let n = 1;
  for (const p of past.slice(-(rep.within - 1)).reverse()) {
    if (rep.reset_on !== undefined && toolIs(rep.reset_on, p.tool)) break;
    if (p.matched.includes(r.id) && (!rep.same || p.key === key)) n++;
  }
  return n;
}

export function evaluate(
  tool: string,
  input: Record<string, unknown>,
  rules: Rule[],
  home: string,
  past: Call[] = [],
): Verdict {
  const key = callKey(tool, input);
  const counts = new Map<string, number>();
  const fired = matching(tool, input, rules, home)
    .filter((r) => {
      if (!r.repeat) return true;
      const n = repeats(r, past, key);
      counts.set(r.id, n);
      return n >= r.repeat.count;
    })
    .sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  for (const action of ["deny", "rewrite", "ask", "warn"] as const) {
    const hits = fired.filter((r) => r.action === action);
    if (hits.length)
      return {
        action,
        fired,
        message: hits.map((r) => line(r, counts.get(r.id))).join("\n"),
      };
  }
  return { action: "allow", fired: [], message: "" };
}

// A test step as a tool call: { tool } bare, else an input the way runRuleTests reads one.
function stepCall(
  step: Step,
  rule: Rule,
  usesPath: boolean,
  home: string,
): [string, Record<string, unknown>] {
  if (typeof step !== "string") return [step.tool, {}];
  if (!rule.match.length) return [step, {}];
  return usesPath
    ? ["Edit", { file_path: expandHome(step, home) }]
    : ["Bash", { command: step }];
}

// Run a sequence through a fresh history; the outcome is the last call's.
function runSequence(seq: Step[], rule: Rule, rs: Rule[], usesPath: boolean, home: string): Outcome {
  const past: Call[] = [];
  let action: Outcome = "allow";
  for (const step of seq) {
    const [tool, input] = stepCall(step, rule, usesPath, home);
    action = evaluate(tool, input, rs, home, past).action;
    past.push({
      tool,
      key: callKey(tool, input),
      matched: matchedRepeat(tool, input, rs, home),
    });
  }
  return action;
}

export function runRuleTests(rule: Rule, home: string): TestResult[] {
  const usesPath = [...rule.match, ...rule.unless].some(
    (m) => m.path !== undefined,
  );
  const tool = usesPath ? "Edit" : "Bash";
  const solo = [{ ...rule, tool }];
  const out: TestResult[] = [];
  if (rule.repeat) {
    const rs = rule.match.length ? solo : [rule];
    for (const [expected, seqs] of Object.entries(rule.tests) as [
      Outcome,
      Step[][],
    ][]) {
      if (expected === "rewrite") continue;
      for (const seq of seqs) {
        const actual = runSequence(seq, rule, rs, usesPath, home);
        const input = seq
          .map((s) => (typeof s === "string" ? s : `{ tool: ${s.tool} }`))
          .join(" -> ");
        out.push({ id: rule.id, input, expected, actual, pass: actual === expected });
      }
    }
    return out;
  }
  for (const [input, expected] of Object.entries(rule.tests.rewrite ?? {})) {
    const v = evaluate(tool, { command: input }, solo, home);
    const r = v.action === "rewrite" ? rewrite(input, v, home) : null;
    const actual = !r ? v.action : "error" in r ? r.error : r.command;
    out.push({ id: rule.id, input, expected, actual, pass: actual === expected });
  }
  for (const [expected, inputs] of Object.entries(rule.tests) as [
    Outcome,
    string[],
  ][]) {
    if (expected === "rewrite") continue;
    for (const input of inputs) {
      if (!rule.match.length) {
        // Tool-only rule: the input is a tool name.
        const actual = evaluate(input, {}, [rule], home).action;
        out.push({ id: rule.id, input, expected, actual, pass: actual === expected });
        continue;
      }
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

type Edit = { from: number; to: number; text: string; id: string };

const SAFE = /^[\w@%+=:,./-]+$/;
const quote = (v: string) => (SAFE.test(v) ? v : `'${v.replace(/'/g, `'\\''`)}'`);

// Remove [from, to) with the blanks after it, or before it at the end of a command.
function cut(cmd: string, from: number, to: number, id: string): Edit {
  let b = to;
  while (cmd[b] === " " || cmd[b] === "\t") b++;
  if (b === to) while (from > 0 && (cmd[from - 1] === " " || cmd[from - 1] === "\t")) from--;
  return { from, to: b, text: "", id };
}

// One rule's edits to one sub-command, spliced by span into the original text.
function editsFor(r: Rule, s: SubCommand, cmd: string): Edit[] | { error: string } {
  const to = r.to!;
  const sp = s.spans!;
  const valueAt = new Map<string, number>(); // flag -> index of its separate value word
  const valueOf = (alt: string): string | undefined => {
    if (alt.startsWith("-")) {
      for (let i = 0; i < s.words.length; i++) {
        if (s.words[i] === "--") break;
        if (s.words[i].startsWith(alt + "=")) return s.words[i].slice(alt.length + 1);
        if (s.words[i] === alt && i + 1 < s.words.length) {
          valueAt.set(alt, i + 1);
          return s.words[i + 1];
        }
      }
      return undefined;
    }
    if (/^[A-Z_][A-Z0-9_]*$/.test(alt)) return s.env[alt];
    return alt;
  };
  let missing = "";
  const fill = (tpl: string) =>
    tpl.replace(/\{([^}]*)\}/g, (whole, alts: string) => {
      for (const a of alts.split("|")) {
        const v = valueOf(a);
        if (v !== undefined) return /^[A-Z_-]/.test(a) ? quote(v) : v;
      }
      missing ||= whole;
      return whole;
    });
  const out: Edit[] = [];
  const [c0, c1] = sp.cmd;
  if (to.cmd !== undefined) out.push({ from: c0, to: c1, text: fill(to.cmd), id: r.id });
  if (to.prefix !== undefined) out.push({ from: c0, to: c0, text: `${fill(to.prefix)} `, id: r.id });
  if (missing) return { error: `${r.id}: nothing fills ${missing}` };
  for (const [flag, repl] of Object.entries(to.flags ?? {})) {
    for (let i = 0; i < s.words.length; i++) {
      const w = s.words[i];
      if (w === "--") break;
      if (w !== flag && !w.startsWith(flag + "=")) continue;
      const [w0, w1] = sp.words[i];
      if (cmd.slice(w0, w0 + flag.length) !== flag)
        return { error: "the command is too complex to rewrite safely" };
      if (repl !== null) out.push({ from: w0, to: w0 + flag.length, text: repl, id: r.id });
      else {
        const v = w === flag ? valueAt.get(flag) : undefined;
        out.push(cut(cmd, w0, v === i + 1 ? sp.words[v][1] : w1, r.id));
        if (v === i + 1) i++;
      }
    }
  }
  for (const name of Object.keys(to.env ?? {}))
    if (sp.env[name]) out.push(cut(cmd, ...sp.env[name], r.id));
  return out;
}

export function rewrite(command: string, v: Verdict, home: string): Rewritten {
  const subs = parse(command);
  const edits: Edit[] = [];
  for (const r of v.fired.filter((r) => r.action === "rewrite"))
    for (const s of subs.filter((s) => firesOn(r, s, subs))) {
      if (!s.spans) return { error: "the command is too complex to rewrite safely" };
      const e = editsFor(r, s, command);
      if ("error" in e) return e;
      edits.push(...e);
    }
  if (!edits.length) return { error: "nothing to rewrite" };
  // Right to left so earlier offsets hold; at one spot, replace before insert.
  edits.sort((a, b) => b.from - a.from || b.to - a.to);
  for (let i = 1; i < edits.length; i++)
    if (edits[i].to > edits[i - 1].from)
      return {
        error: `${[edits[i].id, edits[i - 1].id].sort().join(" and ")} edit the same text`,
      };
  let out = command;
  for (const e of edits) out = out.slice(0, e.from) + e.text + out.slice(e.to);
  return { command: out };
}
