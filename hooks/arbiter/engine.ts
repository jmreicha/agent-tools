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
  const text = [r.description, r.hint].filter(Boolean).join(" ");
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
  const fired = rules
    .filter((r) => toolIs(r.tool, tool) && fires(r, subs, file, home))
    .sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
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
