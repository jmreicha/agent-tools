#!/usr/bin/env bash
# A diagram in someone else's style: blue fills, curved edges, Helvetica.
set -euo pipefail
cat >app.drawio <<'XML'
<mxfile host="drawio">
  <diagram id="app" name="App">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="web" value="Web" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="40" y="120" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="api" value="API" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="240" y="120" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="db" value="Postgres" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="440" y="110" width="80" height="80" as="geometry" />
        </mxCell>
        <mxCell id="e1" style="curved=1;endArrow=block;html=1;strokeColor=#6c8ebf;" edge="1" parent="1" source="web" target="api">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e2" style="curved=1;endArrow=block;html=1;strokeColor=#6c8ebf;" edge="1" parent="1" source="api" target="db">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
XML
