import { expect, mock, test } from "claude-code/testing";

const HOME = "/home/u";
const USER = `${HOME}/.claude/rules/arbiter`;

type Opts = {
  unlistable?: string;
  toolThrows?: boolean;
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
  on("fs.list", ($: any, e: any) =>
    e.path === o.unlistable
      ? { deny: "EACCES" }
      : {
          value: under(e.path).map((p) => ({
            name: p.slice(e.path.length + 1),
            kind: "file",
            size: 0,
            isLink: false,
          })),
        },
  );
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
    if (o.toolThrows && e.tool === "Bash") throw new Error("tool exploded");
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
    description: Plaintext creds.
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
  const want =
    'DENY  "aws sso login"\n  aws/no-sso-login  (user: ~/.claude/rules/arbiter/cloud.yaml)\n    description: Plaintext creds.\n    hint: Use aws-vault.';
  expect(
    (await $.command.run({ command: "arbiter", args: "check aws sso login" }))
      .text,
  ).toBe(want);
  expect(
    (await $.command.run({ command: "arbiter", args: 'check "aws sso login"' }))
      .text,
  ).toBe(want);
  expect(
    (await $.command.run({ command: "arbiter", args: "check 'aws sso login'" }))
      .text,
  ).toBe(want);
  expect(
    (await $.command.run({ command: "arbiter", args: "check ls" })).text,
  ).toBe('ALLOW  "ls"  no rule fired');
});

test("/arbiter list and list <id>", async ($, on) => {
  await boot($, on, { files: RULES });
  expect(
    (await $.command.run({ command: "arbiter", args: "list k8s" })).text,
  ).toBe(
    "2 rules\nID              ACTION  LAYER  DESCRIPTION\nk8s/ask-delete  ask     user\nk8s/warn-get    warn    user",
  );
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
  ).toMatch(/^unknown subcommand bogus\n\n3 rules loaded, 0 errors\n/);
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
  expect((await ui.find({ type: "Text", text: "DENY" })).props.color).toBe(
    "red",
  );
  expect(
    await ui.find({ type: "Text", text: /aws\/no-sso-login  aws sso login$/ }),
  ).toBeDefined();
  expect(
    (await ui.find({ type: "Text", text: /broken\.yaml/ })).props.color,
  ).toBe("yellow");
});

test("/arbiter test reports skipped rule files", async ($, on) => {
  await boot($, on, {
    files: { ...RULES, [`${USER}/broken.yaml`]: "rules: [" },
  });
  const text = (await $.command.run({ command: "arbiter", args: "test" })).text;
  expect(text).toMatch(/^1\/1 rule tests passed; 1 rule file skipped\n/);
  expect(text).toContain(`SKIPPED ${USER}/broken.yaml`);
});

test("an unreadable layer directory is reported, other layers still load", async ($, on) => {
  const toasts: string[] = [];
  const PROJECT = "/work/.claude/rules/arbiter";
  await boot($, on, {
    toasts,
    unlistable: USER,
    files: {
      ...RULES,
      [`${PROJECT}/p.yaml`]:
        "rules:\n  - id: p/x\n    match: { cmd: kubectl }\n",
    },
  });
  expect(
    (await $.tool.call({ tool: "Bash", command: "kubectl get pods" })).deny,
  ).toBe("arbiter p/x");
  expect(toasts).toEqual([
    "arbiter: 1 rule file skipped. Run /arbiter for details.",
  ]);
  expect(
    (await $.command.run({ command: "arbiter", args: "reload" })).text,
  ).toBe("rules: plugin 0, user 0, project 1; disabled 0; errors 1");
});

test("/arbiter init explains where rules live without creating files", async ($, on) => {
  await boot($, on, { files: RULES });
  const text = (await $.command.run({ command: "arbiter", args: "init" })).text;
  expect(text).toContain("user     ~/.claude/rules/arbiter  3 rules");
  expect(text).toContain("project  /work/.claude/rules/arbiter  not created");
  expect(text).toMatch(/plugin   .*\/rules  not created/);
  expect(text).toContain("rules:\n    - id: me/kubectl-context");
  expect(text).toContain("/arbiter reload");
  expect(text).toContain(
    "  # yaml-language-server: $schema=https://raw.githubusercontent.com/jmreicha/agent-tools/main/hooks/arbiter/rule.schema.json\n  rules:",
  );
  expect(text).toMatch(
    /\nGuide: \S+\/hooks\/arbiter\/README\.md\nExamples: \S+\/hooks\/arbiter\/examples\/rules\.yaml$/,
  );
  expect(
    (await $.command.run({ command: "arbiter", args: "bogus" })).text,
  ).toContain("/arbiter init");
});

test("/arbiter with no args shows help with status", async ($, on) => {
  await boot($, on, { files: RULES });
  const text = (await $.command.run({ command: "arbiter", args: "" })).text;
  expect(text).toMatch(/^3 rules loaded, 0 errors\n\n/);
  expect(text).toContain(
    "  /arbiter pane               open the live verdict pane",
  );
  expect(text).toContain("  /arbiter help               show this help");
  expect((await $.command.run({ command: "arbiter", args: "help" })).text).toBe(
    text,
  );
});

test("/arbiter pane opens the pane", async ($, on) => {
  await boot($, on, { files: RULES });
  expect(await $.command.run({ command: "arbiter", args: "pane" })).toEqual({});
});

test("/arbiter list shows descriptions and disabled rules", async ($, on) => {
  await boot($, on, {
    files: {
      ...RULES,
      "/work/.claude/rules/arbiter/p.yaml": "disable: [aws/no-sso-login]\n",
    },
  });
  expect(
    (await $.command.run({ command: "arbiter", args: "list aws" })).text,
  ).toBe(
    "1 rule\nID                ACTION  LAYER  DESCRIPTION\naws/no-sso-login  deny    user   [disabled by project] Plaintext creds.",
  );
});

test("/arbiter list is sorted by id across layers", async ($, on) => {
  await boot($, on, {
    files: {
      ...RULES,
      "/work/.claude/rules/arbiter/p.yaml":
        "rules:\n  - id: a/project\n    match: { cmd: x }\n",
    },
  });
  const ids = (await $.command.run({ command: "arbiter", args: "list" })).text
    .split("\n")
    .slice(2)
    .map((l: string) => l.split(" ")[0]);
  expect(ids).toEqual([
    "a/project",
    "aws/no-sso-login",
    "k8s/ask-delete",
    "k8s/warn-get",
  ]);
});

test("/arbiter test sorts failures by id and skipped files by path", async ($, on) => {
  const bad = (id: string) =>
    `  - id: ${id}\n    match: { cmd: x }\n    tests:\n      deny: ["y", "w"]\n`;
  await boot($, on, {
    root: "/a",
    files: {
      [`${USER}/r.yaml`]: `rules:\n${bad("z/last")}${bad("a/first")}`,
      [`${USER}/broken.yaml`]: "rules: [",
      "/a/.claude/rules/arbiter/broken.yaml": "rules: [",
    },
  });
  const lines = (
    await $.command.run({ command: "arbiter", args: "test" })
  ).text.split("\n");
  expect(lines.slice(1, 3).map((l: string) => l.split(":")[0])).toEqual([
    "SKIPPED /a/.claude/rules/arbiter/broken.yaml",
    `SKIPPED ${USER}/broken.yaml`,
  ]);
  expect(lines.slice(3)).toEqual([
    'FAIL a/first: "w" expected deny, got allow',
    'FAIL a/first: "y" expected deny, got allow',
    'FAIL z/last: "w" expected deny, got allow',
    'FAIL z/last: "y" expected deny, got allow',
  ]);
});

test("pane lists errors sorted by path", async ($, on) => {
  await boot($, on, {
    root: "/a",
    files: {
      [`${USER}/broken.yaml`]: "rules: [",
      "/a/.claude/rules/arbiter/broken.yaml": "rules: [",
    },
  });
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
  const first = await ui.find({ type: "Text", text: /broken\.yaml/ });
  expect(first.children[0]).toMatch(/^\/a\/\.claude/);
});

test("/arbiter check without a command shows its usage", async ($, on) => {
  await boot($, on, { files: RULES });
  expect(
    (await $.command.run({ command: "arbiter", args: "check" })).text,
  ).toBe(
    'usage: /arbiter check "<command>"\n  Dry-run a Bash command against the rules; nothing runs.\n  example: /arbiter check "aws s3 ls --profile prod"',
  );
});

const ROW = (text: string, command = "arbiter") => ({
  plugin: "agent-tools",
  component: "CommandOutput",
  requestId: "m1",
  surface: "terminal",
  viewport: { columns: 100, rows: 30 },
  props: { command, args: "", text, isErrored: false },
});

test("colorize leaves other commands' rows alone", async ($, on) => {
  on("ui.render", () => ({
    type: "Text",
    props: {},
    children: ["drawn by Claude Code"],
  }));
  await boot($, on, { files: RULES });
  const ui = await $.ui.mount(ROW("agent-tools: DENY", "other"));
  expect(
    await ui.find({ type: "Text", text: "drawn by Claude Code" }),
  ).toBeDefined();
});

test("colorize check output", async ($, on) => {
  await boot($, on, { files: RULES });
  const text =
    'agent-tools: DENY  "aws sso login"\n  aws/no-sso-login  (user: ~/.claude/rules/arbiter/cloud.yaml)\n    description: Plaintext creds.\n    hint: Use aws-vault.';
  const ui = await $.ui.mount(ROW(text));
  expect(
    (await ui.find({ type: "Text", text: "agent-tools: " })).props.dimColor,
  ).toBe(true);
  const deny = await ui.find({ type: "Text", text: "DENY" });
  expect(deny.props).toMatchObject({ color: "red", bold: true });
  expect(
    (await ui.find({ type: "Text", text: "  aws/no-sso-login" })).props.bold,
  ).toBe(true);
  expect(
    (await ui.find({ type: "Text", text: /^\s+\(user: / })).props.dimColor,
  ).toBe(true);
  expect(
    (await ui.find({ type: "Text", text: "description:" })).props.dimColor,
  ).toBe(true);
  expect(
    await ui.find({ type: "Text", text: " Plaintext creds." }),
  ).toBeDefined();
});

test("colorize verdict words", async ($, on) => {
  await boot($, on, { files: RULES });
  for (const [word, color] of [
    ["ASK", "yellow"],
    ["WARN", "yellow"],
    ["ALLOW", "green"],
  ]) {
    const ui = await $.ui.mount(ROW(`agent-tools: ${word}  "x"`));
    expect((await ui.find({ type: "Text", text: word })).props.color).toBe(
      color,
    );
    await ui.unmount();
  }
});

test("colorize test output and error handling in yellow", async ($, on) => {
  await boot($, on, { files: RULES });
  let ui = await $.ui.mount(ROW("agent-tools: 3/3 rule tests passed"));
  expect(
    (await ui.find({ type: "Text", text: "3/3 rule tests passed" })).props
      .color,
  ).toBe("green");
  await ui.unmount();
  ui = await $.ui.mount(
    ROW(
      'agent-tools: 1/2 rule tests passed; 1 rule file skipped\nSKIPPED /x.yaml: bad\nFAIL a/b: "y" expected deny, got allow',
    ),
  );
  expect(
    (await ui.find({ type: "Text", text: /^1\/2 rule tests passed/ })).props
      .color,
  ).toBe("yellow");
  expect((await ui.find({ type: "Text", text: /^SKIPPED/ })).props.color).toBe(
    "yellow",
  );
  expect((await ui.find({ type: "Text", text: /^FAIL/ })).props.color).toBe(
    "red",
  );
  await ui.unmount();
  for (const line of [
    "unknown subcommand nope",
    'usage: /arbiter check "<command>"',
    "no rules match",
  ]) {
    ui = await $.ui.mount(ROW(`agent-tools: ${line}`));
    expect((await ui.find({ type: "Text", text: line })).props.color).toBe(
      "yellow",
    );
    await ui.unmount();
  }
});

test("colorize list header and action cells", async ($, on) => {
  await boot($, on, { files: RULES });
  const ui = await $.ui.mount(
    ROW(
      "agent-tools: 2 rules\nID     ACTION  LAYER  DESCRIPTION\na/one  deny    user   x\nb/two  ask     user   y",
    ),
  );
  expect(
    (await ui.find({ type: "Text", text: "ID     ACTION  LAYER  DESCRIPTION" }))
      .props.bold,
  ).toBe(true);
  expect((await ui.find({ type: "Text", text: "deny    " })).props.color).toBe(
    "red",
  );
  expect((await ui.find({ type: "Text", text: "ask     " })).props.color).toBe(
    "yellow",
  );
});

test("a failure after the tool ran keeps the tool's own outcome", async ($, on) => {
  await boot($, on, { files: RULES, toolThrows: true });
  let outcome: unknown;
  try {
    outcome = await $.tool.call({ tool: "Bash", command: "ls" });
  } catch (err) {
    outcome = "rejected";
  }
  expect(JSON.stringify(outcome ?? null)).not.toContain("arbiter failed");
});
