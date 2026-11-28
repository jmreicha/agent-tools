# Testing

Use `terraform test` (or `tofu test`) for module logic. Static checks catch syntax and misconfiguration, and tests prove behavior: validation rules, conditionals, and the shape of outputs.

## Test file

Tests live in `tests/<name>.tftest.hcl`. Each `run` block plans or applies the module and asserts on the result:

```hcl
mock_provider "aws" {}

variables {
  name = "billing"
}

run "rejects_an_uppercase_name" {
  command = plan

  variables {
    name = "Billing"
  }

  expect_failures = [var.name]
}

run "turns_on_versioning_by_default" {
  command = plan

  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled"
    error_message = "Versioning should be on unless the caller turns it off."
  }
}
```

- Name each `run` for the behavior it proves.
- Test a validation rule with `expect_failures`, pointing at the variable.
- Put shared inputs in a `variables` block at the top of the file, and override per run.
- Write the test first and watch it fail, with `agent-tools:testing`.

## Pick the backend for the test

| Test                                                                                | Run against                                      | Cost                    |
| ----------------------------------------------------------------------------------- | ------------------------------------------------ | ----------------------- |
| Inputs, validation, conditionals, counts, known arguments                           | `command = plan` and `mock_provider`             | Free, no network        |
| AWS behavior: computed values, set-type blocks, API defaults, how resources connect | `command = apply` against AWS Emulator           | Free, local, no account |
| What the emulator doesn't cover, or IAM and security behavior                       | `command = apply` against a real sandbox account | Real resources          |

For AWS, the emulator is the default for any test that applies. It runs the real AWS APIs locally, so a test sees the IDs, ARNs, defaults, and errors AWS would return. A mock only returns values you made up.

`command = apply` is the default when a `run` block doesn't set one. Set the command on every block, so a test never applies by accident.

Run tests against a real account only when the user names a sandbox account. `terraform test` destroys what it created at the end, but a failed run can leave resources behind, so tell the user which account to check.

<!-- vale Google.Headings = NO -->

## AWS Emulator

<!-- vale Google.Headings = YES -->

[AWS Emulator](https://github.com/aws/aws-emulator) serves the AWS APIs on `https://127.0.0.1:9297`. Each run generates its own credentials and certificate under `~/.aws/emulator/9297/`.

1. Start it. On Linux, install the package and run `aws-emulator --telemetry off`. On macOS and Windows, build its Docker image and run it, publishing the port on `127.0.0.1` only. Its [getting started guide](https://docs.aws.amazon.com/emulator/latest/userguide/getting-started.html) has both paths. The `aws-emulator` agent skill can set it up: `aws agent-toolkit add-skill --skill-name aws-emulator --region us-east-1`.
2. Point the AWS provider at it, in the shell that runs the tests. The provider reads `AWS_ENDPOINT_URL` and `AWS_CA_BUNDLE`, so the test needs no provider changes:

```bash
export AWS_ENDPOINT_URL=https://127.0.0.1:9297
export AWS_SHARED_CREDENTIALS_FILE=~/.aws/emulator/9297/emulator_credentials
export AWS_CONFIG_FILE=~/.aws/emulator/9297/config
export AWS_CA_BUNDLE=~/.aws/emulator/9297/ca.pem
export AWS_EC2_METADATA_DISABLED=true
export AWS_REGION=us-east-1
unset AWS_PROFILE AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
terraform test
```

3. Unset every variable that supplies real credentials, as in the last line. Environment credentials win over the credentials file, so a leftover key signs requests for your real account, and the emulator rejects them.

- Wrap these steps in the repo's test entry point, such as `script/test`, so CI and people run them the same way.
- Use one Region per emulator. To test two Regions, run two emulators on different ports.
- Check the emulator's fidelity scores on its [releases page](https://github.com/aws/aws-emulator/releases) for each service the module uses. A service it doesn't support yet goes to `mock_provider` or a sandbox account.
- Keep `127.0.0.1` in the endpoint, not `localhost`, so S3 requests put the bucket in the path. S3 Control requests don't reach the emulator.
- Its docs say it isn't for security testing. Don't use it to prove that a policy denies something.
- The emulated resources live only as long as the emulator process. Restart it for a clean run.

## Mocks

Use `mock_provider` for plan-only tests of module logic, where no AWS behavior is involved. It returns made-up values for computed attributes. Set the ones an assertion depends on:

```hcl
mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::billing"
    }
  }
}
```

Use `override_resource` or `override_data` inside a `run` block to fix a value for that run only. When a test needs real AWS behavior, use the emulator instead of more overrides.

## Set-type blocks

Many nested blocks are sets, and a set can't be indexed. `rule[0]` fails with "Cannot index a set value". Check the schema, then iterate:

```hcl
assert {
  condition = alltrue([
    for rule in aws_s3_bucket_server_side_encryption_configuration.this.rule :
    alltrue([for d in rule.apply_server_side_encryption_by_default : d.sse_algorithm == "aws:kms"])
  ])
  error_message = "Encryption should use KMS."
}
```

A set's members are known only after apply, so this needs `command = apply`, against the emulator.

## Beyond `terraform test`

- When the module has an `examples/` directory, run `init -backend=false` and `validate` in each example. README examples aren't run, so check their variable names against `variables.tf` by hand.
- Use Terratest only when the repo already does, or when a test must call the deployed system, such as an HTTP check against a load balancer.
