#!/usr/bin/env bash
# A small VPC module, already applied in prod, with subnets keyed by list position.
set -euo pipefail
cat >versions.tf <<'HCL'
terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
HCL
cat >variables.tf <<'HCL'
variable "availability_zones" {
  description = "AZs for the private subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
HCL
cat >main.tf <<'HCL'
resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.this.id
  availability_zone = var.availability_zones[count.index]
  cidr_block        = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index)
}
HCL
cat >outputs.tf <<'HCL'
output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}
HCL
