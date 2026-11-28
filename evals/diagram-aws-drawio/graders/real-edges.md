---
type: llm
weight: 2
focus: { source: file, path: architecture.drawio }
---

This is draw.io XML for an AWS app: CloudFront, then an ALB in public subnets, then ECS services web and api in private subnets, with api using RDS Postgres and ElastiCache Redis in private subnets, all in VPC prod (10.0.0.0/16) in us-east-1. A cell's `parent` attribute names the group that contains it.

PASS if the edges follow the real path: users to CloudFront, CloudFront to the ALB, the ALB to web and api, and api to RDS and Redis, with no invented services or edges. Edges inside a key or legend don't count. FAIL otherwise.
