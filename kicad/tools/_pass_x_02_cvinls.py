#!/usr/bin/env python3
"""Pass-X2: C_VINLS → (112.50, 104.50); truncate 3V3_DISP; reconnect C_LDO; PMID/GND fanouts east of SW."""
import sys, re
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, netnum

t = load()

# Truncate 3V3_DISP east arms overlapping old C_VINLS
for a,b,c,d in [
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    (113.0, 106.0, 113.0, 107.4),  # B
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del 3V3_DISP {k}")

t = move_fp(t, "C_VINLS", 112.50, 104.50)

d3, pm, gnd = netnum(t,"3V3_DISP"), netnum(t,"PMID"), netnum(t,"GND")
# Reconnect 3V3_DISP to C_LDO @(113.5,106.8) pad2 @106.32
t = add_segment(t, 111.8, 106.0, 113.5, 106.0, 0.25, "F.Cu", d3)
t = add_segment(t, 113.5, 106.0, 113.5, 106.32, 0.25, "F.Cu", d3)

# C_VINLS fanouts: PMID east then south to island (clear SW via @111.55,104.55)
# pad1 (112.5,104.98) pad2 (112.5,104.02)
t = add_segment(t, 112.50, 104.98, 112.95, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 112.95, 104.98, 112.95, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 112.95, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)
# GND east then to C_PMID GND area
t = add_segment(t, 112.50, 104.02, 112.80, 104.02, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.80, 104.02, 112.80, 103.40, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.80, 103.40, 112.68, 103.40, 0.20, "F.Cu", gnd)

save(t)
print("X2 C_VINLS parked")
