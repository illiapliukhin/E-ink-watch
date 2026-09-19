#!/usr/bin/env python3
"""Replay Pass-AD KEEP edits onto Pass-AC final (session base)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ad_sexpr_lib import *

def set_fp_at(t, ref, at_str):
    import re
    prop = f'(property "Reference" "{ref}"'
    pidx = t.find(prop)
    window = t[max(0, pidx - 8000):pidx]
    m = list(re.finditer(r'\(at ([^)]+)\)', window))[-1]
    s = max(0, pidx - 8000) + m.start(1)
    e = max(0, pidx - 8000) + m.end(1)
    return t[:s] + at_str + t[e:]

t = load()

# AD1e: R_ISET rot90 north + ISET B-hop + GND F to via 112.2,102.2
t = set_fp_at(t, "R_ISET", "109.2 101.5 90")
iset = netnum(t, "ISET"); gnd = netnum(t, "GND")
t = add_via(t, 109.2, 100.99, 0.5, 0.25, iset)
t = add_segment(t, 109.2, 100.99, 108.2, 100.99, 0.15, "B.Cu", iset)
t = add_segment(t, 108.2, 100.99, 108.2, 106.0, 0.15, "B.Cu", iset)
t = add_segment(t, 108.2, 106.0, 109.5, 106.0, 0.15, "B.Cu", iset)
t = add_via(t, 109.5, 106.0, 0.5, 0.25, iset)
t = add_segment(t, 109.5, 106.0, 110.2, 106.0, 0.15, "F.Cu", iset)
t = add_segment(t, 109.2, 102.01, 111.2, 102.01, 0.2, "F.Cu", gnd)
t = add_segment(t, 111.2, 102.01, 112.2, 102.01, 0.2, "F.Cu", gnd)
t = add_segment(t, 112.2, 102.01, 112.2, 102.2, 0.2, "F.Cu", gnd)

# AD2k: R_VSYS north + VSYS B north-wrap
t = set_fp_at(t, "R_VSYS", "105.0 103.8 90")
t, _ = del_segments_at(t, 105.0, 103.675, 105.0, 103.35, layer="F.Cu")
t = add_segment(t, 105.0, 102.975, 105.0, 103.35, 0.25, "F.Cu", netnum(t, "3V3"))
vsys = netnum(t, "VSYS")
t = add_via(t, 105.0, 104.625, 0.45, 0.2, vsys)
for a, b in [((105.0,104.625),(106.8,104.625)),((106.8,104.625),(106.8,100.3)),
             ((106.8,100.3),(116.0,100.3)),((116.0,100.3),(116.0,105.6))]:
    t = add_segment(t, a[0], a[1], b[0], b[1], 0.2, "B.Cu", vsys)

# AD3o2: R_SCL nudge + ILIM via move + TS to C3
t = set_fp_at(t, "R_SCL", "112.0 107.8")
ilim = netnum(t, "ILIM")
t, _ = del_via(t, 110.9, 105.9, net=ilim)
t = add_via(t, 111.45, 105.8, 0.5, 0.25, ilim)
t, _ = del_segments_at(t, 110.6, 106.0, 110.9, 105.9, layer="F.Cu")
t = add_segment(t, 110.6, 106.0, 111.45, 105.8, 0.15, "F.Cu", ilim)
t, _ = del_segments_at(t, 110.9, 105.9, 110.3, 105.9, layer="B.Cu")
t = add_segment(t, 111.45, 105.8, 110.3, 105.8, 0.15, "B.Cu", ilim)
t = add_segment(t, 110.3, 105.8, 110.3, 105.35, 0.15, "B.Cu", ilim)
ts = netnum(t, "TS")
t = add_via(t, 108.51, 107.0, 0.4, 0.2, ts)
t = add_segment(t, 108.51, 107.0, 107.8, 107.0, 0.12, "B.Cu", ts)
t = add_segment(t, 107.8, 107.0, 107.8, 105.65, 0.12, "B.Cu", ts)
t = add_segment(t, 107.8, 105.65, 110.4, 105.65, 0.12, "B.Cu", ts)
t = add_via(t, 110.4, 105.65, 0.35, 0.15, ts)
t = add_segment(t, 110.4, 105.65, 110.4, 106.0, 0.1, "F.Cu", ts)
t = add_segment(t, 110.4, 106.0, 111.0, 106.0, 0.1, "F.Cu", ts)

# AD4b: R_SCL 3V3
t = add_segment(t, 112.51, 107.8, 114.6, 107.8, 0.2, "F.Cu", netnum(t, "3V3"))
t = add_segment(t, 114.6, 107.8, 114.6, 107.74, 0.2, "F.Cu", netnum(t, "3V3"))

save(t)
print("Pass-AD keeps applied")
