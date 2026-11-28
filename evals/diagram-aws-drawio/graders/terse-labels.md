---
type: llm
focus: { source: file, path: architecture.drawio }
---

This is draw.io XML for an AWS app: CloudFront, then an ALB in public subnets, then ECS services web and api in private subnets, with api using RDS Postgres and ElastiCache Redis in private subnets, all in VPC prod (10.0.0.0/16) in us-east-1. A cell's `parent` attribute names the group that contains it.

PASS if node labels are 1 to 3 words, not counting a service-name prefix such as "Amazon" or "ECS Fargate", and the VPC label reads like `VPC prod (10.0.0.0/16)`, with details in parentheses. FAIL if a node label is a sentence, or the VPC label drops its CIDR.
