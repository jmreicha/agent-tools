# AWS and network diagrams

## AWS

This follows the AWS architecture icon guidelines (the look of AWS blog diagrams). It overrides the boundary and fill rules in SKILL.md. Every AWS group is solid, even where AWS draws it dashed (Region, AZ).

- **Structure first.** Nest the official groups as AWS Cloud > Account > Region > VPC > AZ > subnet. An AWS account is always the magenta Account group. Don't use the AWS Cloud box for it. A diagram of one account starts at the Account group, labeled `Name (ID)` (`InternalServices-Prod (135330967441)`), never with the word "account" (the magenta group already says it; check-layout flags it), and drops the AWS Cloud level. Skip the AZ level when the source groups subnets by route-table tier (public, private, isolated), and put the AZ in each subnet line instead. An isolated tier uses the private style, labeled `(no default route)`.
  Every group uses the base style `outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=30;` plus one of:

  | Group                                   | Add                                                                                                                                                                      |
  | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | AWS Cloud                               | `grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=light-dark(#232F3E,#D5DBDB);fillColor=none;fontColor=light-dark(#232F3E,#D5DBDB);`                                  |
  | Account                                 | `grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fillColor=none;fontColor=light-dark(#B81D58,#F06A9A);`                                                            |
  | Region                                  | `grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;fontColor=light-dark(#0F6A9E,#5FB4E8);`                                                             |
  | VPC                                     | `grIcon=mxgraph.aws4.group_vpc;strokeColor=#8C4FFF;fillColor=none;fontColor=light-dark(#7A3EF0,#B394FF);`                                                                |
  | Public subnet                           | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#DCEBC6;fillOpacity=40;fontColor=light-dark(#1E6B10,#A6E06A);`                        |
  | Private subnet                          | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#C9E9EE;fillOpacity=40;fontColor=light-dark(#0B5A8A,#8ED3F5);`                        |
  | AZ (no icon, plain style, not the base) | `fillColor=none;strokeColor=#147EBA;verticalAlign=top;align=left;spacingLeft=10;fontColor=light-dark(#0F6A9E,#5FB4E8);whiteSpace=wrap;html=1;container=1;collapsible=0;` |

- Put CIDRs in group labels, in parens: `VPC prod (10.0.0.0/16)`.

- **Security groups:** on Network and Full pages, wrap the members of each SG in the AWS security group group (`security_group` kind: solid, softened AWS red; see palette.md), labeled `SG <name> + <name>` when a member has several. Put the port and protocol on the edges into it (`TCP 33000`, `HTTPS 443`). Pad SG boxes like the subnets around them: the checker treats both as one kind. The Network page also lists each SG's rules on its own card, below the tiers, colored to match its box: a detail table (layout.md), built with `detail_grid` and `sg_rows`: a `dir | proto | port | source / dest` table, one rule per row, inbound before outbound. Write rules as `in tcp 443 0.0.0.0/0`, `in tcp 80-33001 from k8s-traffic`, `out all 0.0.0.0/0`; `sg_rows` splits them into columns and keeps notes (`no inbound rules`) as lines above the table. The grid centers in the VPC. IAM role cards on Security use the same layout. Full doesn't repeat them, and its SG boxes show names only, not `sg-` IDs.

- **Identity:** draw one row per principal: principal (instance profile or service account) → role (`role` icon) → what it reaches. Label the first edge with how the role is assumed (`IMDS`, `IRSA`, `Pod Identity`), and the next with the actions (`s3 Get/Put`). The bottom of the Security page adds a role card per role (name, trust principal, OIDC `sub`, each policy in bold, then `action → resource` lines). Full doesn't repeat them. Policies use the `permissions` icon, not `policy` (an IoT shape).

## Network vs Security pages

- **Network** answers "what can reach what": tiers, route tables, gateways, SG boxes, ports on edges. No trust zones, no red except the SG group's own color.
- **Security** answers "who is trusted, and what's at risk", as an attack path left to right from the Internet globe or cloud:
  - AWS constructs keep their AWS groups (account, VPC, subnet, EKS), which already mark isolation. Only zones with no AWS group (the Internet, a third party edge like a CDN) get a dashed trust boundary (`boundary(kind="trust")`, `dashPattern=8 4`), and only on this page. More dashed boxes read as busy.
  - Lay it out as columns, left to right, every row a path from an outside caller to data:
    1. Internet zone: users and devices, stacked on one center line.
    2. Third party edge zone (CDN), when traffic passes through one.
    3. Account, holding the VPC (public tier with the internet-facing entry points: LBs, instances) and any cluster boundary (EKS) beside it.
    4. IAM roles column, headed `IAM roles`, one role icon per workload, on the same row as the workload that assumes it (edge labeled `IMDS`, `IRSA`).
    5. Data and secrets column, headed `Data and secrets`, each store on the row of the role that reaches it (edge labeled with the actions).
    Then the role detail cards below the columns, inside the account. Draw every workload in scope that holds a role, not just the main service, and leave stores nothing in scope reaches off the page (note them instead).
  - Red means risk only. Mark potential issues with a severity chip on the affected node (`Diagram.severity("H", 1, target)`), numbered to a `Potential issues` note (not "findings", which reads as confirmed; no author tag like "my assessment") on the right, most severe first.
  - Mark crown jewels (the sensitive data stores the user names) with `Diagram.crown(target)`.
  - Add a key for the trust line, each severity level in use, and the crown.
- Security draws the IGW in the VPC's left margin: every internet path crosses it, then fans out to the public targets. Mark the zones and that VPC with `Diagram.fixed`, since the column order and the gateway margin are deliberate.
- A potential issue on something Security doesn't draw (a subnet, a route table) puts its chip on the nearest drawn parent: its account, VPC, or group.
- Lines to a gateway point at the gateway, wherever the layout puts it (the IGW in the left margin). Lines out to vendors and other accounts go right.
- Only the Security page carries potential issues: severity chips, crowns, and the `Potential issues` note. Network and Full don't, so risk is read in one place.
- Network pages always get a `Line types` key, even with fewer than 3 symbols. Lines only: SG boxes are labeled, so they need no key row.
- Traffic lines on Brief, Node, Network, and Full use the line palette (palette.md; `INGRESS`, `EGRESS`, `ENDPOINT`, `PEER`, `APP` in drawio_lib). Security lines stay default, so red risk chips stand out.
- **Trace every path to the end, PrivateLink included.** For each outbound destination (AWS service, vendor, SaaS), check whether it goes out the IGW, through NAT, or through an endpoint:
  - `aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc>`: every endpoint, its type, subnets, SGs, and whether private DNS is on.
  - `aws ec2 describe-vpc-endpoint-services --service-names <svc> [--service-regions <region>]`: the endpoint's `PrivateDnsName` (`collector.newrelic.com`, `lytx.us4.raas-honeycomb.io`) and owner account. A match with the hostname a workload calls means that traffic rides PrivateLink.
  - The endpoint SG's inbound rules decide which subnets can use it.
  Draw each endpoint (or one endpoints card listing them) and a dashed green line on to the provider, named and outside the account, with the provider region when it's cross-region. Never write `+N services`: name every one.
- **Interface endpoints** (PrivateLink, `ecr.api`, `ecr.dkr`) with private DNS serve every subnet in the VPC their SG allows, whatever its route table. Only gateway endpoints (S3, DynamoDB) depend on the route table. Check the endpoint SG before saying a tier can't reach one.
- **Hairpin through the internet** (a node calls a public hostname that comes back in to an ALB in the same VPC, often through a CDN): draw it as two lines: egress out to the CDN, entering the CDN's side that faces the source (a short lane, not a loop around the far side), and ingress from the CDN back through the IGW. Label the egress with the hostname's protocol and port.

- Public and private subnet tints are deliberately close: subtly different, not contrasting.

- **Names:** a service name takes at most 2 lines and never breaks mid-word. Keep "AWS" or "Amazon" with the name. Short forms (`EKS`) are fine once the full name has appeared.

## Network

- **Direction:**
  - A topology diagram runs top to bottom: internet or WAN, then edge and firewall, then core, then sites or servers. This matches the north-south vocabulary.
  - A flow diagram runs left to right.
  - When both north-south and east-west traffic matter, draw two diagrams.
- **Links:**
  - Physical links are solid. Virtual links (VPN, tunnel, peering, overlay) are dashed.
  - Each link gets one label, `medium + speed + role`: `DX 10G primary`.
  - Interface, VLAN, and IP detail goes on the link ends only, and only when the diagram is about that layer.
- **Color:** links may be colored by type, but only with a key row per color (a line sample plus `DX`, `VPN`). Never color alone.
  Line colors come from [palette.md](palette.md), which never reuses a group color. Map the source's hues onto the nearest one.
- **Redundancy:** place pairs side by side, with the role in the label (`Primary` / `Standby`). Color alone doesn't show the role.
- **BGP:** the ASN goes in the node label (`AS64512`). Draw the session as a labeled dashed edge.
- **Detail:** network diagrams get a Brief page and a Full page (see SKILL.md). The Full page keeps resource IDs, route tables, subnet lists (AZ, CIDR, name), listeners, and SG rules under the resource they belong to (`SG: 0.0.0.0/0 TCP 443`).
- **Repeats:** on Full, list them one per line. On Brief, collapse them to a count (`VPC ×53`).
- **Size:** one diagram per site or layer. If links cross, split the diagram.
- **Placeholders:** examples use RFC 1918 / RFC 5737 addresses and private ASNs only.
