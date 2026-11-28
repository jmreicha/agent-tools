#!/usr/bin/env bash
# A small bucket module with no logging inputs yet.
set -euo pipefail
cat >versions.tf <<'HCL'
terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
HCL
cat >variables.tf <<'HCL'
variable "name" {
  description = "Bucket name"
  type        = string
}
HCL
cat >main.tf <<'HCL'
resource "aws_s3_bucket" "this" {
  bucket = var.name
}
HCL
