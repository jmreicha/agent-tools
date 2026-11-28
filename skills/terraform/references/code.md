# Code

House rules for HCL, for repos that don't have their own. Match the repo's existing style first.

## Naming

- Use `snake_case` for resources, variables, outputs, and locals.
- Name a resource `this` when the module creates only one of that type. Otherwise name it for its role: `private`, `public`, `application_logs`.
- Don't repeat the type in the name: `aws_s3_bucket.logs`, not `aws_s3_bucket.logs_bucket`.
- Give a variable enough context to read alone: `vpc_cidr_block`, not `cidr`.
- Name booleans as a state or an action: `enable_nat_gateway`, `create_bucket`.

## Files

| File           | Holds                                                          |
| -------------- | -------------------------------------------------------------- |
| `versions.tf`  | `terraform` block: `required_version` and `required_providers` |
| `providers.tf` | Provider configuration, in a root module only                  |
| `main.tf`      | Resources and module calls                                     |
| `variables.tf` | Inputs                                                         |
| `outputs.tf`   | Outputs                                                        |
| `locals.tf`    | Locals, when there are more than a few                         |
| `moved.tf`     | `moved`, `import`, and `removed` blocks during a migration     |

Split `main.tf` by concern, such as `iam.tf` or `dns.tf`, when it grows past one screen of resources. A reusable module never configures a provider.

## Block order

Resource arguments, in this order:

1. `count` or `for_each`, then a blank line
2. Required arguments
3. Optional arguments and nested blocks
4. `tags`
5. `depends_on`, only for a dependency Terraform can't see
6. `lifecycle`

```hcl
resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public["us-east-1a"].id

  tags = var.tags

  depends_on = [aws_internet_gateway.this]

  lifecycle {
    create_before_destroy = true
  }
}
```

Variable arguments: `description`, `type`, `default`, `sensitive`, `nullable`, then `validation`.

## Readable over clever

Write the plan a reviewer can predict. When a local takes more than a moment to read, rewrite it.

Hard to read:

```hcl
locals {
  rules = { for r in flatten([for sg, cfg in var.groups : [for p in cfg.ports : { key = "${sg}-${p}", sg = sg, port = p }]]) : r.key => r }
}
```

Readable, one step per local, each named for what it holds:

```hcl
locals {
  # One entry per security group and port pair, so each rule gets a stable key.
  group_ports = flatten([
    for group, config in var.groups : [
      for port in config.ports : { group = group, port = port }
    ]
  ])

  rules_by_key = { for rule in local.group_ports : "${rule.group}-${rule.port}" => rule }
}
```

Better still, when the input can change shape: take a flat list of rules as the variable, and drop the locals.

## Variables and outputs

- Use the narrowest type: `list(string)`, `map(string)`, or an `object()` with `optional()` attributes, not `any`.
- Group related settings into one object variable when they change together, such as a `logging` object, so callers can't set half of them.
- Give every optional attribute its default in the type, with `optional()`. Then `main.tf` reads the value directly:

```hcl
variable "logging" {
  description = "Access logging for the bucket"
  type = object({
    enabled        = optional(bool, true)
    retention_days = optional(number, 90)
    prefix         = optional(string, "logs/")
  })
  default  = {}
  nullable = false
}

resource "aws_cloudwatch_log_group" "access" {
  name              = "/s3/${var.name}"
  retention_in_days = var.logging.retention_days
}
```

Without `optional()`, the same default ends up in `main.tf` as `lookup(var.logging, "retention_days", 90)` or `try(var.logging.retention_days, 90)`, repeated at every use.

- Set `nullable = false` on a variable whose default you rely on.
- Validate what would otherwise fail at apply time, such as a CIDR, a name length, or an allowed value. Cross-variable validation needs 1.9 or later.
- An output returns what a caller needs, such as IDs, ARNs, and names. Return an object or a map for a group of related values. Never return a whole resource.

## Toggles and repeats

| Case                                    | OpenTofu 1.11 and later                | Terraform                      |
| --------------------------------------- | -------------------------------------- | ------------------------------ |
| Create one resource or module, or not   | `lifecycle { enabled = var.enable_x }` | `count = var.enable_x ? 1 : 0` |
| A set of things that may grow or shrink | `for_each` over a set or map           | Same                           |
| A set of things referenced by name      | `for_each` over a map                  | Same                           |

`enabled` reads better than `count`: the resource keeps a plain address, `aws_nat_gateway.this`, with no `[0]`, and evaluates to `null` when it's off.

```hcl
resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public["us-east-1a"].id

  lifecycle {
    enabled = var.enable_nat_gateway
  }
}

output "nat_gateway_id" {
  description = "NAT gateway ID, or null when it's off"
  value       = var.enable_nat_gateway ? aws_nat_gateway.this.id : null
}
```

- `enabled` can't be combined with `count` or `for_each`, and its value must be known at plan time, not sensitive, and not null.
- Switching a resource from `count = x ? 1 : 0` to `enabled` needs no `moved` block: OpenTofu moves `[0]` to the plain address itself. A module still needs `moved { from = module.x[0]  to = module.x }`.
- Terraform has no `enabled` argument. Keep `count` there.

With `count` over a list, removing the second item renumbers every item after it, and Terraform destroys and recreates them. `for_each` keys stay put.

- Key `for_each` on values known at plan time, such as names or AZs, not resource IDs.
- Switching an existing resource from `count` to `for_each` needs a `moved` block per item. See [state.md](state.md).
- A splat (`[*]`) doesn't work on a `for_each` resource. Use `values(aws_subnet.private)[*].id`, or a `for` expression for a map.

## Versions

```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

| Pin                            | Rule                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------ |
| `required_version` in a module | A floor (`>= 1.9`), so callers aren't forced onto one version                  |
| `required_version` in a root   | The version CI runs, with `~>` or exact                                        |
| Providers                      | `~> <major>.<minor>` or `~> <major>.0`. Commit `.terraform.lock.hcl` for roots |
| Registry modules               | An exact version. Renovate bumps it                                            |
| Git modules                    | `?ref=` a tag or a commit SHA, not a branch                                    |

Run `terraform init -upgrade` only to change a pin on purpose, and in its own change.

## Features by version

Check the repo's version floor before you use one of these.

| Feature                                    | Terraform |
| ------------------------------------------ | --------- |
| `moved` blocks                             | 1.1       |
| `optional()` with defaults                 | 1.3       |
| `import` blocks                            | 1.5       |
| `terraform test`                           | 1.6       |
| `removed` blocks, `mock_provider` in tests | 1.7       |
| Provider-defined functions                 | 1.8       |
| Cross-variable validation                  | 1.9       |
| `ephemeral` resources                      | 1.10      |
| Write-only (`_wo`) arguments               | 1.11      |

OpenTofu forked at 1.5 and numbers its releases on its own. It has `ephemeral` resources and write-only arguments from 1.11, and state and plan encryption (`encryption` block), which Terraform doesn't. Check OpenTofu's docs for the version of any other feature.
