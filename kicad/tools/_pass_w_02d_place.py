#!/usr/bin/env python3
"""Pass-W2d: Minimal pocket — no J_STRAP_R move. Caps + ILIM via + strip + CD/PMIC_INT fix."""
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
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del ({a},{b})-({c},{d}) -> {k}")

t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

# ILIM via clear of MP: north toward U2 C2 area but east
for oxs,oys in [("113.44","105.35"),("113.440","105.350")]:
    p = rf'(\t\(via\n\t\t\(at ){re.escape(oxs)} {re.escape(oys)}(\))'
    t2, n = re.subn(p, r'\g<1>112.90 105.90\g<2>', t, count=1)
    if n:
        t = t2; print("ILIM via -> (112.90,105.90)"); break

# Caps only
t = move_fp(t, "C_SYS", 112.90, 102.50)    # north of MP
t = move_fp(t, "C_VINLS", 112.50, 104.50)  # south park
t = move_fp(t, "C_LDO", 114.20, 109.50)    # south of R_LSCTRL/SW3
t = move_fp(t, "C_PMID", 112.20, 103.35)

# Re-route CD: from E2 (110.6,106.8) east at y=106.95 then to R_CD
# Re-route PMIC_INT: from D2 (110.6,106.4) west immediately (already had path to via)
cd = netnum(t, "CD")
pi = netnum(t, "PMIC_INT")
t = add_segment(t, 110.6, 106.8, 110.6, 106.95, 0.20, "F.Cu", cd)
t = add_segment(t, 110.6, 106.95, 112.8, 106.95, 0.20, "F.Cu", cd)
t = add_segment(t, 112.8, 106.95, 112.8, 108.26, 0.20, "F.Cu", cd)
# PMIC_INT: short west from pad then keep existing B path — need via at 110.4,106.4?
# Old: (110.6,106.4)-(110.6,106.7)-(110.4,106.7) then B. Check remaining PMIC_INT
t = add_segment(t, 110.6, 106.4, 110.4, 106.4, 0.15, "F.Cu", pi)

# VSYS reconnect y=105.6 — but ILIM now at 112.9,105.9 and C_VINLS pad1 at 112.5,104.98
# Use y=105.55 east of x=113.5 only; west connection via existing B5 at 105.6
vs = netnum(t, "VSYS")
t = add_segment(t, 117.412, 104.5, 117.412, 105.55, 0.30, "F.Cu", vs)
t = add_segment(t, 117.412, 105.55, 113.60, 105.55, 0.30, "F.Cu", vs)
t = add_segment(t, 113.60, 105.55, 113.60, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 113.60, 105.60, 112.05, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.05, 105.60, 111.80, 105.60, 0.25, "F.Cu", vs)

save(t)
print("W2d done")
