# State

Terraform tracks each resource by its address, such as `aws_iam_user.deploy["ci"]`. Change the address in code without telling Terraform, and the plan destroys the old object and creates a new one. Every change to an existing resource's address goes through a block in code, so the move is reviewed in the plan and replayed in every environment.

## Moving an address

Add a `moved` block for each address that changes: a rename, a `count` to `for_each` switch, or a move into or out of a module.

```hcl
# Users were keyed by list position. Keying by name means removing one user doesn't renumber the rest.
moved {
  from = aws_iam_user.deploy[0]
  to   = aws_iam_user.deploy["ci"]
}

moved {
  from = aws_iam_user.deploy[1]
  to   = aws_iam_user.deploy["release"]
}
```

- Map each old index to the key of the same object. Read the list's order from the code, or from the variable's value in that environment. When environments set the list differently, each one needs its own mapping, so ask.
- A module move is one block: `from = aws_s3_bucket.logs`, `to = module.logging.aws_s3_bucket.this`.
- A `moved` block can't use `for_each` or expressions. Write one per address.
- Keep the blocks until every environment has applied them. In a shared module, keep them for at least one major version.
- The plan should show `has moved to` and no destroy. A destroy means a mapping is wrong.

## Adopting an existing object

Use an `import` block, not `terraform import`, so the import is in the plan:

```hcl
import {
  to = aws_s3_bucket.artifacts
  id = "acme-build-artifacts"
}
```

Write the resource to match the real object. The plan after the import should show no changes, or only the changes you intend.

## Dropping a resource from management

Use a `removed` block to stop managing an object without destroying it:

```hcl
removed {
  from = aws_cloudwatch_log_group.legacy

  lifecycle {
    destroy = false
  }
}
```

## State layout

- One state per environment and per lifecycle. Networking, data stores, and apps change at different rates and carry different risk, so they don't share a state.
- Split a state when reviewers stop reading its whole plan. A plan nobody reads is an unreviewed apply.
- Pass values between states with outputs and data sources, or the orchestrator's dependency wiring, such as Terragrunt `dependency` blocks. Don't reach into another team's state with `terraform_remote_state` without their agreement.
- Use a remote backend with locking and versioning, such as S3 with `use_lockfile = true`, or GCS or azurerm. Never commit state or a `*.tfstate.backup`.
- Restrict state read access like secrets, because state holds every argument in plain text.

## What a human runs

The agent writes the blocks and runs `plan`. A human runs `apply`, and any of these when a block can't express the change:

- `terraform state mv`, `state rm`, and `state replace-provider`
- `terraform force-unlock`, after checking that no run holds the lock
- `terraform apply -replace=<address>`, for a deliberate recreate

Write the exact command in the report, with the reason it's needed.
