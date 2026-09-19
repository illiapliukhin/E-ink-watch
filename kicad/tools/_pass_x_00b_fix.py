#!/usr/bin/env python3
"""Pass-X0b: Fix X0 shorts — CD via B, PMIC_INT north-west, restore TS Pass-T spine."""
import sys, re
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()

# Remove X0 copper that shorted
for a,b,c,d in [
    (110.6, 106.4, 110.35, 106.4),
    (110.6, 106.8, 110.6, 107.00),
    (110.6, 107.00, 112.8, 107.00),
    (112.8, 107.00, 112.8, 108.26),
    (111.0, 107.30, 111.0, 107.10),
    (111.0, 107.10, 108.2, 107.10),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

cd, pi, ts = netnum(t,"CD"), netnum(t,"PMIC_INT"), netnum(t,"TS")

# Restore TS Pass-T spine @y=107.25
t = add_segment(t, 111.0, 107.25, 108.2, 107.25, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.30, 111.0, 107.25, 0.18, "F.Cu", ts)

# PMIC_INT: from D2 (110.6,106.4) go NORTH to 106.55 then WEST (away from IPRETERM @106.4 and CD @106.8)
t = add_segment(t, 110.6, 106.4, 110.6, 106.55, 0.15, "F.Cu", pi)
t = add_segment(t, 110.6, 106.55, 110.25, 106.55, 0.15, "F.Cu", pi)
# Need to reconnect to existing B path — old went to (110.4,106.7). Add via at (110.25,106.55)
t = add_via(t, 110.25, 106.55, 0.40, 0.25, pi)
# Check if B PMIC_INT exists nearby — connect on B to old via @94.2 path
# Existing: B (94.2,90.55)-(94.2,106.4) and (110.4,106.7)-(109.45,106.7) etc.
# Add B: (110.25,106.55)-(110.25,106.7)-(109.45,106.7) if that net continues
t = add_segment(t, 110.25, 106.55, 110.25, 106.70, 0.15, "B.Cu", pi)
t = add_segment(t, 110.25, 106.70, 109.45, 106.70, 0.15, "B.Cu", pi)

# CD: via near E2 then B to existing CD via @113.3,108.41 — avoid R_CD GND and TS
t = add_via(t, 110.75, 106.95, 0.40, 0.25, cd)
t = add_segment(t, 110.6, 106.8, 110.75, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 110.75, 106.8, 110.75, 106.95, 0.18, "F.Cu", cd)
t = add_segment(t, 110.75, 106.95, 113.30, 108.41, 0.20, "B.Cu", cd)

save(t)
print("X0b done")
