---
type: llm
weight: 2
focus: { source: file, path: architecture.drawio }
---

This is draw.io XML for an AWS app: CloudFront, then an ALB in public subnets, then ECS services web and api in private subnets, with api using RDS Postgres and ElastiCache Redis in private subnets, all in VPC prod (10.0.0.0/16) in us-east-1. A cell's `parent` attribute names the group that contains it.

PASS if every node in the description appears and sits in the right group: the ALB in a public subnet, and web, api, RDS, and Redis in private subnets, all inside the VPC, inside us-east-1. CloudFront and users may sit outside the region. FAIL if a node is missing or in the wrong group.
