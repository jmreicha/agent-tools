---
type: llm
weight: 3
focus: { source: file, path: architecture.drawio }
---

This is draw.io XML for an AWS app: CloudFront, then an ALB in public subnets, then ECS services web and api in private subnets, with api using RDS Postgres and ElastiCache Redis in private subnets, all in VPC prod (10.0.0.0/16) in us-east-1.

PASS if all of these hold:

- Every node in the description appears, and each one sits in the right place: the ALB in a public subnet, and web, api, RDS, and Redis in private subnets, all inside the VPC.
- Edges follow the real path: users to CloudFront, CloudFront to the ALB, the ALB to web and api, and api to RDS and Redis. There are no invented services or edges.
- Node labels are 1 to 3 words. The VPC label reads like `VPC prod (10.0.0.0/16)`, with details in parentheses.
- There are no sticky notes, and no fills used for decoration. The semitransparent fills of the AWS region, VPC, and subnet groups are standard and don't count.

FAIL if any of these is wrong.
