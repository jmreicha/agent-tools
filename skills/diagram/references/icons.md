# Icons and logos

Anything that has an icon gets one: K8s, AWS, GCP, Azure, Cisco, network gear, users, SaaS tools.
The label goes below the icon, and icons are 60×60 (about 48×48 for K8s objects inside a boundary).
Every icon also gets `verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;aspect=fixed;`.
Never crop, flip, rotate, or recolor an icon. A container (cluster, VPC, account) is a boundary, not an icon. Accounts and VPCs are never dashed. Put a 30×30 vendor icon next to its label.

## Library shapes (built into draw.io, so they work offline)

Look styles up in this order:
1. Styles already used in nearby `.drawio` files: `grep -ho 'style="[^"]*shape=mxgraph\.[^"]*"' <dir>/*.drawio | sort -u`
2. The drawio MCP `search_shapes` tool, if it's connected
3. The patterns below. Check real names in the app bundle, because a wrong name renders as a blank or a solid square:
   `grep -aoE 'mxgraph\.(aws4|gcp2|cisco|kubernetes)\.[a-z0-9_.]+' /Applications/draw.io.app/Contents/Resources/app.asar | sort -u | grep <term>`

| Vendor | Style |
|---|---|
| K8s | `shape=mxgraph.kubernetes.icon;prIcon=<pod\|svc\|deploy\|ing\|crd\|secret\|cm\|job\|ns\|node\|api>;fillColor=#2875E2;strokeColor=#ffffff;` |
| AWS | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<service>;fillColor=<category color>;strokeColor=#ffffff;` |
| AWS (legacy look) | `shape=mxgraph.aws3.<route_53\|application_load_balancer\|rds\|s3>;fillColor=<#F58536\|#F58534\|#2E73B8\|#E05243>;outlineConnect=0;` |
| EKS | `shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.eks;fillColor=#232F3E;strokeColor=#ffffff;` |
| GCP | `shape=mxgraph.gcp2.hexIcon;prIcon=<service>;fillColor=#5184F3;strokeColor=none;` |
| Azure | `shape=image;image=img/lib/azure2/<category>/<Service>.svg;` |
| Cisco | `shape=mxgraph.cisco.<category>.<device>;fillColor=#036897;strokeColor=#ffffff;` (for example `routers.router`, `security.firewall`, `people.man_woman`) |

draw.io's GCP set (`gcp2`) is Google's pre-2025 style. In the current system, about 19 flagship products
(GKE, Cloud Run, BigQuery, Cloud SQL, Cloud Storage, Compute Engine…) have unique icons, and every other
service uses a category icon (Compute, Networking, Databases…). If the user wants the current look, take
the SVG from the zips at cloud.google.com/icons and embed it as a data URI.

## Brand logos (anything without a library shape)

Try these sources in order. Check each URL first with `curl -sL -o /dev/null -w '%{http_code}'`:
1. `https://cdn.simpleicons.org/<slug>` (`argo`, `terraform`, `github`, `pagerduty`, `cloudflare`)
2. `https://raw.githubusercontent.com/cncf/artwork/main/projects/<name>/icon/color/<name>-icon-color.svg` (for example `crossplane`, `opentelemetry`)
3. `https://github.com/<org>.png?size=128` (for example `honeycombio`)
4. the vendor's press kit, found by web search

Use the URL as `shape=image;imageAspect=0;image=<url>;`, then embed every URL so the diagram works offline:
`python3 <this skill dir>/scripts/embed-icons.py <file.drawio|file.excalidraw>`
The script exits non-zero if any fetch fails or a URL returns something that isn't an image.
If no source has a logo, use a cloud shape for an edge or CDN service and a plain box for anything else.
