# Terragrunt

Terragrunt runs Terraform or OpenTofu for a tree of units. Each unit is a directory with a `terragrunt.hcl` that points at a module and sets its inputs. The rules in the main skill still apply to the modules. This file covers the wiring.

## Read the layout first

- Find the root config. Current repos use `root.hcl`, included with `find_in_parent_folders("root.hcl")`. Older ones use a root `terragrunt.hcl` and a bare `find_in_parent_folders()`. Match the repo, and don't rename the root unless asked.
- Find the shared layers: `_envcommon/` or similar folders of partial configs, and the `account.hcl`, `region.hcl`, or `env.hcl` files that units read with `read_terragrunt_config`.
- A `terragrunt.stack.hcl` means the repo generates units from stacks. Edit the stack file, not the generated units.
- Check the Terragrunt version the repo pins, in `mise.toml`, `.terragrunt-version`, or CI. The CLI changed in 0.73 and later, and newer versions refuse some older commands.

## Write a unit

```hcl
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "git::https://github.com/acme/infra-modules.git//modules/bucket?ref=v2.3.0"
}

dependency "kms" {
  config_path = "../kms"

  mock_outputs                            = { key_arn = "arn:aws:kms:us-east-1:111111111111:key/mock" }
  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
}

inputs = {
  name        = "billing-exports"
  kms_key_arn = dependency.kms.outputs.key_arn
}
```

- Pin `source` to a tag or a commit SHA with `?ref=`. A branch moves under you.
- Wire units together with `dependency` blocks, not `terraform_remote_state` or hardcoded IDs, so Terragrunt orders the runs.
- Give each `dependency` `mock_outputs` limited to `init`, `validate`, and `plan`, so a unit plans before its dependency exists and never applies with a mock value.
- Put values shared by many units in the root or an environment file once. Don't copy them into each unit.
- The root generates `backend` and `provider` blocks with `remote_state` and `generate`. Don't write those blocks in the module or the unit.

## Commands

| Task                               | Command                                    |
| ---------------------------------- | ------------------------------------------ |
| Plan one unit                      | `terragrunt plan`, in the unit's directory |
| Plan every unit below a directory  | `terragrunt run --all plan`                |
| Format HCL                         | `terragrunt hcl fmt`                       |
| Validate inputs against the module | `terragrunt hcl validate --inputs`         |
| Show the dependency order          | `terragrunt dag graph`                     |

- `run --all` replaces the deprecated `run-all`. Use the form the repo's pinned version supports.
- Plan with `run --all` only below the directory you changed, not the whole tree.
- The plan-only rule covers Terragrunt: never run `apply`, `destroy`, or `run --all apply`.
