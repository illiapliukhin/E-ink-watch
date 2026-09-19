#!/usr/bin/env python3
"""Pass-X0: Clear latent CD↔PMIC_INT and TS↔SCL before pocket moves."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, netnum

t = load()
# CD: was (110.6,106.8)-(112.8,106.8) — sits 0.1mm from PMIC_INT end at y=106.7
# PMIC_INT: (110.6,106.4)-(110.6,106.7)-(110.4,106.7)
t, k = del_segments_at(t, 110.6, 106.8, 112.8, 106.8)
print(f"del CD east {k}")
t, k = del_segments_at(t, 110.6, 106.4, 110.6, 106.7)
print(f"del PI vert {k}")
t, k = del_segments_at(t, 110.6, 106.7, 110.4, 106.7)
print(f"del PI west {k}")

cd, pi, ts = netnum(t,"CD"), netnum(t,"PMIC_INT"), netnum(t,"TS")
# PMIC_INT: west immediately from pad D2
t = add_segment(t, 110.6, 106.4, 110.35, 106.4, 0.15, "F.Cu", pi)
# CD: south then east at y=107.00 clear of PMIC_INT and R_CD GND@107.24
t = add_segment(t, 110.6, 106.8, 110.6, 107.00, 0.18, "F.Cu", cd)
t = add_segment(t, 110.6, 107.00, 112.8, 107.00, 0.20, "F.Cu", cd)
t = add_segment(t, 112.8, 107.00, 112.8, 108.26, 0.20, "F.Cu", cd)

# TS: lower west spine 107.25→107.10 to clear R_SCL pad north edge ~107.28
t, k = del_segments_at(t, 111.0, 107.25, 108.2, 107.25)
print(f"del TS spine {k}")
# keep vertical (111,107.3)-(111,106); connect to new spine
t = add_segment(t, 111.0, 107.30, 111.0, 107.10, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.10, 108.2, 107.10, 0.18, "F.Cu", ts)

save(t)
print("X0 done")
