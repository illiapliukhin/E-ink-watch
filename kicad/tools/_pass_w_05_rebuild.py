#!/usr/bin/env python3
"""Pass-W5 rebuild: placement + VSYS on B + fanouts + CD/PMIC + TS jog. One shot."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, add_via, netnum

t = load()

dels = [
    (112.8, 105.32, 112.8, 105.4),
    (112.8, 103.52, 112.2, 103.52),
    (112.51, 103.5, 112.51, 102.4),
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    (113.0, 106.0, 113.0, 107.4),
    (111.8, 106.1, 112.05, 106.1),
    (112.05, 106.1, 112.05, 105.6),
    (117.412, 106.1, 111.8, 106.1),
    (117.412, 104.5, 117.412, 106.1),
    (112.05, 105.6, 111.8, 105.6),
    (110.6, 106.8, 112.8, 106.8),
    (110.6, 106.4, 110.6, 106.7),
    (110.6, 106.7, 110.4, 106.7),
    # TS west spine y=107.25 — will replace at 107.05
    (111.0, 107.25, 108.2, 107.25),
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

# ILIM east via near R_ILIM
for oxs,oys in [("113.44","105.35")]:
    p = rf'(\t\(via\n\t\t\(at ){re.escape(oxs)} {re.escape(oys)}(\))'
    t2,n = re.subn(p, r'\g<1>114.50 106.60\g<2>', t, count=1)
    if n:
        t=t2; print("ILIM via -> (114.50,106.60)")

# Placement
t = move_fp(t, "C_VINLS", 112.50, 104.50)
t = move_fp(t, "C_SYS", 118.00, 103.50)
t = move_fp(t, "C_LDO", 113.50, 106.80)
t = move_fp(t, "C_PMID", 112.20, 103.35)

vs, pm, cd, pi, d3, gnd, ts = [netnum(t,n) for n in
    ("VSYS","PMID","CD","PMIC_INT","3V3_DISP","GND","TS")]

# 3V3_DISP to C_LDO
t = add_segment(t, 111.8, 106.0, 113.5, 106.0, 0.25, "F.Cu", d3)
t = add_segment(t, 113.5, 106.0, 113.5, 106.32, 0.25, "F.Cu", d3)

# VSYS on B: via near B5, B manhattan to L_SYS via
t = add_via(t, 112.25, 105.60, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.25, 105.60, 0.25, "F.Cu", vs)
t = add_via(t, 117.40, 104.50, 0.50, 0.30, vs)
t = add_segment(t, 112.25, 105.60, 112.25, 104.50, 0.30, "B.Cu", vs)
t = add_segment(t, 112.25, 104.50, 117.40, 104.50, 0.30, "B.Cu", vs)
# F to L_SYS pad and C_SYS
t = add_segment(t, 117.40, 104.50, 117.412, 104.50, 0.30, "F.Cu", vs)
t = add_segment(t, 117.412, 104.50, 118.00, 104.50, 0.28, "F.Cu", vs)
t = add_segment(t, 118.00, 104.50, 118.00, 103.98, 0.28, "F.Cu", vs)

# C_VINLS PMID -> island via south path (below SW): (112.5,104.98)->(112.5,103.85)->(111.35,103.85)
t = add_segment(t, 112.50, 104.98, 112.50, 103.85, 0.22, "F.Cu", pm)
t = add_segment(t, 112.50, 103.85, 111.35, 103.85, 0.22, "F.Cu", pm)
# C_VINLS GND -> C_PMID GND
t = add_segment(t, 112.50, 104.02, 112.50, 103.52, 0.22, "F.Cu", gnd)
t = add_segment(t, 112.50, 103.52, 112.68, 103.52, 0.22, "F.Cu", gnd)
t = add_segment(t, 112.68, 103.52, 112.68, 103.35, 0.22, "F.Cu", gnd)

# C_PMID pad1 to island
t, k = del_segments_at(t, 111.35, 103.4, 111.72, 103.4)
t = add_segment(t, 111.35, 103.35, 111.72, 103.35, 0.28, "F.Cu", pm)
t = add_segment(t, 111.35, 103.85, 111.35, 103.35, 0.28, "F.Cu", pm)

# C_PMID island -> A3 stitch on F @ x=111.05 (Pass-W step 4)
# Path: via(111.35,103.85) -> (111.05,103.85) -> (111.05,105.20) -> A3(111.00,105.20)
# Clear SW via(111.55,104.55) and VBUS@110.6
t = add_segment(t, 111.35, 103.85, 111.05, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 111.05, 103.85, 111.05, 105.20, 0.20, "F.Cu", pm)
t = add_segment(t, 111.05, 105.20, 111.00, 105.20, 0.20, "F.Cu", pm)

# CD via east then north to CD via
t = add_segment(t, 110.6, 106.8, 111.2, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 111.2, 106.8, 111.2, 107.10, 0.18, "F.Cu", cd)
t = add_segment(t, 111.2, 107.10, 113.3, 107.10, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 107.10, 113.3, 108.41, 0.20, "F.Cu", cd)

# PMIC_INT west
t = add_segment(t, 110.6, 106.4, 110.4, 106.4, 0.15, "F.Cu", pi)

# TS spine lower
t = add_segment(t, 111.0, 107.05, 108.2, 107.05, 0.18, "F.Cu", ts)
# connect vertical TS (111,107.3)-(111,106) to new spine
t = add_segment(t, 111.0, 107.30, 111.0, 107.05, 0.18, "F.Cu", ts)

save(t)
print("W5 rebuild done")
