---
description: AWS three-tier draw.io diagram from a text description. Checks the style contract and the layout check.
tags: [diagram]
max_turns: 60
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

Make a draw.io diagram of our app and save it as architecture.drawio in this folder.

Users reach CloudFront, which forwards to an ALB in the public subnets of VPC prod (10.0.0.0/16) in us-east-1. The ALB sends traffic to two ECS Fargate services in the private subnets: web and api. The api reads and writes an RDS Postgres database and uses an ElastiCache Redis cluster, both in the private subnets.
