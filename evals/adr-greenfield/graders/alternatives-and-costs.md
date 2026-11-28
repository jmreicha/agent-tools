---
type: llm
weight: 2
focus: trace
---

The user decided on Postgres over DynamoDB for the orders service, because reporting needs joins across orders, customers, and refunds. The cost is running schema migrations and sizing the instance.

Judge only the ADR file the agent wrote. PASS if it states the decision as an action, lists DynamoDB as a rejected alternative with the reason, and lists the migrations and sizing work as consequences. FAIL if any of these is missing.
