#!/usr/bin/env bash
# Someone else's diagram: grey cards, Verdana, a key for two line types, and a muted label color.
set -euo pipefail
N='rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#999999;fontFamily=Verdana;'
SYNC='endArrow=classic;html=1;strokeColor=#333333;strokeWidth=2;'
ASYNC='endArrow=open;html=1;strokeColor=#333333;strokeWidth=2;dashed=1;'
K='text;html=1;align=left;verticalAlign=middle;fontFamily=Verdana;fontSize=10;fontColor=#999999;'
cat >orders.drawio <<XML
<mxfile host="drawio">
  <diagram id="orders" name="Orders">
    <mxGraphModel dx="900" dy="600" grid="1" gridSize="10">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="shop" value="Shop" style="$N" vertex="1" parent="1"><mxGeometry x="40" y="80" width="120" height="60" as="geometry" /></mxCell>
        <mxCell id="orders" value="Orders service" style="$N" vertex="1" parent="1"><mxGeometry x="240" y="80" width="120" height="60" as="geometry" /></mxCell>
        <mxCell id="db" value="Orders DB" style="$N" vertex="1" parent="1"><mxGeometry x="440" y="80" width="120" height="60" as="geometry" /></mxCell>
        <mxCell id="mail" value="Mailer" style="$N" vertex="1" parent="1"><mxGeometry x="240" y="220" width="120" height="60" as="geometry" /></mxCell>
        <mxCell id="e1" style="$SYNC" edge="1" parent="1" source="shop" target="orders"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e2" style="$SYNC" edge="1" parent="1" source="orders" target="db"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e3" style="$ASYNC" edge="1" parent="1" source="orders" target="mail"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="key-title" value="Key" style="${K}fontStyle=1;" vertex="1" parent="1"><mxGeometry x="440" y="200" width="160" height="20" as="geometry" /></mxCell>
        <mxCell id="key-sync-line" style="$SYNC" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="440" y="235" as="sourcePoint" /><mxPoint x="480" y="235" as="targetPoint" /></mxGeometry></mxCell>
        <mxCell id="key-sync" value="Request" style="$K" vertex="1" parent="1"><mxGeometry x="490" y="225" width="110" height="20" as="geometry" /></mxCell>
        <mxCell id="key-async-line" style="$ASYNC" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="440" y="260" as="sourcePoint" /><mxPoint x="480" y="260" as="targetPoint" /></mxGeometry></mxCell>
        <mxCell id="key-async" value="Event" style="$K" vertex="1" parent="1"><mxGeometry x="490" y="250" width="110" height="20" as="geometry" /></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
XML
