import { expect, mock, test } from "claude-code/testing";

const HOME = "/home/u";
const USER = `${HOME}/.claude/rules/arbiter`;

type Opts = {
  unlistable?: string;
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
    e.path === o.unlistable ? { deny: "EACCES" } : ({
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

test("/arbiter test reports skipped rule files", async ($, on) => {
  await boot($, on, { files: { ...RULES, [`${USER}/broken.yaml`]: "rules: [" } });
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
    files: { ...RULES, [`${PROJECT}/p.yaml`]: "rules:\n  - id: p/x\n    match: { cmd: kubectl }\n" },
  });
  expect((await $.tool.call({ tool: "Bash", command: "kubectl get pods" })).deny).toBe("arbiter p/x");
  expect(toasts).toEqual(["arbiter: 1 rule file skipped. Run /arbiter for details."]);
  expect((await $.command.run({ command: "arbiter", args: "reload" })).text).toBe(
    "rules: plugin 0, user 0, project 1; disabled 0; errors 1",
  );
});
