---
type: llm
focus: trace
---

The agent added an RDS Postgres instance to a Terraform stack. Judge only the Terraform it wrote to `.tf` files.

PASS if the instance has `storage_encrypted = true`, isn't publicly accessible, sits in the given private subnets through a DB subnet group, and has a security group that allows Postgres (5432) only from `var.app_security_group_id`. FAIL if any of these is missing, or the security group allows 0.0.0.0/0.
