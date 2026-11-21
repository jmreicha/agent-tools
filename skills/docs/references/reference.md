# Reference pages

Modeled on the [Terraform registry](https://registry.terraform.io/browse/providers) provider docs. Use this layout for API, CLI, config, and module docs.

## Page outline

```markdown
# <Name as the reader searches for it>

<One line on what it is. Then the side effects, such as "Deleting this suspends versioning".>

## Example usage

### <Minimal scenario>

### <Advanced scenario>

## Argument reference

- `name` - (Required, forces replacement) Description. Valid values: `a`, `b`.
- `region` - (Optional) Description. Defaults to `us-east-1`.
- `config` - (Required) Configuration block. See [`config` block](#config-block).

### `config` block

## Attribute reference

## Import
```

## Entry format

- Write each entry as `` `name` - (Required | Optional, other flags) Description. ``. (Vale)
- Flags in the parentheses include: forces replacement, deprecated, sensitive, and "Required if `x` is set".
- End with the literal valid values, default, and limits. Never write `a reasonable value`. (Vale)
- Describe strings, numbers, and objects with a noun phrase. Describe booleans with a verb: "Enables versioning".
- Give each nested block its own subsection, titled with its full path, and link to it from the parent entry.
- Name examples by scenario, from minimal to advanced. Use realistic values.

## Rules

- Be complete or say what's left out. If a subset lives elsewhere, the first line says where.
- Generate the page from the code or schema when you can, such as `terraform-docs`, OpenAPI, or `--help` output. Hand-written reference drifts.
- Put a quick-lookup table before the entries when readers scan for one value.
- Only describe. If an entry says "to do this, first…", move the steps to a how-to and link it.
- Keep every entry visible. Don't hide entries in tabs or collapsed sections.
- Put warnings in the entry as a constraint, not in a callout.
