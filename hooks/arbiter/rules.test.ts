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
