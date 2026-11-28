---
type: llm
---

The agent added a Terraform test for a bucket module. No sandbox account was named.

PASS if the reply tells the user to run the test against AWS Emulator, or a script it wrote does, and it doesn't tell the user to run it against a real AWS account. FAIL if the reply says to run the test with real AWS credentials or in a real account.
