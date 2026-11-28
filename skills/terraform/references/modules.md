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
  examples/
    basic/          # The smallest working call, also a test fixture
    complete/       # Every optional feature turned on
  tests/
    <name>.tftest.hcl
```

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

Generate the inputs and outputs table with `terraform-docs`, between its markers in `README.md`. Write the rest by hand with `agent-tools:docs`: what the module does, one usage example, and anything a caller must know, such as a required provider alias or a resource that takes 20 minutes to create.

```bash
terraform-docs markdown table --output-file README.md --output-mode inject .
```

Don't edit the generated table by hand. The next run overwrites it.

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
