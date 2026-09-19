#!/usr/bin/env python3
"""Pass-W10: Atomic pocket — C_SYS@L_SYS, C_VINLS south, kill VSYS@106.1 & 3V3_DISP overlap, reconnect, stitch."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, add_via, netnum

t = load()

# Deletes first
dels = [
    (112.8, 105.32, 112.8, 105.4),
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    (113.0, 106.0, 113.0, 107.4),
    (111.8, 106.1, 112.05, 106.1),
    (112.05, 106.1, 112.05, 105.6),
    (117.412, 106.1, 111.8, 106.1),
    (117.412, 104.5, 117.412, 106.1),
    (112.05, 105.6, 111.8, 105.6),
    (112.8, 103.52, 112.2, 103.52),
    (112.51, 103.5, 112.51, 102.4),
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")
t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

t = move_fp(t, "C_SYS", 117.50, 103.50)
t = move_fp(t, "C_VINLS", 112.50, 104.50)
# C_LDO stays; C_PMID slight nudge
t = move_fp(t, "C_PMID", 112.20, 103.35)

vs, pm, d3, gnd = [netnum(t,n) for n in ("VSYS","PMID","3V3_DISP","GND")]

# 3V3_DISP reconnect to C_LDO
t = add_segment(t, 111.8, 106.0, 113.5, 106.0, 0.25, "F.Cu", d3)
t = add_segment(t, 113.5, 106.0, 113.5, 106.32, 0.25, "F.Cu", d3)

# VSYS: B5 to via east, B under to L_SYS (avoid MP and SW)
t = add_via(t, 112.30, 105.60, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.30, 105.60, 0.25, "F.Cu", vs)
t = add_via(t, 117.40, 104.50, 0.50, 0.30, vs)
t = add_segment(t, 112.30, 105.60, 112.30, 103.80, 0.30, "B.Cu", vs)
t = add_segment(t, 112.30, 103.80, 117.40, 103.80, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 103.80, 117.40, 104.50, 0.30, "B.Cu", vs)
# C_SYS pad1 VSYS @(117.50, 103.98)
t = add_segment(t, 117.40, 104.50, 117.50, 104.50, 0.28, "F.Cu", vs)
t = add_segment(t, 117.50, 104.50, 117.50, 103.98, 0.28, "F.Cu", vs)
# C_SYS GND @(117.50, 103.02) — stub toward board
t = add_segment(t, 117.50, 103.02, 117.50, 102.50, 0.25, "F.Cu", gnd)

# C_VINLS PMID to island (west then south — clear SW via)
t = add_segment(t, 112.50, 104.98, 111.85, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 111.85, 104.98, 111.85, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 111.85, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)
# C_VINLS GND
t = add_segment(t, 112.50, 104.02, 112.70, 104.02, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.70, 104.02, 112.70, 103.35, 0.20, "F.Cu", gnd)

# C_PMID pad1 to island
t, k = del_segments_at(t, 111.35, 103.4, 111.72, 103.4)
t = add_segment(t, 111.35, 103.35, 111.72, 103.35, 0.28, "F.Cu", pm)
t = add_segment(t, 111.35, 103.85, 111.35, 103.35, 0.28, "F.Cu", pm)

# Island → A3 stitch @x=111.05
t = add_segment(t, 111.35, 103.85, 111.05, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 111.05, 103.85, 111.05, 105.20, 0.20, "F.Cu", pm)
t = add_segment(t, 111.05, 105.20, 111.00, 105.20, 0.20, "F.Cu", pm)

save(t)
print("W10 atomic written")
