#!/usr/bin/env bash
# A repo that already keeps its diagrams in docs/architecture.
set -euo pipefail
mkdir -p docs/architecture src
printf '# Architecture\n\n![System context](system-context.drawio.png)\n' >docs/architecture/README.md
cat >docs/architecture/system-context.drawio <<'XML'
<mxfile host="drawio"><diagram id="ctx" name="System context"><mxGraphModel><root><mxCell id="0" /><mxCell id="1" parent="0" />
<mxCell id="api" value="API" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="120" height="60" as="geometry" /></mxCell>
</root></mxGraphModel></diagram></mxfile>
XML
printf 'print("worker")\n' >src/worker.py
