#!/usr/bin/env python3
"""Pass-W4: Fix W3 shorts — PMID fanout, VSYS y, ILIM, C_SYS, CD."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, netnum

t = load()

# Remove bad PMID fanout to A4/SW
for a,b,c,d in [
    (112.50, 104.98, 112.50, 105.20),
    (112.50, 105.20, 111.40, 105.20),
    (111.40, 105.20, 111.40, 105.60),
    # bad VSYS
    (111.80, 105.60, 112.40, 105.60),
    (112.40, 105.60, 112.40, 106.50),
    (112.40, 106.50, 117.412, 106.50),
    (117.412, 106.50, 117.412, 104.50),
    (117.412, 104.50, 117.40, 103.68),
    # CD path
    (110.6, 106.8, 110.6, 106.95),
    (110.6, 106.95, 113.3, 106.95),
    (113.3, 106.95, 113.3, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

# ILIM via (112.70,105.50) -> (113.50, 105.20) — east, mid height; check MP west 113.4
# MP west edge 113.4 — via at 113.50 might kiss. Use (112.20, 105.85)
for oxs,oys in [("112.70","105.50"),("112.7","105.5")]:
    p = rf'(\t\(via\n\t\t\(at ){re.escape(oxs)} {re.escape(oys)}(\))'
    t2,n = re.subn(p, r'\g<1>112.15 105.85\g<2>', t, count=1)
    if n:
        t=t2; print("ILIM -> (112.15,105.85)"); break

# C_SYS further east/south from strap pad10
t = move_fp(t, "C_SYS", 118.00, 103.50)

pm = netnum(t, "PMID")
vs = netnum(t, "VSYS")
cd = netnum(t, "CD")
gnd = netnum(t, "GND")

# PMID fanout: C_VINLS.1 (112.5,104.98) -> north to B4 (111.4,105.6) via x=112.0 then west
# Avoid A4 SW at (111.4,105.2) and ILIM at (112.15,105.85)
t = add_segment(t, 112.50, 104.98, 111.70, 104.98, 0.22, "F.Cu", pm)
t = add_segment(t, 111.70, 104.98, 111.70, 105.60, 0.22, "F.Cu", pm)
t = add_segment(t, 111.70, 105.60, 111.40, 105.60, 0.22, "F.Cu", pm)  # B4

# VSYS @ y=106.85 — clear 3V3_DISP to 106.32 and R_ILIM GND@106.60
t = add_segment(t, 111.80, 105.60, 112.50, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.50, 105.60, 112.50, 106.85, 0.25, "F.Cu", vs)
t = add_segment(t, 112.50, 106.85, 117.412, 106.85, 0.30, "F.Cu", vs)
t = add_segment(t, 117.412, 106.85, 117.412, 104.50, 0.30, "F.Cu", vs)
# C_SYS pad1 at (118.00, 103.98)
t = add_segment(t, 117.412, 104.50, 118.00, 104.50, 0.28, "F.Cu", vs)
t = add_segment(t, 118.00, 104.50, 118.00, 103.98, 0.28, "F.Cu", vs)
# C_SYS GND pad2 (118.00, 103.02) — leave for zone/via later or short stub south

# CD: from E2 go east at 106.8 carefully? Pad E2 is CD. Go NE to (110.9,106.95) then east
# Avoid SDA tracks west. Vertical 0.15mm from pad may hit SDA — go east first on pad row
t = add_segment(t, 110.6, 106.8, 111.0, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 111.0, 106.8, 111.0, 106.95, 0.18, "F.Cu", cd)
t = add_segment(t, 111.0, 106.95, 113.3, 106.95, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 106.95, 113.3, 108.41, 0.20, "F.Cu", cd)

save(t)
print("W4 fixes written")
