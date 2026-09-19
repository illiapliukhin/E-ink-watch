#!/usr/bin/env python3
"""Pass-W3: C_VINLS south-park; C_SYS by L_SYS; C_LDO home; VSYS@106.5; CD/PMIC_INT fix."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, netnum

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
    (110.6, 106.8, 112.8, 106.8),
    (110.6, 106.4, 110.6, 106.7),
    (110.6, 106.7, 110.4, 106.7),
    # old C_SYS fanouts already listed; C_SYS will move away so delete VSYS stubs to old pad
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

# ILIM via: move north-west clear of MP and of new VSYS@106.5
for oxs, oys in [("113.44", "105.35")]:
    p = rf'(\t\(via\n\t\t\(at ){re.escape(oxs)} {re.escape(oys)}(\))'
    t2, n = re.subn(p, r'\g<1>112.70 105.50\g<2>', t, count=1)
    if n:
        t = t2
        print("ILIM via -> (112.70,105.50)")

# Footprints
t = move_fp(t, "C_VINLS", 112.50, 104.50)   # PMID decouple by U2
t = move_fp(t, "C_SYS", 117.40, 103.20)     # by L_SYS VSYS pad
t = move_fp(t, "C_LDO", 113.50, 106.80)     # home — C_VINLS no longer on 3V3_DISP rail
t = move_fp(t, "C_PMID", 112.20, 103.35)

# 3V3_DISP: short stub C5 -> east to C_LDO pad2 only (x to 113.5)
d3 = netnum(t, "3V3_DISP")
t = add_segment(t, 111.8, 106.0, 113.5, 106.0, 0.25, "F.Cu", d3)
t = add_segment(t, 113.5, 106.0, 113.5, 106.32, 0.25, "F.Cu", d3)

# VSYS @ y=106.50 south of MP, clear 3V3_DISP@106.0
vs = netnum(t, "VSYS")
# from B5 (111.8,105.6) east to 112.40, south to 106.50, east to L_SYS, down to pad
t = add_segment(t, 111.80, 105.60, 112.40, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.40, 105.60, 112.40, 106.50, 0.25, "F.Cu", vs)
t = add_segment(t, 112.40, 106.50, 117.412, 106.50, 0.30, "F.Cu", vs)
t = add_segment(t, 117.412, 106.50, 117.412, 104.50, 0.30, "F.Cu", vs)
# C_SYS pad1 VSYS at (117.40, 103.68) — stub from L_SYS pad
t = add_segment(t, 117.412, 104.50, 117.40, 103.68, 0.28, "F.Cu", vs)

# CD: E2 -> y=106.95 -> x=113.3 (via) avoiding R_CD GND at x=112.8
cd = netnum(t, "CD")
t = add_segment(t, 110.6, 106.8, 110.6, 106.95, 0.20, "F.Cu", cd)
t = add_segment(t, 110.6, 106.95, 113.3, 106.95, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 106.95, 113.3, 108.41, 0.20, "F.Cu", cd)
# R_CD pad1 still needs connection from via — existing may remain

# PMIC_INT west escape
pi = netnum(t, "PMIC_INT")
t = add_segment(t, 110.6, 106.4, 110.4, 106.4, 0.15, "F.Cu", pi)

# C_VINLS fanouts: PMID pad1 (112.5,104.98) -> west toward U2 PMID / island
# GND pad2 (112.5,104.02) -> south/east GND
pm = netnum(t, "PMID")
gnd = netnum(t, "GND")
t = add_segment(t, 112.50, 104.98, 112.50, 105.20, 0.25, "F.Cu", pm)
t = add_segment(t, 112.50, 105.20, 111.40, 105.20, 0.25, "F.Cu", pm)  # toward A3/B4 row
t = add_segment(t, 111.40, 105.20, 111.40, 105.60, 0.25, "F.Cu", pm)  # to B4
t = add_segment(t, 112.50, 104.02, 112.50, 103.52, 0.25, "F.Cu", gnd)
t = add_segment(t, 112.50, 103.52, 112.68, 103.52, 0.25, "F.Cu", gnd)
t = add_segment(t, 112.68, 103.52, 112.68, 103.35, 0.25, "F.Cu", gnd)  # C_PMID GND

# C_PMID pad1 already to island via — update if pad moved
# pad1 now (111.72,103.35) — old track to (111.72,103.4); fix
t, k = del_segments_at(t, 111.35, 103.4, 111.72, 103.4)
print(f"del old C_PMID PMID stub {k}")
t = add_segment(t, 111.35, 103.35, 111.72, 103.35, 0.28, "F.Cu", pm)
t = add_segment(t, 111.35, 103.85, 111.35, 103.35, 0.28, "F.Cu", pm)

save(t)
print("W3 pocket written")
