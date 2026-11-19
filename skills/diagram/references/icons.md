# Icons and logos

Anything that has an icon gets one: K8s, AWS, GCP, Azure, Cisco, network gear, users, SaaS tools.
The label goes below the icon, and icons are 60×60 (about 48×48 for K8s objects inside a boundary).
Every icon also gets `verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;aspect=fixed;`.
**People:** every user, client, or team is the same plain outline silhouette: `person("user")` for one, `person("team")` for a group (`shape=mxgraph.aws4.user` / `users`, fill `light-dark(#232F3E,#D5DBDB)`). Never use figures, avatars, or clip art (Cisco `people.*`, office people). To tell user types apart, change only the silhouette's color (blue `#2875E2`, green `#7AA116`, purple `#8C4FFF`) and give each color a key row.

Never crop, flip, rotate, or recolor an icon, except the people silhouette above and the outline sets the tile rule colors. The white inside an icon is `light-dark(#ffffff,#ffffff)`, because the CLI flips a bare `#ffffff`. A container (cluster, VPC, account) is a boundary, not an icon. Boundaries are never dashed. Put a 30×30 vendor icon next to its label.

## Library shapes (built into draw.io, so they work offline)

Look styles up in this order:
1. Styles already used in nearby `.drawio` files: `grep -ho 'style="[^"]*shape=mxgraph\.[^"]*"' <dir>/*.drawio | sort -u`
2. The drawio MCP `search_shapes` tool, if it's connected
3. The patterns below. Check real names in the app bundle, because a wrong name renders as a blank or a solid square:
   `grep -aoE 'mxgraph\.(aws4|gcp2|cisco|kubernetes)\.[a-z0-9_.]+' /Applications/draw.io.app/Contents/Resources/app.asar | sort -u | grep <term>`

| Vendor | Style |
|---|---|
| K8s | `shape=mxgraph.kubernetes.icon;prIcon=<pod\|svc\|deploy\|ing\|crd\|secret\|cm\|job\|ns\|node\|api>;fillColor=#2875E2;strokeColor=light-dark(#ffffff,#ffffff);` |
| AWS | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<service>;fillColor=<category color>;strokeColor=light-dark(#ffffff,#ffffff);` |
| AWS (legacy look) | `shape=mxgraph.aws3.<route_53\|application_load_balancer\|rds\|s3>;fillColor=<#F58536\|#F58534\|#2E73B8\|#E05243>;outlineConnect=0;` |
| EKS | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;fillColor=#ED7100;strokeColor=light-dark(#ffffff,#ffffff);` (orange, like the cluster border; never the navy productIcon) |
| GCP | `shape=mxgraph.gcp2.hexIcon;prIcon=<service>;fillColor=#5184F3;strokeColor=none;` |
| Azure | `shape=image;image=img/lib/azure2/<category>/<Service>.svg;` |
| GitHub | `shape=mxgraph.azure.github_code;fillColor=light-dark(#181717,#E6E6E6);strokeColor=none;` (never the simple-icons image) |
| Cisco | `shape=mxgraph.cisco.<category>.<device>;fillColor=#036897;strokeColor=light-dark(#ffffff,#ffffff);` (for example `routers.router`, `security.firewall`) |
| Cloudflare | `cloudflare("<product>")` in drawio_lib, then embed-icons.py, which tiles it orange on peach (the tile rule; Cloudflare's own diagrams look the same). Products are the file names in [cloudflare-docs/src/icons](https://github.com/cloudflare/cloudflare-docs/tree/production/src/icons) (`workers`, `r2`, `d1`, `kv`, `dns`, `waf`, `tunnel`, `access`, `load-balancing`…). Use `image("https://cdn.simpleicons.org/cloudflare")` for the Cloudflare boundary |

draw.io's GCP set (`gcp2`) is Google's pre-2025 style. In the current system, about 19 flagship products
(GKE, Cloud Run, BigQuery, Cloud SQL, Cloud Storage, Compute Engine…) have unique icons, and every other
service uses a category icon (Compute, Networking, Databases…). If the user wants the current look, take
the SVG from the zips at cloud.google.com/icons and embed it as a data URI.

## Brand logos (anything without a library shape)

Find one with `python3 <this skill dir>/scripts/find-logo.py <name> [--domain example.com] [--github org]`.
It tries simple-icons, CNCF artwork, the GitHub org avatar, then the vendor site's icons, and prints every working URL; the first is the pick.
It rejects rasters under 64px and flags all-black SVGs. If it finds nothing, try the vendor's press kit.

**The tile rule.** Every icon is either a library shape or a logo on the standard tile. There are no other cases.
Use the URL with `image(url)` (or `shape=image;imageAspect=0;image=<url>;`), then run
`python3 <this skill dir>/scripts/embed-icons.py <file.drawio|file.excalidraw>`. It embeds every URL so the diagram works offline, and in draw.io it puts each logo on a 64px rounded tile with fixed colors, so the logo reads the same in both themes:

| Logo | Tile | Logo color |
|---|---|---|
| One color (Okta, Helm, Argo, GitHub Actions) | its color, tinted to 10% | its own |
| One color too pale for its tint (Vault yellow) | `#232F3E` (AWS dark) | its own |
| Several colors (Honeycomb, Crossplane), or a PNG | `#F4F4F4` | its own |

An outline set with no color of its own passes its brand color as a URL suffix: `<url>#tile=<hex>` (`cloudflare()` does this).
Don't pick tile colors by hand. check-layout.py flags any image icon without the tile. The script exits non-zero if any fetch fails or a URL returns something that isn't an image.
A library icon with a dark fill (`#232F3E`) gets lightened in dark mode and its white glyph washes out. Pin it: `fillColor=light-dark(#232F3E,#232F3E)`.

If no source has a logo, use a cloud shape for an edge or CDN service and a plain box for anything else.
