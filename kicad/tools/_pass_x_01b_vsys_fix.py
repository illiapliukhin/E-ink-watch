#!/usr/bin/env python3
"""Pass-X1b: Delete VSYS@106.1; reconnect B5↔L_SYS↔C_SYS on B/F clear of 3V3_DISP. Keep C_SYS."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()
for a,b,c,d in [
    (111.8, 106.1, 112.05, 106.1),
    (112.05, 106.1, 112.05, 105.6),
    (117.412, 106.1, 111.8, 106.1),
    (117.412, 104.5, 117.412, 106.1),
    (112.05, 105.6, 111.8, 105.6),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

vs = netnum(t, "VSYS")
# Via east of B5 clear of SW via@111.55 and VBUS@110.6 — use (112.35,105.60)
# ILIM B at y=105.35 — via annulus may kiss; try (112.50, 105.65)
t = add_via(t, 112.50, 105.65, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.50, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.50, 105.60, 112.50, 105.65, 0.25, "F.Cu", vs)
# B south then east — y=103.90 clear of SW B @104.5/104.9 and SW via @115,104.5
t = add_via(t, 117.40, 104.50, 0.50, 0.30, vs)
t = add_segment(t, 112.50, 105.65, 112.50, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 112.50, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 103.90, 117.40, 104.50, 0.30, "B.Cu", vs)
# F to L_SYS pad2 and C_SYS pad1 @(117.80,104.08)
t = add_segment(t, 117.40, 104.50, 117.412, 104.50, 0.30, "F.Cu", vs)
t = add_segment(t, 117.412, 104.50, 117.80, 104.50, 0.28, "F.Cu", vs)
t = add_segment(t, 117.80, 104.50, 117.80, 104.08, 0.28, "F.Cu", vs)

save(t)
print("X1b VSYS done")
