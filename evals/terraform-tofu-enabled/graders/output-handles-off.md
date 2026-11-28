---
type: regex
# With enabled = false the resource is null, so the output must guard the .id read.
pattern: 'aws_nat_gateway\.this\.id\s*:\s*null|aws_nat_gateway\.this\s*(==|!=)\s*null|try\(aws_nat_gateway\.this'
target: { source: file, path: outputs.tf }
---
