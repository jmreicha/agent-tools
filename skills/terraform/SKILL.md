---
name: terraform
description: House standard for Terraform, OpenTofu, and Terragrunt, built around the ways IaC changes go wrong in production, such as recreated resources, secrets in state, oversize blast radius, and unreviewed applies. Matches the repo's existing layout, tool, and module style first. Use whenever writing, changing, reviewing, refactoring, testing, or debugging .tf, .tftest.hcl, Terragrunt files (terragrunt.hcl, root.hcl), creating modules, moving resources between addresses or state, upgrading providers, or setting up IaC checks and pipelines.
version: 2.0.0
tags: [infrastructure, terraform, opentofu, terragrunt, iac]
---

# Terraform

Write infrastructure code whose plan a reviewer can trust. The costly Terraform bugs are changes that look small in the diff and destroy, expose, or drift something in the plan. Every rule here guards against one of them.

The rules cover Terraform and OpenTofu alike. Where they differ, use the repo's binary: `terraform` or `tofu`.

## Match the repo first

Find what the repo already does before you write anything:

```bash
git ls-files | rg '\.tf$|\.tftest\.hcl$|(^|/)(terragrunt|root)\.hcl$|terragrunt\.stack\.hcl$|\.terraform\.lock\.hcl$|\.tflint\.hcl$|\.terraform-version$|\.opentofu-version$|mise\.toml$'
```

- Read `required_version`, the provider pins, and the backend, and write for those versions. A feature newer than the floor needs the floor raised first, and the user's OK.
- Use the binary the repo uses. `.opentofu-version`, a `tofu` call in CI, or `encryption` blocks mean OpenTofu.
- `terragrunt.hcl` or `root.hcl` means Terragrunt drives the runs. Follow [references/terragrunt.md](references/terragrunt.md).
- Copy the naming, file split, and module shape of the nearest existing module. The house rules in [references/code.md](references/code.md) apply only where the repo has no answer.
- When a registry module covers the resource, do what the repo does. In a repo with no pattern, offer the module once, and write raw resources unless the user picks the module.
- When you write a module of your own, model its interface on the reference set for the cloud: [terraform-aws-modules](https://github.com/terraform-aws-modules) for AWS, and [Cloud Foundation Fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/modules) for Google Cloud. Read the closest module there before you design inputs. See [references/modules.md](references/modules.md).

## Look up the schema first

Write no resource argument, block, or attribute from memory. Provider schemas change between major versions. A recalled argument fails `validate`, or passes and means something else.

- Before you write a resource or data source, look it up for the pinned provider version: `ctx7 library <provider>`, then `ctx7 docs <id> "<resource> arguments"`. Fall back to the registry page for that version.
- Check whether each nested block is a list or a set. You can't index a set with `[0]`, in code or in tests.
- When an upgrade guide exists for a provider major version bump, read it before you change the pin: `ctx7 get-upgrade-guide`.

## Never surprise the plan

Before you change anything that exists, decide what the plan should show. Then make the code produce exactly that plan.

| Failure            | Rule                                                                                                                                                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity churn     | A rename, a `count` to `for_each` switch, or a move into a module changes resource addresses, and Terraform destroys and recreates. Add a `moved` block for every changed address. Use `import` and `removed` blocks, not `state` commands. |
| Secrets in state   | State stores every argument and data source result in plain text. Keep secrets out: provider managed secrets, write-only `_wo` arguments, or `ephemeral` resources. `sensitive = true` hides output and stores the value anyway.            |
| Blast radius       | One state per environment and per lifecycle. A change to a shared root needs a plan for every consumer. Don't add resources to a root that other teams apply.                                                                               |
| Forced replacement | Check the schema for arguments that force a new resource before you change them. When replacement is the point, say so, and add `create_before_destroy` when the old one serves traffic.                                                    |
| Drift and pins     | Pin providers with `~>` and commit `.terraform.lock.hcl`. Pin modules to an exact version. Don't bump a pin in the same change as a behavior change.                                                                                        |

[references/state.md](references/state.md) has the patterns for moves, imports, removals, and state layout. [references/security.md](references/security.md) has secret handling and scanning.

## Plan, and leave the apply to a human

- Run `plan`. Never run `apply`, `destroy`, `import`, `state mv`, `state rm`, or `force-unlock`. A human runs those, from a reviewed plan.
- Save the plan you show: `terraform plan -out=tfplan`, then `terraform show -no-color tfplan`.
- Read the plan before you report it. Count adds, changes, and destroys, and name every replacement (`-/+`) and destroy. A destroy you didn't intend is a bug in your change, so fix the code. Don't explain it away.
- Without credentials or a backend, stop at `init -backend=false` and `validate`, and say the plan didn't run.
- Never write credentials, account secrets, or state into the repo, chat, or a plan file you commit.

## Readable first

A reviewer has to predict the plan from the code. Clever HCL hides what gets created, so readability beats brevity, reuse, and fewer lines.

- Write resources out. Two plain resource blocks beat one block driven by a `for_each` over a computed map.
- One function per expression, two at most. Break nested `merge(flatten([for ...]))` chains into named locals, one step each, or remove the need for them.
- Keep business logic out of `for` expressions. When a `local` needs a comment to explain what it builds, simplify it or write the result out literally.
- Put defaults in the variable's type with `optional()`, not in `main.tf`. An object variable with `optional(<type>, <default>)` attributes lets `main.tf` read `var.logging.retention_days` directly, with no `lookup()`, `try()`, or `coalesce()`.
- No `dynamic` block unless the block's count really varies by input. A fixed set of nested blocks is written out.
- Toggle a single resource or module with `lifecycle { enabled = var.enable_x }` on OpenTofu 1.11 and later, and `count = var.enable_x ? 1 : 0` on Terraform. Skip ternary chains, and `try()` calls that hide a missing value.
- When you touch hard-to-read code, offer to simplify it. Keep the plan identical, with `moved` blocks where addresses change.

## Write the code

- One resource module does one job. Compose modules in the root, and keep environment values in the root, not in the module.
- Every variable and output gets a `description` and an explicit `type`. Required inputs have no `default`. Validate inputs whose bad values would fail late, at apply time.
- Use `for_each` with stable keys for anything that might change in number.
- Keep `main.tf`, `variables.tf`, `outputs.tf`, and `versions.tf`, and split by concern when `main.tf` grows past one screen of resources.
- A comment says why: a workaround, a constraint, or a ticket. Never what a block does.

[references/code.md](references/code.md) has naming, block order, and version features. [references/modules.md](references/modules.md) has module layout, interfaces, and docs.

## Test at the cheapest level that proves it

| What you're proving                             | Check                                                        |
| ----------------------------------------------- | ------------------------------------------------------------ |
| Syntax, types, references                       | `fmt -check`, `validate`                                     |
| Lint and provider rules                         | `tflint`                                                     |
| Misconfigurations                               | `trivy config .`                                             |
| Variable validation, conditionals, output shape | `terraform test` with `command = plan` and mocks             |
| AWS behavior, computed values, set blocks       | `terraform test` with `command = apply` against AWS Emulator |

Write the failing test first with `agent-tools:testing`. For AWS, run apply tests against [AWS Emulator](https://github.com/aws/aws-emulator). It returns what AWS would, and creates nothing real. Test against a real account only when the user names a sandbox account. [references/testing.md](references/testing.md) has the test file shape, mocks, and set-type assertions.

## Check

Run these steps in order on the roots and modules you changed. Skip a tool that isn't installed, and say so. Use the repo's own wrapper, such as `script/test` or a pre-commit hook, when it has one.

1. `terraform fmt -recursive`
2. `terraform init -backend=false`, then `terraform validate`, in each changed root and module
3. `tflint --recursive`
4. `trivy config .`, then fix high and critical findings, or name each exception and why.
5. `terraform test`, when the module has tests
6. `terraform plan -out=tfplan`, when credentials and a backend are available

## Report

- The versions you wrote for, and any assumption about the backend or account.
- The plan summary: adds, changes, destroys, and every replacement by address. Say "plan not run" and why, when it didn't run.
- Each `moved`, `import`, or `removed` block, and what it prevents.
- Each check, and whether it passed, failed, or was skipped and why.
- What the human must do next, such as "apply from `tfplan` in staging first".
