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

async function loadRules($: EngineInterface) {
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
  const skipped = rules.errors.filter((e, i, all) => all.findIndex((x) => x.path === e.path) === i);
  const head =
    `${results.length - failed.length}/${results.length} rule tests passed` +
    (skipped.length ? `; ${skipped.length} rule file${skipped.length === 1 ? "" : "s"} skipped` : "");
  return [
    head,
    ...skipped.map((p) => `SKIPPED ${describe(p)}`),
    ...failed.map(
      (t) =>
        `FAIL ${t.id}: ${JSON.stringify(t.input)} expected ${t.expected}, got ${t.actual}`,
    ),
  ].join("\n");
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
  if (!sub) {
    await $.ui.open({ id: "arbiter", title: "arbiter", closeOnEscape: true });
    return {};
  }
  if (sub === "check" && rest) return { text: check(rest) };
  if (sub === "list") return { text: list(rest) };
  if (sub === "test") return { text: testAll() };
  if (sub === "reload") {
    await loadRules($);
    return { text: summary() };
  }
  return { text: USAGE };
}

async function drawPane($: EngineInterface, e: any) {
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
    await loadRules($);
    return next(e);
  });

  on("tool.call", async ($, e, next) => guardCall($, e, next)).catch(
    async ($, e, next) => ({
      deny: `arbiter failed (${next.error.kind}): ${next.error.message}`,
    }),
  );

  on("command.run", { command: "arbiter" }, async ($, e) => runCommand($, e));

  on("ui.render", { component: "Pane", requestId: "arbiter" }, async ($, e) =>
    drawPane($, e),
  );
}
