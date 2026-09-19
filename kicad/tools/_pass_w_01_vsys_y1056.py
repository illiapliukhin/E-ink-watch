#!/usr/bin/env python3
"""Pass-W1: VSYS spine y=106.1→105.6 (clear 3V3_DISP@106.0). Bar already deleted."""
import sys
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, add_segment, netnum

t = load()
n = netnum(t, "VSYS")
# Remove leftover VSYS stubs at y=106.1
for a,b,c,d in [
    (111.8, 106.1, 112.05, 106.1),
    (112.05, 106.1, 112.05, 105.6),
    (117.412, 104.5, 117.412, 106.1),
]:
    t, k = del_segments_at(t, a, b, c, d, layer="F.Cu")
    print(f"del ({a},{b})-({c},{d}) n={k}")

# Ensure path: L_SYS (117.412,104.5) -> (117.412,105.6) -> (112.05,105.6) -> (111.8,105.6) [B5]
# Existing: (112.05,105.6)-(111.8,105.6) may remain
t = add_segment(t, 117.412, 104.5, 117.412, 105.6, 0.30, "F.Cu", n)
t = add_segment(t, 117.412, 105.6, 112.05, 105.6, 0.30, "F.Cu", n)
# keep or add (112.05,105.6)-(111.8,105.6)
t, k = del_segments_at(t, 112.05, 105.6, 111.8, 105.6, layer="F.Cu")
print(f"refresh B5 stub del={k}")
t = add_segment(t, 112.05, 105.6, 111.8, 105.6, 0.25, "F.Cu", n)
save(t)
print("W1 VSYS @y=105.6 done")
