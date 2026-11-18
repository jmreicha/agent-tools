# AWS and network diagrams

## AWS

This follows the AWS architecture icon guidelines (the look of AWS blog diagrams). It overrides the boundary and fill rules in SKILL.md. Every AWS group is solid, even where AWS draws it dashed (Region, AZ).
- **Structure first.** Nest the official groups as AWS Cloud > Region > VPC > AZ > subnet, with at least 10px of padding inside each.
  Every group uses the base style `outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=30;` plus one of:

  | Group | Add |
  |---|---|
  | AWS Cloud | `grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=light-dark(#232F3E,#D5DBDB);fillColor=none;fontColor=light-dark(#232F3E,#D5DBDB);` |
  | Account | `grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fillColor=none;fontColor=#CD2264;` |
  | Region | `grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;fontColor=#147EBA;` |
  | VPC | `grIcon=mxgraph.aws4.group_vpc;strokeColor=#8C4FFF;fillColor=none;fontColor=#8C4FFF;` |
  | Public subnet | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;fillOpacity=40;fontColor=#248814;` |
  | Private subnet | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;fillOpacity=40;fontColor=#147EBA;` |
  | AZ (no icon; plain style, not the base) | `fillColor=none;strokeColor=#147EBA;verticalAlign=top;fontColor=#147EBA;whiteSpace=wrap;html=1;container=1;collapsible=0;` |
- Put CIDRs in group labels: `VPC 10.0.0.0/16`.
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
- **Color:** links may be colored by type, but only with a one-line text key (`blue = DX · green = VPN`). Never a color-only legend.
- **Redundancy:** place pairs side by side, with the role in the label (`Primary` / `Standby`), never shown by color alone.
- **BGP:** the ASN goes in the node label (`AS64512`). Draw the session as a labeled dashed edge.
- **Detail:** network diagrams get a Brief page and a Full page (see SKILL.md). The Full page keeps resource IDs, route tables, subnet lists (AZ, CIDR, name), listeners, and SG rules under the resource they belong to (`SG: 0.0.0.0/0 TCP 443`).
- **Repeats:** on Full, list them one per line; on Brief, collapse them to a count (`VPC ×53`).
- **Size:** one diagram per site or layer. If links cross, split the diagram.
- **Placeholders:** examples use RFC 1918 / RFC 5737 addresses and private ASNs only.
