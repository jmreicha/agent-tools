# AWS and network diagrams

## AWS

This follows the AWS architecture icon guidelines (the look of AWS blog diagrams). It overrides the boundary and fill rules in SKILL.md. Every AWS group is solid, even where AWS draws it dashed (Region, AZ).
- **Structure first.** Nest the official groups as AWS Cloud > Account > Region > VPC > AZ > subnet. An AWS account is always the magenta Account group, never the AWS Cloud box. A diagram of one account starts at the Account group, labeled `<name> account`, and drops the AWS Cloud level. Skip the AZ level when the source groups subnets by route-table tier (public, private, isolated), and put the AZ in each subnet line instead. An isolated tier uses the private style, labeled `(no default route)`.
  Every group uses the base style `outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=30;` plus one of:

  | Group | Add |
  |---|---|
  | AWS Cloud | `grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=light-dark(#232F3E,#D5DBDB);fillColor=none;fontColor=light-dark(#232F3E,#D5DBDB);` |
  | Account | `grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fillColor=none;fontColor=light-dark(#B81D58,#F06A9A);` |
  | Region | `grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;fontColor=light-dark(#0F6A9E,#5FB4E8);` |
  | VPC | `grIcon=mxgraph.aws4.group_vpc;strokeColor=#8C4FFF;fillColor=none;fontColor=light-dark(#7A3EF0,#B394FF);` |
  | Public subnet | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#DCEBC6;fillOpacity=40;fontColor=light-dark(#1E6B10,#A6E06A);` |
  | Private subnet | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#C9E9EE;fillOpacity=40;fontColor=light-dark(#0B5A8A,#8ED3F5);` |
  | AZ (no icon; plain style, not the base) | `fillColor=none;strokeColor=#147EBA;verticalAlign=top;fontColor=light-dark(#0F6A9E,#5FB4E8);whiteSpace=wrap;html=1;container=1;collapsible=0;` |
- Put CIDRs in group labels: `VPC 10.0.0.0/16`.
- Public and private subnet tints are deliberately close: subtly different, never contrasting.
- **Names:** a service name takes at most 2 lines and never breaks mid-word. Keep "AWS" or "Amazon" with the name. Short forms (`EKS`) are fine once the full name has appeared.

## Network

- **Direction:**
  - A topology diagram runs top to bottom: internet or WAN, then edge and firewall, then core, then sites or servers. This matches the north-south vocabulary.
  - A flow diagram runs left to right.
  - When both north-south and east-west traffic matter, draw two diagrams.
- **Links:**
  - Physical links are solid; virtual links (VPN, tunnel, peering, overlay) are dashed.
  - Each link gets one label, `medium + speed + role`: `DX 10G primary`.
  - Interface, VLAN, and IP detail goes on the link ends only, and only when the diagram is about that layer.
- **Color:** links may be colored by type, but only with a key row per color (a line sample plus `DX`, `VPN`). Never color alone.
  Line colors never reuse an AWS group or icon color (`#7AA116`, `#00A4A6`, `#147EBA`, `#8C4FFF`, `#CD2264`, or the AWS Cloud's `#232F3E`/`#D5DBDB`), so a line never blends into a border. Gray is out too: it reads as the AWS Cloud border in dark mode. Use green `light-dark(#1B7F3B,#3DDC84)`, blue `light-dark(#1F4FD1,#6E9BFF)`, amber `light-dark(#9A6200,#E8A33D)`, and red `#F62E00`, at `strokeWidth=2`. Map the source's hues onto the nearest of these.
- **Redundancy:** place pairs side by side, with the role in the label (`Primary` / `Standby`), never shown by color alone.
- **BGP:** the ASN goes in the node label (`AS64512`). Draw the session as a labeled dashed edge.
- **Detail:** network diagrams get a Brief page and a Full page (see SKILL.md). The Full page keeps resource IDs, route tables, subnet lists (AZ, CIDR, name), listeners, and SG rules under the resource they belong to (`SG: 0.0.0.0/0 TCP 443`).
- **Repeats:** on Full, list them one per line; on Brief, collapse them to a count (`VPC ×53`).
- **Size:** one diagram per site or layer. If links cross, split the diagram.
- **Placeholders:** examples use RFC 1918 / RFC 5737 addresses and private ASNs only.
