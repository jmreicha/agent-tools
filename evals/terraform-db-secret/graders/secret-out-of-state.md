---
type: regex
weight: 3
# Either lets RDS own the secret or uses a write-only argument, so state never holds the password.
pattern: '(?:\.tf","content"|"new_string"):"(?:[^"\\]|\\.)*(?:manage_master_user_password\s*=\s*true|password_wo\s*=)'
target: trace
---
