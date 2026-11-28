# Security

## Secrets

State and saved plans store every argument and every data source result in plain text. `sensitive = true` only hides the value from output. Keep secrets out of state entirely, in this order of preference:

1. **The provider manages the secret.** For RDS, set `manage_master_user_password = true`, and RDS keeps the password in Secrets Manager. Terraform never sees it.
2. **A write-only argument**, fed by an `ephemeral` resource. Write-only arguments end in `_wo` and pair with a `_wo_version` argument. Bump the version to rotate:

```hcl
ephemeral "aws_secretsmanager_secret_version" "db" {
  secret_id = var.db_secret_arn
}

resource "aws_db_instance" "this" {
  # ...
  password_wo         = ephemeral.aws_secretsmanager_secret_version.db.secret_string
  password_wo_version = 1
}
```

3. **The app reads the secret at runtime.** Terraform passes only the secret's ARN or name. The value stays out of Terraform.

These all store the secret in state. Don't use them:

- `password = var.db_password`, even with `sensitive = true`
- `random_password` feeding a normal argument
- A `data "aws_secretsmanager_secret_version"` lookup. A data source result is stored too. Use the `ephemeral` resource instead.
- A secret in a `default`, a `.tfvars` file, or an output

Check the provider schema for a `_wo` argument before you assume one exists.

## Scanning

```bash
trivy config .
```

- Run it on every change. Fix high and critical findings.
- When a finding is a deliberate exception, suppress it inline with the rule ID and a reason:

```hcl
#trivy:ignore:AVD-AWS-0089 Access logs go to the central logging account.
resource "aws_s3_bucket" "logs" {
  bucket = "acme-access-logs"
}
```

- Use `checkov -d .` when the repo already uses it. Don't add a second scanner otherwise.
- Policy as code (OPA, Sentinel, or OpenTofu and Terraform policy tools) belongs to the pipeline. Match the repo's.

## Defaults to write

| Resource kind   | Default                                                                                                                     |
| --------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Storage         | Encrypted at rest. Public access blocked (`aws_s3_bucket_public_access_block`)                                              |
| Databases       | `storage_encrypted = true`, `publicly_accessible = false`, `deletion_protection = true` in prod                             |
| Networking      | A dedicated VPC. Private subnets for data stores                                                                            |
| Security groups | Ingress from another security group, or a known CIDR. Never `0.0.0.0/0` on anything but a public load balancer's 80 and 443 |
| IAM             | Name actions and resources. No `"*"` action, and no `"*"` resource on a write action                                        |
| Logs            | A retention period on every log group                                                                                       |
