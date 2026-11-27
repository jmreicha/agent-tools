# Palette

One color per meaning, the same in every diagram. Group colors follow the AWS architecture icons.
Line colors never reuse a group color, so a line never blends into a border.
Every text color passes WCAG contrast in both themes, and `check-layout.py` checks it.

## Groups and boundaries

All solid. Border colors are AWS's own. The label colors are the same hues, darker in light mode and lighter in dark mode, so they stay readable.

| Element                                         | Border                                                                                         | Label                         | Fill             | Helper                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------- | ---------------- | ------------------------------ |
| AWS Cloud (several accounts)                    | `light-dark(#232F3E,#D5DBDB)`                                                                  | same                          | none             | `group(kind="cloud")`          |
| Account                                         | `#CD2264` magenta                                                                              | `light-dark(#B81D58,#F06A9A)` | none             | `group(kind="account")`        |
| Region                                          | `#00A4A6` teal                                                                                 | `light-dark(#0F6A9E,#5FB4E8)` | none             | `group(kind="region")`         |
| AZ                                              | `#147EBA` blue                                                                                 | `light-dark(#0F6A9E,#5FB4E8)` | none             | AZ style in aws-network.md     |
| VPC                                             | `#8C4FFF` purple                                                                               | `light-dark(#7A3EF0,#B394FF)` | none             | `group(kind="vpc")`            |
| Public subnet                                   | `#7AA116` green                                                                                | `light-dark(#1E6B10,#A6E06A)` | `#DCEBC6` at 40% | `group(kind="public")`         |
| Private subnet                                  | `#00A4A6` teal                                                                                 | `light-dark(#0B5A8A,#8ED3F5)` | `#C9E9EE` at 40% | `group(kind="private")`        |
| Security group                                  | `light-dark(#CF6F63,#D9776B)` softened AWS red (bright `#DD3522` competes with severity chips) | `light-dark(#A8443A,#F0958A)` | none             | `group(kind="security_group")` |
| Auto Scaling group                              | `#ED7100` orange                                                                               | `light-dark(#B35500,#FF9A3D)` | none             | `group(kind="asg")`            |
| EKS / Kubernetes cluster                        | `#ED7100` orange                                                                               | `light-dark(#B35500,#FF9A3D)` | none             | `boundary(kind="eks")`         |
| Kubernetes namespace                            | `#326CE5` K8s blue                                                                             | `light-dark(#2457C5,#7FA6F5)` | none             | `boundary(kind="namespace")`   |
| Data center, office, on-prem                    | `#7D8998` gray                                                                                 | `light-dark(#5A6573,#AEB8C4)` | none             | `group(kind="datacenter")`     |
| Anything else (SaaS, vendor cloud, environment) | default                                                                                        | default                       | none             | `boundary()`                   |

## Network lines

All lines are 2px. Hue says what kind of traffic it is, the dash says how it travels, and the arrowhead says which way.

| Interaction                                  | Color                               | Dash                                           | Ends                         |
| -------------------------------------------- | ----------------------------------- | ---------------------------------------------- | ---------------------------- |
| Internet ingress                             | green `light-dark(#1B7F3B,#3DDC84)` | solid                                          | arrow                        |
| Internet egress                              | blue `light-dark(#1F4FD1,#6E9BFF)`  | solid                                          | arrow                        |
| Private endpoint (VPC endpoint, PrivateLink) | green                               | dashed                                         | arrow                        |
| VPC peering                                  | brown `light-dark(#7A4A2A,#C49A6C)` | solid                                          | none (two-way)               |
| Transit Gateway attachment                   | gray `light-dark(#888888,#AAAAAA)`  | solid, or dashed when attached with no routing | none                         |
| VPN / IPsec tunnel                           | red `#F62E00`                       | dashed                                         | none                         |
| Direct Connect                               | default                             | solid, 3px                                     | none                         |
| BGP session                                  | default                             | dotted (`dashPattern=1 3`)                     | none, labeled with both ASNs |
| Control plane / management                   | default                             | dotted                                         | arrow                        |
| App or service call (non network diagrams)   | default                             | solid                                          | arrow                        |

- Network diagrams use no red emphasis, because their line colors already carry meaning. Mark what's new or risky with a label (`(new)`) or a note instead.
- Past about 5 line colors in one diagram, readers stop matching colors to the key. Fall back to dash patterns and edge labels.
- The key lists only the rows a diagram actually draws.

## Other colors

| Use                                               | Color                                                                                                      |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Emphasis lines and borders (not network diagrams) | `#F62E00`                                                                                                  |
| Emphasis text                                     | `light-dark(#C42500,#FF6A3D)` (`RED_TEXT`)                                                                 |
| Secondary text (a whole cell, as `fontColor`)     | `light-dark(#666666,#BBBBBB)`                                                                              |
| People                                            | `light-dark(#232F3E,#D5DBDB)`. To tell user types apart: blue `#2875E2`, green `#7AA116`, purple `#8C4FFF` |
| Icon whites                                       | `light-dark(#ffffff,#ffffff)`                                                                              |
