#!/usr/bin/env bash
# An OpenTofu 1.11 stack with an always-on NAT gateway.
set -euo pipefail
printf '1.11.0\n' >.opentofu-version
cat >versions.tf <<'HCL'
terraform {
  required_version = ">= 1.11"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
HCL
cat >variables.tf <<'HCL'
variable "public_subnet_id" {
  description = "Public subnet for the NAT gateway"
  type        = string
}
HCL
cat >main.tf <<'HCL'
resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = var.public_subnet_id
}
HCL
cat >outputs.tf <<'HCL'
output "nat_gateway_id" {
  description = "NAT gateway ID"
  value       = aws_nat_gateway.this.id
}
HCL
