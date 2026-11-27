---
type: llm
weight: 3
focus: { source: file, path: pricing.py }
---

Before the refactor, `checkout_total` and `quote_total` gave 10% off at a subtotal of 100 or more (`>=`), and `invoice_total` only above 100 (`>`). So `invoice_total(100)` returned 100, and the other two returned 90.

PASS if the refactored file keeps all three public functions, the shared discount logic exists once instead of three times, and every function returns exactly what it did before for every input, including `invoice_total(100) == 100`.

FAIL if the duplication is still there, or if any function's result changed, such as `invoice_total(100)` now returning 90.
