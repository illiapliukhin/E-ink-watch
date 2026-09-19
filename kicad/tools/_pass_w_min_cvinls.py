#!/usr/bin/env python3
"""Pass-W minimal: C_VINLS south park + strip overlapping stubs + truncate 3V3_DISP; no stitch yet."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, netnum

t = load()
dels = [
    (112.8, 105.32, 112.8, 105.4),
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    (113.0, 106.0, 113.0, 107.4),
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    print(f"del {k} ({a},{b})-({c},{d})")
t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

t = move_fp(t, "C_VINLS", 112.50, 104.50)
# C_SYS east slightly to make room
t = move_fp(t, "C_SYS", 113.50, 103.70)

d3 = netnum(t, "3V3_DISP")
# reconnect 3V3_DISP to C_LDO only (C_LDO still at 113.5,106.8)
t = add_segment(t, 111.8, 106.0, 113.5, 106.0, 0.25, "F.Cu", d3)
t = add_segment(t, 113.5, 106.0, 113.5, 106.32, 0.25, "F.Cu", d3)

# C_VINLS fanouts: PMID to island via (west then south), GND to C_PMID GND area
pm, gnd = netnum(t,"PMID"), netnum(t,"GND")
t = add_segment(t, 112.50, 104.98, 111.90, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 111.90, 104.98, 111.90, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 111.90, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 112.50, 104.02, 112.80, 104.02, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.80, 104.02, 112.80, 103.52, 0.20, "F.Cu", gnd)

# C_SYS new pads: VSYS (113.5,104.18) GND (113.5,103.22) — minimal stubs if needed later
save(t)
print("min done")
