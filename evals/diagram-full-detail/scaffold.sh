#!/usr/bin/env bash
# A network inventory with real-looking IDs, the kind a reviewer copies from.
set -euo pipefail
cat >inventory.md <<'MD'
# Payments network inventory (exported 2026-11-20)

- Account: Payments-Prod (418273645190), region us-east-1
- VPC payments-prod: vpc-0a1b2c3d4e5f60718, 10.40.0.0/16
- Public subnets: subnet-0f11aa22bb33cc44d (10.40.0.0/24, us-east-1a), subnet-0f55ee66ff77aa88b (10.40.1.0/24, us-east-1b)
- Private subnets: subnet-0c99dd00ee11ff223 (10.40.10.0/24, us-east-1a), subnet-0c44bb55cc66dd778 (10.40.11.0/24, us-east-1b)
- ALB payments-api-alb in the public subnets, listener HTTPS 443
- ECS service payments-api (Fargate, 4 tasks) in the private subnets, port 8443
- RDS payments-db (Postgres 16, db.r6g.large, Multi-AZ) in the private subnets, port 5432
- NAT gateway nat-07e8f9a0b1c2d3e4f in subnet-0f11aa22bb33cc44d
MD
