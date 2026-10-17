// Rule files: parse, validate, merge layers. Spec: rules.yass.yaml
import { load, YAMLException } from "./vendor/js-yaml.mjs";

export type Layer = "plugin" | "user" | "project";
export type Action = "deny" | "ask" | "warn" | "rewrite";
export type Outcome = "deny" | "ask" | "rewrite" | "warn" | "allow";
export type RewriteTo = {
  prefix?: string;
  cmd?: string;
  flags?: Record<string, string | null>;
  env?: Record<string, null>;
};
export type Repeat = {
  count: number;
  within: number;
  reset_on?: string | string[];
  same: boolean;
};
// One step of a repeat rule's test: an input string, or a bare call to a tool.
export type Step = string | { tool: string };
export type Matcher = {
  cmd?: string | string[];
  args?: (string | string[])[];
  flags?: string[];
  wrapped_by?: string | string[];
  env?: Record<string, string>;
  regex?: string;
  path?: string | string[];
  piped_to?: Matcher;
};
export type Rule = {
  id: string;
  tool: string | string[];
  match: Matcher[];
  unless: Matcher[];
  action: Action;
  to?: RewriteTo;
  repeat?: Repeat;
  description?: string;
  hint?: string;
  enabled: boolean;
  // Repeat rules list sequences of steps instead of single inputs.
  tests: Partial<Record<Exclude<Outcome, "rewrite">, string[] | Step[][]>> & {
    rewrite?: Record<string, string>;
  };
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
  // by "self": the rule has enabled: false.
  disabled: { rule: Rule; by: Layer | "self" }[];
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
  "repeat",
  "description",
  "hint",
  "enabled",
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
  "piped_to",
];
const ACTIONS = ["deny", "ask", "warn", "rewrite"];
const OUTCOMES = ["deny", "ask", "rewrite", "warn", "allow"];
const TO_KEYS = ["prefix", "cmd", "flags", "env"];
const REPEAT_KEYS = ["count", "within", "reset_on", "same"];
export const MAX_WITHIN = 200;
const DEFAULT_WITHIN = 20;
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

function canBeBash(t: string): boolean {
  const m = REGEX.exec(t);
  if (!m) return t === "Bash";
  try {
    return new RegExp(m[1], m[2]).test("Bash");
  } catch {
    return false; // reported as an invalid regex
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
  if ("piped_to" in m) {
    checkMatcher(m.piped_to, `${where}.piped_to`, out);
    if (isObj(m.piped_to) && "path" in m.piped_to)
      out.push(`${where}.piped_to: path is not allowed in piped_to`);
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
    if (!RULE_KEYS.includes(k))
      out.push(
        k === "reason"
          ? "unknown key reason (renamed to description)"
          : `unknown key ${k}`,
      );
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
  if (!("match" in r)) {
    // A rule without match fires on every call to its tools, so never on Bash.
    const tools = "tool" in r && strOrStrs(r.tool) ? [r.tool].flat() : null;
    if (!tools) out.push("match is required");
    else if (tools.some(canBeBash)) out.push("match is required when tool can be Bash");
    if ("unless" in r) out.push("unless needs match");
  }
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
  if (r.action === "rewrite" && !("to" in r)) out.push("action rewrite needs to");
  if ("to" in r) checkRewrite(r.to, r.action, out);
  if ("repeat" in r) checkRepeat(r.repeat, r.action, out);
  for (const k of ["description", "hint"] as const)
    if (k in r && !isStr(r[k])) out.push(`${k} must be a string`);
  if ("enabled" in r && typeof r.enabled !== "boolean")
    out.push("enabled must be true or false");
  if ("tests" in r) {
    if (!isObj(r.tests)) out.push("tests must be a mapping");
    else
      for (const [k, v] of Object.entries(r.tests)) {
        if (!OUTCOMES.includes(k)) out.push(`tests: unknown outcome ${k}`);
        else if (k === "rewrite") {
          if (!isObj(v) || !Object.values(v).every(isStr))
            out.push("tests.rewrite must map commands to commands");
        } else if (!("repeat" in r)) {
          if (!isStrs(v)) out.push(`tests.${k} must be a list of strings`);
        } else if (!isSeqs(v))
          out.push(
            `tests.${k} must be a list of sequences, each a list of inputs or { tool: <name> }`,
          );
      }
  }
}

const isStep = (v: unknown): boolean =>
  isStr(v) ||
  (isObj(v) && Object.keys(v).length === 1 && isStr(v.tool));
const isSeqs = (v: unknown): boolean =>
  Array.isArray(v) &&
  v.every((q) => Array.isArray(q) && q.length > 0 && q.every(isStep));
const isInt = (v: unknown): v is number => Number.isInteger(v);

function checkRepeat(rep: unknown, action: unknown, out: string[]) {
  if (action === "rewrite") out.push("repeat cannot be used with action: rewrite");
  if (!isObj(rep) || Object.keys(rep).some((k) => !REPEAT_KEYS.includes(k))) {
    out.push("repeat must be a mapping of count, within, reset_on, same");
    return;
  }
  if (!isInt(rep.count) || rep.count < 2)
    out.push("repeat.count must be an integer of 2 or more");
  const count = isInt(rep.count) ? rep.count : 2;
  if (
    "within" in rep &&
    (!isInt(rep.within) || rep.within < count || rep.within > MAX_WITHIN)
  )
    out.push(`repeat.within must be an integer from count to ${MAX_WITHIN}`);
  else if (!("within" in rep) && count > DEFAULT_WITHIN)
    out.push(`repeat.within is required when count is over ${DEFAULT_WITHIN}`);
  if ("reset_on" in rep) {
    if (!strOrStrs(rep.reset_on))
      out.push("repeat.reset_on must be a string or list of strings");
    else
      for (const t of [rep.reset_on].flat()) {
        const bad = badRegex(t);
        if (bad) out.push(`repeat.reset_on: ${bad}`);
      }
  }
  if ("same" in rep && typeof rep.same !== "boolean")
    out.push("repeat.same must be true or false");
}

function checkRewrite(to: unknown, action: unknown, out: string[]) {
  if (action !== "rewrite") out.push("to needs action: rewrite");
  if (!isObj(to) || !Object.keys(to).length || Object.keys(to).some((k) => !TO_KEYS.includes(k))) {
    out.push("to must be a mapping of prefix, cmd, flags, env");
    return;
  }
  for (const k of ["prefix", "cmd"] as const)
    if (k in to && !isStr(to[k])) out.push(`to.${k} must be a string`);
  if ("flags" in to && (!isObj(to.flags) || !Object.values(to.flags).every((v) => v === null || isStr(v))))
    out.push("to.flags must map flags to a flag or null");
  if ("env" in to && (!isObj(to.env) || !Object.values(to.env).every((v) => v === null)))
    out.push("to.env must map names to null");
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

  const rules = (raw as Record<string, unknown>[]).map((r): Rule => ({
    id: r.id as string,
    tool: (r.tool as string | string[] | undefined) ?? "Bash",
    match: r.match === undefined ? [] : ([r.match].flat() as Matcher[]),
    unless: r.unless === undefined ? [] : ([r.unless].flat() as Matcher[]),
    action: (r.action as Action | undefined) ?? "deny",
    to: r.to as RewriteTo | undefined,
    repeat: isObj(r.repeat)
      ? {
          count: r.repeat.count as number,
          within: (r.repeat.within as number | undefined) ?? DEFAULT_WITHIN,
          reset_on: r.repeat.reset_on as string | string[] | undefined,
          same: r.repeat.same === true,
        }
      : undefined,
    description: r.description as string | undefined,
    hint: r.hint as string | undefined,
    enabled: r.enabled !== false,
    tests: (r.tests as Rule["tests"] | undefined) ?? {},
    layer,
    path,
    source: r,
  }));
  return {
    path,
    layer,
    rules,
    disable: (doc.disable as string[] | undefined) ?? [],
    errors: [],
  };
}

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
  const all = [...byId.values()];
  for (const r of all) if (!r.enabled) disabled.push({ rule: r, by: "self" });
  return { rules: all.filter((r) => r.enabled), disabled, errors, warnings };
}
