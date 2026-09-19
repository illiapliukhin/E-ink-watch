#!/usr/bin/env python3
"""Pass-X23: CD via-to-B immediately — clear TS vertical @x=111."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()
for a,b,c,d in [
    (110.60, 106.80, 110.85, 106.80),
    (110.85, 106.80, 110.85, 108.50),
    (110.85, 108.50, 113.30, 108.50),
    (113.30, 108.50, 113.30, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")

cd = netnum(t, "CD")
# Short F stub west of TS, via, B around
t = add_via(t, 110.45, 106.95, 0.40, 0.25, cd)
t = add_segment(t, 110.60, 106.80, 110.45, 106.80, 0.18, "F.Cu", cd)
t = add_segment(t, 110.45, 106.80, 110.45, 106.95, 0.18, "F.Cu", cd)
t = add_segment(t, 110.45, 106.95, 110.45, 108.50, 0.18, "B.Cu", cd)
t = add_segment(t, 110.45, 108.50, 113.30, 108.50, 0.20, "B.Cu", cd)
t = add_segment(t, 113.30, 108.50, 113.30, 108.41, 0.20, "B.Cu", cd)

save(t)
print("X23 done")
