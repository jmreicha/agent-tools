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
let layers: { layer: Layer; dir: string; exists: boolean }[] = [];
let pluginRoot = "";
const SCHEMA =
  "https://raw.githubusercontent.com/jmreicha/agent-tools/main/hooks/arbiter/rule.schema.json";
const recent: Hit[] = [];

const COMMANDS: [string, string][] = [
  ["/arbiter help", "show this help"],
  ["/arbiter init", "where rules live and how to add one"],
  ["/arbiter list [filter|id]", "list rules, or print one rule's YAML"],
  ['/arbiter check "<command>"', "dry-run a Bash command against the rules"],
  ["/arbiter test", "run every rule's inline tests"],
  ["/arbiter reload", "re-read rule files"],
  ["/arbiter pane", "open the live verdict pane"],
];

const cmp = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);
const byPath = (a: Problem, b: Problem) =>
  cmp(a.path, b.path) || (a.line ?? 0) - (b.line ?? 0);

// Rows padded into aligned columns, trailing spaces trimmed.
function table(rows: string[][]): string {
  const widths = rows[0].map((_, c) =>
    Math.max(...rows.map((r) => r[c].length)),
  );
  return rows
    .map((r) =>
      r
        .map((cell, c) => cell.padEnd(widths[c]))
        .join("  ")
        .trimEnd(),
    )
    .join("\n");
}

function help(): string {
  const n = rules.rules.length;
  const errs = rules.errors.length;
  const status = `${n} rule${n === 1 ? "" : "s"} loaded, ${errs} error${errs === 1 ? "" : "s"}`;
  return `${status}\n\n${table(COMMANDS.map(([cmd, what]) => ["  " + cmd, what]))}`;
}

async function loadRules($: EngineInterface) {
  home = (await $.env.get("HOME")) ?? "";
  pluginRoot = $.plugin.root;
  const user = `${home}/.claude/rules/arbiter`;
  const project = `${await $.session.root()}/.claude/rules/arbiter`;
  const dirs: [Layer, string][] = [
    ["plugin", `${$.plugin.root}/rules`],
    ["user", user],
  ];
  if (project !== user) dirs.push(["project", project]);
  const files: ParsedFile[] = [];
  layers = [];
  for (const [layer, dir] of dirs) {
    const exists = await $.fs.exists(dir);
    layers.push({ layer, dir, exists });
    if (!exists) continue;
    let entries;
    try {
      entries = await $.fs.list(dir);
    } catch (err) {
      // one unreadable layer must not drop the others
      const error = { path: dir, message: `cannot list: ${String(err)}` };
      files.push({ path: dir, layer, rules: [], disable: [], errors: [error] });
      continue;
    }
    for (const entry of entries) {
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

function check(input: string): string {
  const command = input.replace(/^(["'])(.*)\1$/s, "$2");
  const v = evaluate("Bash", { command }, rules.rules, home);
  if (v.action === "allow") return `ALLOW  "${command}"  no rule fired`;
  const lines = [`${v.action.toUpperCase()}  "${command}"`];
  for (const r of v.fired) {
    lines.push(`  ${r.id}  (${r.layer}: ${short(r.path)})`);
    if (r.description) lines.push(`    description: ${r.description}`);
    if (r.hint) lines.push(`    hint: ${r.hint}`);
  }
  return lines.join("\n");
}

function list(filter: string): string {
  const exact = rules.rules.find((r) => r.id === filter);
  if (exact) return dump(exact.source).trimEnd();
  const rows = [
    ...rules.rules.map((r) => [r.id, r.action, r.layer, r.description ?? ""]),
    ...rules.disabled.map((d) => [
      d.rule.id,
      d.rule.action,
      d.rule.layer,
      `[disabled by ${d.by}] ${d.rule.description ?? ""}`.trimEnd(),
    ]),
  ]
    .filter((row) => row[0].includes(filter))
    .sort((a, b) => cmp(a[0], b[0]));
  if (!rows.length) return "no rules match";
  const count = `${rows.length} rule${rows.length === 1 ? "" : "s"}`;
  return `${count}\n${table([["ID", "ACTION", "LAYER", "DESCRIPTION"], ...rows])}`;
}

// Path with the home directory shown as ~.
function short(path: string): string {
  return home && path.startsWith(home + "/")
    ? "~" + path.slice(home.length)
    : path;
}

function init(): string {
  const rows = layers.map(({ layer, dir, exists }) => {
    const n = rules.rules.filter((r) => r.layer === layer).length;
    return `  ${layer.padEnd(8)} ${short(dir)}  ${exists ? `${n} rule${n === 1 ? "" : "s"}` : "not created"}`;
  });
  return [
    "arbiter loads *.yaml rule files from these folders (later layers win):",
    ...rows,
    "",
    "Add your own: create a .yaml file in the user folder (all repos) or project folder (this repo):",
    `  # yaml-language-server: $schema=${SCHEMA}`,
    "  rules:",
    "    - id: me/kubectl-context",
    "      match: { cmd: kubectl }",
    "      unless: { flags: [--context] }",
    "      hint: Pass --context <existing-context>.",
    "      tests:",
    '        deny: ["kubectl get pods"]',
    "",
    'Then: /arbiter reload, /arbiter check "<command>", /arbiter test.',
    `Guide: ${short(pluginRoot)}/hooks/arbiter/README.md`,
    `Examples: ${short(pluginRoot)}/hooks/arbiter/examples/rules.yaml`,
  ].join("\n");
}

function testAll(): string {
  const results = rules.rules.flatMap((r) => runRuleTests(r, home));
  const failed = results
    .filter((t) => !t.pass)
    .sort((a, b) => cmp(a.id, b.id) || cmp(a.input, b.input));
  const skipped = rules.errors
    .filter((e, i, all) => all.findIndex((x) => x.path === e.path) === i)
    .sort(byPath);
  const head =
    `${results.length - failed.length}/${results.length} rule tests passed` +
    (skipped.length
      ? `; ${skipped.length} rule file${skipped.length === 1 ? "" : "s"} skipped`
      : "");
  return [
    head,
    ...skipped.map((p) => `SKIPPED ${describe(p)}`),
    ...failed.map(
      (t) =>
        `FAIL ${t.id}: ${JSON.stringify(t.input)} expected ${t.expected}, got ${t.actual}`,
    ),
  ].join("\n");
}

const COLOR: Record<string, string> = {
  deny: "red",
  rewrite: "red",
  ask: "yellow",
  warn: "yellow",
  allow: "green",
};

type Seg = [string, Record<string, unknown>?];

// One output line as styled segments; the text itself is unchanged.
function segments(
  line: string,
  table: { action: number; layer: number } | null,
): Seg[] {
  let m: RegExpExecArray | null;
  if ((m = /^(DENY|ASK|WARN|ALLOW)\b(.*)$/s.exec(line)))
    return [[m[1], { color: COLOR[m[1].toLowerCase()], bold: true }], [m[2]]];
  if (/^FAIL\b/.test(line)) return [[line, { color: "red" }]];
  if (/^(SKIPPED\b|unknown subcommand|usage:|no rules match)/.test(line))
    return [[line, { color: "yellow" }]];
  if ((m = /^(\d+)\/(\d+) rule tests passed(.*)$/s.exec(line)))
    return [[line, { color: m[1] === m[2] && !m[3] ? "green" : "yellow" }]];
  if ((m = /^(\s+)(description:|hint:)(.*)$/s.exec(line)))
    return [[m[1]], [m[2], { dimColor: true }], [m[3]]];
  if ((m = /^(\s+\S+)(\s+\((?:plugin|user|project): .*\))$/s.exec(line)))
    return [
      [m[1], { bold: true }],
      [m[2], { dimColor: true }],
    ];
  if (table) {
    const cell = line.slice(table.action, table.layer);
    return [
      [line.slice(0, table.action)],
      [cell, { color: COLOR[cell.trim()] }],
      [line.slice(table.layer)],
    ];
  }
  return [[line]];
}

async function drawOutput($: EngineInterface, e: any, next: any) {
  if (e.props.command !== "arbiter" || e.props.isErrored) return next(e);
  const { Box, Text } = $.ui.resolve(e);
  const prefix = `${$.plugin.name}: `;
  let table: { action: number; layer: number } | null = null;
  const rows = String(e.props.text)
    .split("\n")
    .map((raw: string, i: number) => {
      const lead = i === 0 && raw.startsWith(prefix) ? prefix : "";
      const line = raw.slice(lead.length);
      let segs: Seg[];
      if (/^ID +ACTION +LAYER +DESCRIPTION$/.test(line)) {
        table = {
          action: line.indexOf("ACTION"),
          layer: line.indexOf("LAYER"),
        };
        segs = [[line, { bold: true }]];
      } else segs = segments(line, table);
      if (lead) segs.unshift([lead, { dimColor: true }]);
      const parts = segs
        .filter(([s]) => s !== "")
        .map(([s, props]) => Text({ ...props, children: [s] }));
      return Box({
        flexDirection: "row",
        children: parts.length ? parts : [Text({ children: [" "] })],
      });
    });
  return Box({ flexDirection: "column", children: rows });
}

async function guardCall($: EngineInterface, e: any, next: any) {
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

async function runCommand($: EngineInterface, e: any) {
  const args = String(e.args ?? "").trim();
  const sub = args.split(/\s+/)[0];
  const rest = args.slice(sub.length).trim();
  if (!sub || sub === "help") return { text: help() };
  if (sub === "pane") {
    await $.ui.open({ id: "arbiter", title: "arbiter", closeOnEscape: true });
    return {};
  }
  if (sub === "check")
    return {
      text: rest
        ? check(rest)
        : 'usage: /arbiter check "<command>"\n  Dry-run a Bash command against the rules; nothing runs.\n  example: /arbiter check "aws s3 ls --profile prod"',
    };
  if (sub === "list") return { text: list(rest) };
  if (sub === "init") return { text: init() };
  if (sub === "test") return { text: testAll() };
  if (sub === "reload") {
    await loadRules($);
    return { text: summary() };
  }
  return { text: `unknown subcommand ${sub}\n\n${help()}` };
}

async function drawPane($: EngineInterface, e: any) {
  const { Box, Text } = $.ui.resolve(e);
  const n = (l: Layer) => rules.rules.filter((r) => r.layer === l).length;
  const problems = [
    ...[...rules.errors]
      .sort(byPath)
      .map((p) =>
        Text({ color: "yellow", wrap: "wrap", children: [describe(p)] }),
      ),
    ...[...rules.warnings]
      .sort(byPath)
      .map((p) =>
        Text({ color: "yellow", wrap: "wrap", children: [describe(p)] }),
      ),
  ];
  const hits = recent.length
    ? recent.map((h) =>
        Box({
          flexDirection: "row",
          children: [
            Text({
              dimColor: true,
              children: [`${new Date(h.at).toLocaleTimeString()}  `],
            }),
            Text({
              color: COLOR[h.action],
              bold: true,
              children: [h.action.toUpperCase()],
            }),
            Text({
              wrap: "truncate-end",
              children: [`  ${h.ids.join(",")}  ${h.target}`],
            }),
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
      argumentHint:
        "[help | init | list | check <command> | test | reload | pane]",
      immediate: true,
    });
    await loadRules($);
    return next(e);
  });

  on("tool.call", async ($, e, next) => guardCall($, e, next)).catch(
    async ($, e, next) => ({
      deny: `arbiter failed (${next.error.kind}): ${next.error.message}`,
    }),
  );

  on("command.run", { command: "arbiter" }, async ($, e) => runCommand($, e));

  on("ui.render", { component: "CommandOutput" }, async ($, e, next) =>
    drawOutput($, e, next),
  );

  on("ui.render", { component: "Pane", requestId: "arbiter" }, async ($, e) =>
    drawPane($, e),
  );
}
