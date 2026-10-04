import { expect, test } from "claude-code/testing";
import { parse } from "./shell.ts";

const cmds = (s: string) => parse(s).map((c) => c.cmd);
const raw = (s: string) => [
  { raw: s, cmd: "", args: [], flags: [], env: {}, wrappers: [] },
];

test("splits on control operators", () => {
  expect(cmds("a && b || c; d | e & f\ng |& h")).toEqual([
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
  ]);
});

test("fills every field", () => {
  const s =
    "AWS_PROFILE=prod /usr/bin/aws --region us-east-1 s3 ls --recursive=true";
  expect(parse(s)).toEqual([
    {
      raw: s,
      cmd: "aws",
      args: ["us-east-1", "s3", "ls"],
      flags: ["--region", "--recursive"],
      env: { AWS_PROFILE: "prod" },
      wrappers: [],
    },
  ]);
});

test("quotes are data", () => {
  expect(cmds(`echo "aws s3 ls; kubectl" 'a && b'`)).toEqual(["echo"]);
  expect(parse(`echo "a b" 'c d' e\\ f`)[0].args).toEqual([
    "a b",
    "c d",
    "e f",
  ]);
});

test("substitutions are parsed and come first", () => {
  expect(
    cmds("echo $(aws sts get-caller-identity) `kubectl get pods`"),
  ).toEqual(["aws", "kubectl", "echo"]);
  expect(cmds('echo "$(aws s3 ls)"')).toEqual(["aws", "echo"]);
  expect(cmds("diff <(aws s3 ls) x")).toEqual(["aws", "diff"]);
  expect(cmds("echo $((1 + 2)) ${HOME}")).toEqual(["echo"]);
});

test("bash -c script is parsed", () => {
  expect(cmds(`bash -c 'aws s3 ls | head'`)).toEqual(["bash", "aws", "head"]);
  expect(cmds(`sh -lc "kubectl get pods"`)).toEqual(["sh", "kubectl"]);
});

test("heredoc body is data", () => {
  const c = `git commit -m "$(cat <<'EOF'\nfix(arbiter): never run aws sso login\nEOF\n)"`;
  expect(cmds(c)).toEqual(["cat", "git"]);
  expect(cmds("cat <<-END\n\taws s3 ls\n\tEND\npwd")).toEqual(["cat", "pwd"]);
});

test("comments are ignored", () => {
  expect(cmds("ls # aws s3 ls\npwd")).toEqual(["ls", "pwd"]);
  expect(parse("echo a#b")[0].args).toEqual(["a#b"]);
});

test("redirections are neither args nor flags", () => {
  const [c] = parse("aws s3 ls > out.txt 2>&1 < in.txt &>> log");
  expect(c.args).toEqual(["s3", "ls"]);
  expect(c.flags).toEqual([]);
});

test("bare -- ends flags and is dropped", () => {
  const [c] = parse("git checkout -- -weird");
  expect(c.flags).toEqual([]);
  expect(c.args).toEqual(["checkout", "-weird"]);
});

test("aws-vault exec is unwrapped", () => {
  const out = parse("aws-vault exec lytxread -- aws s3 ls").map(
    ({ cmd, args, wrappers }) => ({ cmd, args, wrappers }),
  );
  expect(out).toEqual([
    { cmd: "aws-vault", args: ["exec", "lytxread"], wrappers: [] },
    { cmd: "aws", args: ["s3", "ls"], wrappers: ["aws-vault"] },
  ]);
  expect(parse("aws-vault exec lytxread aws s3 ls")[1]).toMatchObject({
    cmd: "aws",
    wrappers: ["aws-vault"],
  });
  expect(cmds("aws-vault list")).toEqual(["aws-vault"]);
});

test("wrappers nest and are inherited through bash -c", () => {
  const subs = parse(`sudo -u root aws-vault exec p -- bash -c 'aws s3 ls'`);
  expect(subs.find((s) => s.cmd === "aws")!.wrappers).toEqual([
    "sudo",
    "aws-vault",
  ]);
});

test("other wrappers", () => {
  expect(parse("env FOO=1 aws s3 ls")[1]).toMatchObject({
    cmd: "aws",
    env: { FOO: "1" },
    wrappers: ["env"],
  });
  expect(parse("timeout 5 kubectl get pods")[1]).toMatchObject({
    cmd: "kubectl",
    wrappers: ["timeout"],
  });
  expect(parse("xargs -n 1 aws s3 rm")[1]).toMatchObject({
    cmd: "aws",
    args: ["s3", "rm"],
    wrappers: ["xargs"],
  });
  expect(parse("op run -- terraform apply")[1]).toMatchObject({
    cmd: "terraform",
    wrappers: ["op"],
  });
  expect(cmds("op read op://vault/item")).toEqual(["op"]);
  expect(cmds("sudo")).toEqual(["sudo"]);
});

test("subshells and reserved words", () => {
  expect(
    cmds("(cd x && aws s3 ls); if kubectl get ns; then echo ok; fi"),
  ).toEqual(["cd", "aws", "kubectl", "echo"]);
});

test("empty input and empty segments", () => {
  expect(parse("")).toEqual([]);
  expect(parse("   ")).toEqual([]);
  expect(parse(" ;; ; ")).toEqual([]);
  expect(parse("FOO=bar")).toEqual([]);
});

test("unterminated input falls back to one raw sub-command", () => {
  for (const s of [
    `echo 'x`,
    'echo "x',
    "echo $(ls",
    "echo `ls",
    "cat <<EOF\nbody",
    "cat <<EOF",
  ]) {
    expect(parse(s)).toEqual(raw(s));
  }
});

test("more wrappers: nohup, doas, exec, watch, command, builtin", () => {
  const wrapped = (s: string) =>
    parse(s).find((c) => c.cmd === "aws")?.wrappers;
  expect(wrapped("nohup aws s3 ls")).toEqual(["nohup"]);
  expect(wrapped("doas -u root aws s3 ls")).toEqual(["doas"]);
  expect(wrapped("exec -a name aws s3 ls")).toEqual(["exec"]);
  expect(wrapped("watch -n 5 aws s3 ls")).toEqual(["watch"]);
  expect(wrapped("watch 'aws s3 ls'")).toEqual(["watch"]);
  expect(wrapped("command aws s3 ls")).toEqual(["command"]);
  expect(wrapped("builtin aws s3 ls")).toEqual(["builtin"]);
  expect(cmds("command -v aws")).toEqual(["command"]);
  expect(cmds("command -V aws")).toEqual(["command"]);
});
