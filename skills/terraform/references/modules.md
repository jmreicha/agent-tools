# Modules

## Kinds

| Kind            | Does                                                     | Example                            |
| --------------- | -------------------------------------------------------- | ---------------------------------- |
| Resource module | One job, built from closely tied resources               | A VPC with its subnets and routes  |
| Service module  | Composes resource modules into one product               | An app's ALB, ECS service, and DNS |
| Root            | Calls modules with one environment's values, holds state | `live/prod/orders`                 |

- A module that needs a paragraph to describe its job is two modules.
- Environment values live in the root. A module takes them as inputs, and never branches on `var.environment` to pick sizes or counts.
- A root holds no resource logic worth reusing. Move it into a module once a second root needs it.
- Don't wrap a single resource in a module unless the module adds real defaults, such as encryption and public access blocking around a bucket.

## Layout

```text
modules/<name>/
  README.md
  versions.tf
  main.tf
  variables.tf
  outputs.tf
  tests/
    <name>.tftest.hcl
```

Add an `examples/` directory only when the repo's other modules have one. Otherwise the examples live in `README.md`.

In a repo of many modules, keep each one under `modules/<name>/` and the roots under a separate tree, such as `live/` or `envs/`. A module published to a registry gets its own repo, named `terraform-<provider>-<name>`.

## Interface

The variables and outputs are the module's API. Treat a change to them like an API change:

| Change                                                                           | Kind                      | Version bump                       |
| -------------------------------------------------------------------------------- | ------------------------- | ---------------------------------- |
| Add an optional variable or a new output                                         | Additive                  | Minor                              |
| Change a default, or what a resource does by default                             | Behavior change           | Minor, and say it in the changelog |
| Rename or remove a variable or output, add a required variable, or change a type | Breaking                  | Major                              |
| Change a resource address without a `moved` block                                | Breaking, and destructive | Don't. Add the `moved` block       |

- Add a feature as an optional variable that defaults to today's behavior, so existing callers see no plan change.
- Take `tags` as a `map(string)` input and apply it to every resource that supports tags.
- Accept a `create` or `enable_<feature>` boolean only when callers need to switch the module or the feature off.

## Docs

A module's `README.md` has two parts: prose and examples you write, and an inputs and outputs reference that `terraform-docs` generates. Follow an existing module's README when the repo has one. Otherwise use this outline:

1. **What it does.** One or two sentences: what the module creates and when to use it. Add anything a caller must know, such as a required provider alias or a resource that takes 20 minutes to create.
2. **Examples, plenty of them.** Start with the smallest working call, then one example per common setup and per optional feature. Show each as plain Terraform and as a Terragrunt unit:

````markdown
## Examples

### Private bucket with logging

```hcl
module "exports" {
  source = "git::https://github.com/acme/infra-modules.git//modules/bucket?ref=v2.3.0"

  name = "billing-exports"
  logging = {
    enabled = true
    prefix  = "exports/"
  }
}
```

With Terragrunt:

```hcl
terraform {
  source = "git::https://github.com/acme/infra-modules.git//modules/bucket?ref=v2.3.0"
}

inputs = {
  name    = "billing-exports"
  logging = { enabled = true, prefix = "exports/" }
}
```
````

3. **Reference.** The generated inputs, outputs, providers, and requirements, between the `terraform-docs` markers:

```markdown
<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
```

Generate the reference with `terraform-docs`:

```bash
terraform-docs markdown table --output-file README.md --output-mode inject .
```

- Use the repo's `.terraform-docs.yml` when it has one, and its settings win. In a repo of many modules, `terraform-docs markdown table --recursive --recursive-path modules --output-file README.md .` updates every module's README.
- Run it after every change to variables or outputs, and commit the result. A README whose table doesn't match `variables.tf` is wrong.
- Don't edit between the markers by hand. The next run overwrites it.
- Write the prose and examples with `agent-tools:docs`. Pin every example `source` to a real tag, and use the module's real variable names, so each example works when copied.

## Reference modules

When you write a module, read the closest module in the reference set for its cloud, and copy its interface: input names, input shapes, defaults, and outputs. Callers who know these sets then know your module. Write the resources yourself. Call these modules only when the repo already does or the user asks.

| Cloud        | Reference                                                                                                                            | Copy                                                                                                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AWS          | [terraform-aws-modules](https://github.com/terraform-aws-modules), such as `terraform-aws-vpc`                                       | A `create_<resource>` boolean, a `tags` map applied everywhere, inputs named after the provider arguments, and outputs named `<resource>_<attribute>`, such as `vpc_id` or `db_instance_arn`                                     |
| Google Cloud | [Cloud Foundation Fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/modules), such as `modules/gcs` | Inputs that stay close to the provider resource, `project_id` and `name` up front, and IAM in the same module, through an `iam` map in `{ROLE => [MEMBERS]}` form, with `iam_bindings_additive` for roles the module doesn't own |

- Read the reference module at a released tag, not `master`.
- Copy the interface, not every feature. Add an input only when a caller needs it.
- Where a reference module disagrees with these rules, such as a deeply nested local or a `dynamic` block, keep the interface and write the body plainly.

## Registry modules

- Pin an exact version: `version = "6.0.1"`.
- Read the module's inputs for the pinned version before you call it, the same as a provider schema.
- Read its changelog before a major bump. Its upgrade notes usually include the `moved` blocks you need, or say it ships them.
