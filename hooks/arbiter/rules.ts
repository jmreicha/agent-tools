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
  piped_to?: Matcher;
};
export type Rule = {
  id: string;
  tool: string | string[];
  match: Matcher[];
  unless: Matcher[];
  action: Action;
  to?: string;
  description?: string;
  hint?: string;
  enabled: boolean;
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
  for (const k of ["description", "hint"] as const)
    if (k in r && !isStr(r[k])) out.push(`${k} must be a string`);
  if ("enabled" in r && typeof r.enabled !== "boolean")
    out.push("enabled must be true or false");
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

  const rules = (raw as Record<string, unknown>[]).map((r): Rule => ({
    id: r.id as string,
    tool: (r.tool as string | string[] | undefined) ?? "Bash",
    match: [r.match].flat() as Matcher[],
    unless: r.unless === undefined ? [] : ([r.unless].flat() as Matcher[]),
    action: (r.action as Action | undefined) ?? "deny",
    to: r.to as string | undefined,
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
