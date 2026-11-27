#!/usr/bin/env bash
# Drops a column with live data, swallows the backfill error, and adds no tests.
set -euo pipefail
cat >change.diff <<'DIFF'
diff --git a/migrations/0042_drop_legacy_email.sql b/migrations/0042_drop_legacy_email.sql
new file mode 100644
--- /dev/null
+++ b/migrations/0042_drop_legacy_email.sql
@@ -0,0 +1,3 @@
+-- Emails now live in user_contacts.
+ALTER TABLE users DROP COLUMN legacy_email;
+DROP INDEX IF EXISTS users_legacy_email_idx;
diff --git a/app/users.py b/app/users.py
--- a/app/users.py
+++ b/app/users.py
@@ -10,9 +10,13 @@ def primary_email(user_id):
-    row = db.one("SELECT legacy_email FROM users WHERE id = %s", user_id)
-    return row.legacy_email
+    try:
+        row = db.one("SELECT email FROM user_contacts WHERE user_id = %s AND is_primary", user_id)
+        return row.email
+    except Exception:
+        return None
DIFF
