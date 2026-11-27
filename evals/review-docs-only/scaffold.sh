#!/usr/bin/env bash
set -euo pipefail
cat >change.diff <<'DIFF'
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -3,7 +3,7 @@
-Run `make tset` to run the unit tests.
+Run `make test` to run the unit tests.
DIFF
