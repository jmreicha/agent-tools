import { expect, test } from "claude-code/testing";
import { evaluate, runRuleTests } from "./engine.ts";
import { parseRuleFile, type Rule } from "./rules.ts";

const HOME = "/home/u";
const rules = (yaml: string): Rule[] => {
  const f = parseRuleFile(yaml, "/r.yaml", "user");
  if (f.errors.length) throw new Error(JSON.stringify(f.errors));
  return f.rules;
};
const bash = (command: string, rs: Rule[]) =>
  evaluate("Bash", { command }, rs, HOME);

const VAULT = rules(`
rules:
  - id: aws/requires-vault
    match: { cmd: aws }
    unless: { wrapped_by: aws-vault }
    description: AWS goes through aws-vault.
    hint: Use aws-vault exec lytxread -- aws.
  - id: aws/no-sso-login
    match: { cmd: aws, args: [sso, login] }
    hint: Never.
  - id: k8s/ask-delete
    match: { cmd: kubectl, args: [[delete, drain]] }
    action: ask
  - id: k8s/warn-get
    match: { cmd: kubectl, args: [get] }
    action: warn
  - id: fs/kubeconfig
    tool: [Edit, Write]
    match: { path: "~/.kube/config" }
  - id: mcp/no-prod
    tool: /^mcp__prod__/
    match: { regex: "/x/" }
`);

test("no match allows", () => {
  expect(bash("ls -la", VAULT)).toEqual({
    action: "allow",
    fired: [],
    message: "",
  });
});

test("deny lists every fired deny rule sorted by id", () => {
  const v = bash("aws sso login", VAULT);
  expect(v.action).toBe("deny");
  expect(v.fired.map((r) => r.id)).toEqual([
    "aws/no-sso-login",
    "aws/requires-vault",
  ]);
  expect(v.message).toBe(
    "arbiter aws/no-sso-login: Never.\narbiter aws/requires-vault: AWS goes through aws-vault. Use aws-vault exec lytxread -- aws.",
  );
});

test("unless excuses the same sub-command", () => {
  expect(bash("aws-vault exec lytxread -- aws s3 ls", VAULT).action).toBe(
    "allow",
  );
  expect(
    bash("aws-vault exec lytxread -- true && aws s3 ls", VAULT).action,
  ).toBe("deny");
});

test("quoted mention does not fire", () => {
  expect(
    bash(`echo "aws s3 ls" && grep 'kubectl delete' notes.md`, VAULT).action,
  ).toBe("allow");
});

test("text inside heredoc does not fire", () => {
  expect(
    bash(
      `git commit -m "$(cat <<'EOF'\nnever run aws sso login\nEOF\n)"`,
      VAULT,
    ).action,
  ).toBe("allow");
});

test("strictest action wins and fired lists all", () => {
  const v = bash(
    "kubectl --context p delete pod x && kubectl --context p get pods",
    VAULT,
  );
  expect(v.action).toBe("ask");
  expect(v.fired.map((r) => r.id)).toEqual(["k8s/ask-delete", "k8s/warn-get"]);
  expect(v.message).toBe("arbiter k8s/ask-delete");
  expect(bash("kubectl get pods", VAULT).action).toBe("warn");
});

test("args match in order across flag values", () => {
  expect(bash("kubectl --context prod delete pod web", VAULT).action).toBe(
    "ask",
  );
  expect(bash("kubectl logs deploy/delete-worker", VAULT).action).toBe("allow");
});

test("path rules use file_path and expand ~", () => {
  expect(
    evaluate("Edit", { file_path: "/home/u/.kube/config" }, VAULT, HOME).action,
  ).toBe("deny");
  expect(
    evaluate("Read", { file_path: "/home/u/.kube/config" }, VAULT, HOME).action,
  ).toBe("allow");
  expect(
    evaluate("Edit", { file_path: "/home/u/.kube/config2" }, VAULT, HOME)
      .action,
  ).toBe("allow");
});

test("command matchers never fire for non-Bash tools; tool regex works", () => {
  expect(evaluate("Write", { command: "aws s3 ls" }, VAULT, HOME).action).toBe(
    "allow",
  );
  expect(evaluate("mcp__prod__query", {}, VAULT, HOME).action).toBe("allow");
});

test("rewrite behaves as deny", () => {
  const rs = rules(
    "rules:\n  - id: rm/trash\n    match: { cmd: rm }\n    action: rewrite\n    to: trash\n",
  );
  expect(bash("rm a", rs).action).toBe("deny");
});

test("flags, env, wrapped_by lists, globs and regex", () => {
  const rs = rules(`
rules:
  - id: t/flags
    match: { cmd: git, flags: [--force] }
  - id: t/env
    match: { env: { AWS_PROFILE: "prod*" } }
  - id: t/wrap
    match: { cmd: terraform, wrapped_by: [sudo, op] }
  - id: t/regex
    match: { regex: "/DROP\\\\s+TABLE/i" }
`);
  expect(bash("git push --force", rs).action).toBe("deny");
  expect(bash("git push -f", rs).action).toBe("allow");
  expect(bash("AWS_PROFILE=prod-admin true", rs).action).toBe("deny");
  expect(bash("AWS_PROFILE=dev true", rs).action).toBe("allow");
  expect(bash("op run -- terraform plan", rs).action).toBe("deny");
  expect(bash('psql -c "drop   table x"', rs).action).toBe("deny");
});

test("unparsable command still meets regex rules only", () => {
  const rs = rules(
    `rules:\n  - id: t/r\n    match: { regex: "/aws/" }\n  - id: t/c\n    match: { cmd: aws }\n`,
  );
  const v = bash(`aws s3 ls 'oops`, rs);
  expect(v.fired.map((r) => r.id)).toEqual(["t/r"]);
});

test("runRuleTests passes and fails per input", () => {
  const [r] = rules(`
rules:
  - id: t/k
    match: { cmd: kubectl }
    unless: { flags: [--context] }
    tests:
      deny: ["kubectl get pods", "kubectl --context p get pods"]
      allow: ["kubectl --context p get pods"]
`);
  expect(
    runRuleTests(r, HOME).map((t) => [t.input, t.expected, t.actual, t.pass]),
  ).toEqual([
    ["kubectl get pods", "deny", "deny", true],
    ["kubectl --context p get pods", "deny", "allow", false],
    ["kubectl --context p get pods", "allow", "allow", true],
  ]);
});

test("runRuleTests uses Edit and expands ~ for path rules, ignoring tool", () => {
  const [r] = rules(
    'rules:\n  - id: t/p\n    tool: /^Write$/\n    match: { path: "~/.kube/config" }\n    tests:\n      deny: ["~/.kube/config"]\n      allow: ["~/other"]\n',
  );
  expect(runRuleTests(r, HOME).every((t) => t.pass)).toBe(true);
  expect(
    runRuleTests(
      rules("rules:\n  - id: t/n\n    match: { cmd: x }\n")[0],
      HOME,
    ),
  ).toEqual([]);
});
