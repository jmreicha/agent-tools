---
type: regex
pattern: "sketch=1|shadow=1|gradientColor=(?!none)|swimlane"
match: not_contains
target: { source: file, path: architecture.drawio }
---
