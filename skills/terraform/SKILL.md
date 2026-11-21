---
name: terraform-skill
description: Use when working with Terraform or OpenTofu - creating modules, writing tests (native test framework), reviewing configurations, choosing between testing approaches, debugging state issues, implementing security scanning (trivy, checkov), or making infrastructure-as-code architecture decisions
version: 1.1.0
tags: [infrastructure, terraform, iac, testing]
---

# Terraform

Write, test, and review Terraform and OpenTofu code that holds up in production. The rules come from [terraform-best-practices.com](https://www.terraform-best-practices.com/) and from running Terraform at work, so each one has a reason behind it.

## When to use this skill

- Creating new Terraform or OpenTofu configurations or modules
- Setting up testing infrastructure for IaC code
- Deciding between testing approaches (validate, plan, frameworks)
- Structuring multi environment deployments
- Reviewing or refactoring existing Terraform/OpenTofu projects
- Choosing between module patterns or state management approaches

Don't use this skill for:

- Basic Terraform or OpenTofu syntax. You already know it.
- Provider API reference. Link the provider docs instead.
- Cloud platform questions unrelated to Terraform/OpenTofu

## Core principles

### 1. Code structure

**Module Hierarchy:**

| Type                      | When to Use                                  | Scope                                           |
| ------------------------- | -------------------------------------------- | ----------------------------------------------- |
| **Resource Module**       | Single logical group of connected resources  | VPC + subnets, Security group + rules           |
| **Infrastructure Module** | Collection of resource modules for a purpose | Multiple resource modules in one region/account |
| **Composition**           | Complete infrastructure                      | Spans multiple regions/accounts                 |

**Hierarchy:** Resource → Resource Module → Infrastructure Module → Composition

**Directory Structure:**

```text
modules/            # Reusable modules
├── networking/
├── compute/
└── data/
```

**Key principle from terraform-best-practices.com:**

- Separate **environments** (prod, staging) from **modules** (reusable components)
- Use **examples/** as both documentation and integration test fixtures
- Keep modules small and focused (single responsibility)

**For detailed module architecture, see:** [Code Patterns: Module Types & Hierarchy](./code-patterns.md)

### 2. Naming conventions

**Resources:**

```hcl
# Good: Descriptive, contextual
resource "aws_instance" "web_server" { }
resource "aws_s3_bucket" "application_logs" { }

# Good: "this" for singleton resources (only one of that type)
resource "aws_vpc" "this" { }
resource "aws_security_group" "this" { }

# Avoid: Generic names for non-singletons
resource "aws_instance" "main" { }
resource "aws_s3_bucket" "bucket" { }
```

**Singleton Resources:**

Use `"this"` when your module creates only one resource of that type:

Do:

```hcl
resource "aws_vpc" "this" {}           # Module creates one VPC
resource "aws_security_group" "this" {}  # Module creates one SG
```

Don't use "this" for multiple resources:

```hcl
resource "aws_subnet" "this" {}  # If creating multiple subnets
```

Use descriptive names when creating multiple resources of the same type.

**Variables:**

```hcl
# Prefix with context when needed
var.vpc_cidr_block          # Not just "cidr"
var.database_instance_class # Not just "instance_class"
```

**Files:**

- `main.tf` - Primary resources
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `versions.tf` - Provider versions
- `data.tf` - Data sources (optional)

## Testing strategy framework

### Decision matrix: which testing approach?

| Your Situation                   | Recommended Approach  | Tools                                    | Cost     |
| -------------------------------- | --------------------- | ---------------------------------------- | -------- |
| **Quick syntax check**           | Static analysis       | `terraform validate`, `fmt`              | Free     |
| **Pre-commit validation**        | Static + lint         | `validate`, `tflint`, `trivy`, `checkov` | Free     |
| **Terraform 1.6+, simple logic** | Native test framework | Built in `terraform test`                | Free-Low |
| **Security/compliance focus**    | Policy as code        | OPA, Sentinel                            | Free     |
| **Cost-sensitive workflow**      | Mock providers (1.7+) | Native tests + mocking                   | Free     |

### Testing pyramid for infrastructure

```text
        /\
       /  \          End-to-End Tests (Expensive)
      /____\         - Full environment deployment
     /      \        - Production-like setup
    /________\
   /          \      Integration Tests (Moderate)
  /____________\     - Module testing in isolation
 /              \    - Real resources in test account
/________________\   Static Analysis (Cheap)
                     - validate, fmt, lint
                     - Security scanning
```

### Native test rules (1.6+)

**Before generating test code:**

1. **Validate schemas with Terraform MCP:**

   ```text
   Search provider docs → Get resource schema → Identify block types
   ```

2. **Choose correct command mode:**
   - `command = plan` - Fast, for input validation
   - `command = apply` - Required for computed values and set-type blocks

3. **Test set-type blocks without indexing:**
   - Cannot index with `[0]`
   - Use `for` expressions to iterate
   - Or use `command = apply` to materialize

**Common patterns:**

- S3 encryption rules: **set** (use for expressions)
- Lifecycle transitions: **set** (use for expressions)
- IAM policy statements: **set** (use for expressions)

**For detailed testing guides, see:**

- **[Testing Frameworks Guide](testing-frameworks.md)** - Deep dive into static analysis, native tests
- **[Quick Reference](quick-reference.md#testing-approach-selection)** - Decision flowchart and command cheat sheet

## Code structure standards

### Resource block ordering

**Strict ordering for consistency:**

1. `count` or `for_each` FIRST (blank line after)
2. Required attributes
3. Optional attributes
4. `tags` as last real argument
5. `depends_on` after tags, when there's a hidden dependency
6. `lifecycle` last, when you override create or destroy behavior

```hcl
# GOOD - Correct ordering
resource "aws_nat_gateway" "this" {
  count = var.create_nat_gateway ? 1 : 0

  allocation_id = aws_eip.this[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.name}-nat"
  }

  depends_on = [aws_internet_gateway.this]

  lifecycle {
    create_before_destroy = true
  }
}
```

### Variable block ordering

1. `description` (required)
2. `type`
3. `default`
4. `validation`
5. `nullable` (when setting to false)

```hcl
variable "environment" {
  description = "Environment name for resource tagging"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }

  nullable = false
}
```

**For complete structure guidelines, see:** [Code Patterns: Block Ordering & Structure](code-patterns.md#block-ordering--structure)

## `count` or `for_each`

### Quick decision guide

| Scenario                            | Use                         | Why                                 |
| ----------------------------------- | --------------------------- | ----------------------------------- |
| Boolean condition (create or don't) | `count = condition ? 1 : 0` | Simple on/off toggle                |
| Simple numeric replication          | `count = 3`                 | Fixed number of identical resources |
| Items may be reordered/removed      | `for_each = toset(list)`    | Stable resource addresses           |
| Reference by key                    | `for_each = map`            | Named access to resources           |
| Multiple named resources            | `for_each`                  | Better maintainability              |

### Common patterns

**Boolean conditions:**

```hcl
# GOOD - Boolean condition
resource "aws_nat_gateway" "this" {
  count = var.create_nat_gateway ? 1 : 0
  # ...
}
```

**Stable addressing with for_each:**

```hcl
# GOOD - Removing "us-east-1b" only affects that subnet
resource "aws_subnet" "private" {
  for_each = toset(var.availability_zones)

  availability_zone = each.key
  # ...
}

# BAD - Removing middle AZ recreates all subsequent subnets
resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  availability_zone = var.availability_zones[count.index]
  # ...
}
```

**For migration guides and detailed examples, see:** [Code Patterns: Count vs For_Each](code-patterns.md#count-vs-for_each-deep-dive)

## Locals for dependency management

**Use locals to force the correct resource deletion order:**

```hcl
# Problem: Subnets might be deleted after CIDR blocks, causing errors
# Solution: Use try() in locals to hint deletion order

locals {
  # References secondary CIDR first, falling back to VPC
  # Forces Terraform to delete subnets before CIDR association
  vpc_id = try(
    aws_vpc_ipv4_cidr_block_association.this[0].vpc_id,
    aws_vpc.this.id,
    ""
  )
}

resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_vpc_ipv4_cidr_block_association" "this" {
  count = var.add_secondary_cidr ? 1 : 0

  vpc_id     = aws_vpc.this.id
  cidr_block = "10.1.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = local.vpc_id  # Uses local, not direct reference
  cidr_block = "10.1.0.0/24"
}
```

**Why this matters:**

- Prevents deletion errors when destroying infrastructure
- Sets the dependency order without an explicit `depends_on`
- Particularly useful for VPC configurations with secondary CIDR blocks

**For detailed examples, see:** [Code Patterns: Locals for Dependency Management](code-patterns.md#locals-for-dependency-management)

## Module development

### Standard module structure

```text
my-module/
├── README.md           # Usage documentation (with example usage included)
├── main.tf             # Primary resources
├── variables.tf        # Input variables with descriptions
├── outputs.tf          # Output values
├── versions.tf         # Provider version constraints
└── tests/              # Test files
    └── unit.tftest.hcl
```

### Variable and output rules

**Variables:**

- Always include `description`
- Use explicit `type` constraints
- Give optional variables a `default`, and leave required inputs without one
- Add `validation` blocks for complex constraints
- Use `sensitive = true` for secrets

**Outputs:**

- Always include `description`
- Mark sensitive outputs with `sensitive = true`
- Consider returning objects for related values
- Document what consumers should do with each output

**For detailed module patterns, see:**

- **[Module Patterns Guide](module-patterns.md)** - Variable conventions, output design, do and don't patterns
- **[Quick Reference](quick-reference.md#common-patterns)** - Resource naming, variable naming, file organization

## Security & compliance

### Essential security checks

```bash
# Static security scanning
trivy config .
```

### Common issues to avoid

**Do:**

- Use AWS Secrets Manager / Parameter Store
- Create dedicated VPCs
- Enable encryption at rest
- Use least privilege security groups

**Don't:**

- Store secrets in variables
- Use default VPC
- Skip encryption
- Open security groups to 0.0.0.0/0

**For detailed security guidance, see:**

- **[Security & Compliance Guide](security-compliance.md)** - Trivy/Checkov integration, secrets management, state file security, compliance testing

## Version management

### Version constraint syntax

```hcl
version = "5.0.0"      # Exact (avoid - inflexible)
version = "~> 5.0"     # Recommended: 5.0.x only
version = ">= 5.0"     # Minimum (risky - breaking changes)
```

### Strategy by component

| Component          | Strategy            | Example                       |
| ------------------ | ------------------- | ----------------------------- |
| **Terraform**      | Pin minor version   | `required_version = "~> 1.9"` |
| **Providers**      | Pin major version   | `version = "~> 5.0"`          |
| **Modules (prod)** | Pin exact version   | `version = "5.1.2"`           |
| **Modules (dev)**  | Allow patch updates | `version = "~> 5.1"`          |

### Update workflow

```bash
# Lock versions initially
terraform init              # Creates .terraform.lock.hcl

# Update to latest within constraints
terraform init -upgrade     # Updates providers

# Review and test
terraform plan
```

**For detailed version management, see:** [Code Patterns: Version Management](code-patterns.md#version-management)

## Modern Terraform features (1.0+)

### Feature availability by version

| Feature                    | Version | Use Case                                     |
| -------------------------- | ------- | -------------------------------------------- |
| `try()` function           | 0.13+   | Safe fallbacks, replaces `element(concat())` |
| `nullable = false`         | 1.1+    | Prevent null values in variables             |
| `moved` blocks             | 1.1+    | Refactor without destroy/recreate            |
| `optional()` with defaults | 1.3+    | Optional object attributes                   |
| Native testing             | 1.6+    | Built in test framework                      |
| Mock providers             | 1.7+    | Cost free unit testing                       |
| Provider functions         | 1.8+    | Provider specific data transformation        |
| Cross-variable validation  | 1.9+    | Validate relationships between variables     |
| Write-only arguments       | 1.11+   | Secrets never stored in state                |

### Quick examples

```hcl
# try() - Safe fallbacks (0.13+)
output "sg_id" {
  value = try(aws_security_group.this[0].id, "")
}

# optional() - Optional attributes with defaults (1.3+)
variable "config" {
  type = object({
    name    = string
    timeout = optional(number, 300)  # Default: 300
  })
}

# Cross-variable validation (1.9+)
variable "environment" { type = string }
variable "backup_days" {
  type = number
  validation {
    condition     = var.environment == "prod" ? var.backup_days >= 7 : true
    error_message = "Production requires backup_days >= 7"
  }
}
```

**For complete patterns and examples, see:** [Code Patterns: Modern Terraform Features](code-patterns.md#modern-terraform-features-10)

## Version specific guidance

### Terraform 1.0-1.5

- No native testing framework available
- Focus on static analysis and plan validation

### Terraform 1.6+ / OpenTofu 1.6+

- **New:** Native `terraform test` / `tofu test` command
- Consider migrating from external frameworks for simple tests

### Terraform 1.7+ / OpenTofu 1.7+

- **New:** Mock providers for unit testing
- Reduce cost by mocking external dependencies
- Use real integration tests for final validation

### Terraform or OpenTofu

Both are fully supported by this skill. For licensing, governance, and feature comparison, see [Quick Reference: Terraform vs OpenTofu](quick-reference.md#terraform-or-opentofu-comparison).

## Detailed guides

This file covers what you need most of the time. Open a guide when the task goes deeper:

- **[Testing Frameworks](./testing-frameworks.md)** - In depth guide to static analysis, native tests
- **[Module Patterns](./module-patterns.md)** - Module structure, variable and output conventions, do and don't patterns
- **[Security & Compliance](./security-compliance.md)** - Trivy/Checkov integration, secrets management, compliance testing
- **[Quick Reference](./quick-reference.md)** - Command cheat sheets, decision flowcharts, troubleshooting guide
