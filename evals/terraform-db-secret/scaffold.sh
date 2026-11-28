#!/usr/bin/env bash
# A stack with networking inputs, ready for a database.
set -euo pipefail
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
variable "vpc_id" {
  description = "VPC for the orders service"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnets for the database"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group of the orders service tasks"
  type        = string
}
HCL
printf '# Orders service stack.\n' >main.tf
