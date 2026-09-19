#!/usr/bin/env python3
"""Replay Pass-AE KEEP edits onto Pass-AD final."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ae_sexpr_lib import *

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
# AE0: BTN1 clear of OPT
btn1 = netnum(t, "BTN1")
t, _ = del_segments_at(t, 98.0, 110.5, 98.0, 111.2, layer="B.Cu")
t, _ = del_segments_at(t, 98.0, 111.2, 107.5, 111.2, layer="B.Cu")
t, _ = del_segments_at(t, 107.5, 111.2, 107.5, 110.5, layer="B.Cu")
t = add_segment(t, 98.0, 110.5, 98.0, 111.6, 0.18, "B.Cu", btn1)
t = add_segment(t, 98.0, 111.6, 107.5, 111.6, 0.18, "B.Cu", btn1)
t = add_segment(t, 107.5, 111.6, 107.5, 110.5, 0.18, "B.Cu", btn1)

# AE0i: TP6 + CD west of R_CD GND pad
t = set_fp_at(t, "TP6", "108.5 111.0")  # final pos after power stitch
cd = netnum(t, "CD")
t, _ = del_segments_at(t, 113.5, 108.26, 113.5, 106.8, layer="F.Cu")
t, _ = del_segments_at(t, 113.5, 106.8, 110.6, 106.8, layer="F.Cu")
t = add_segment(t, 113.5, 108.26, 112.8, 108.26, 0.15, "F.Cu", cd)
t = add_segment(t, 112.8, 108.26, 112.8, 106.8, 0.15, "F.Cu", cd)
t = add_segment(t, 112.8, 106.8, 110.6, 106.8, 0.15, "F.Cu", cd)

# AE3_1c: 3V3_DISP east + C_SYS GND
d = netnum(t, "3V3_DISP"); g = netnum(t, "GND")
t = add_via(t, 116.85, 103.0, 0.45, 0.2, d)
t = add_segment(t, 116.85, 103.0, 116.85, 106.0, 0.25, "B.Cu", d)
t = add_segment(t, 116.85, 106.0, 113.0, 106.0, 0.25, "B.Cu", d)
t = add_via(t, 118.5, 103.52, 0.4, 0.2, g)
t = add_segment(t, 118.5, 103.52, 120.0, 103.52, 0.2, "B.Cu", g)
t = add_segment(t, 120.0, 103.52, 120.0, 108.0, 0.2, "B.Cu", g)
t = add_segment(t, 120.0, 108.0, 117.2, 108.0, 0.2, "B.Cu", g)

# AE9: strap L
t = add_segment(t, 83.15, 98.75, 83.15, 102.25, 0.25, "F.Cu", g)

# AE17: north 3V3
n = netnum(t, "3V3")
t = add_segment(t, 97.6, 86.35, 106.0, 86.35, 0.25, "F.Cu", n)
t = add_segment(t, 106.0, 86.35, 106.0, 87.5, 0.25, "F.Cu", n)

save(t)
print("Pass-AE keeps applied")
