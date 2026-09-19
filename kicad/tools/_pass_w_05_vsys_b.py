#!/usr/bin/env python3
"""Pass-W5: VSYS via B.Cu under congestion; clean PMID fanout; ILIM by R_ILIM; TS jog."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum, move_fp

t = load()

# Delete all current VSYS F segments we added + leftover baseline near B5
vsys_dels = [
    (111.80, 105.60, 112.50, 105.60),
    (112.50, 105.60, 112.50, 106.85),
    (112.50, 106.85, 117.412, 106.85),
    (117.412, 106.85, 117.412, 104.50),
    (117.412, 104.50, 118.00, 104.50),
    (118.00, 104.50, 118.00, 103.98),
    (112.05, 105.60, 111.80, 105.60),
    (112.05, 105.60, 112.05, 105.60),
]
for a,b,c,d in vsys_dels:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del VSYS {k} ({a},{b})-({c},{d})")

# Delete PMID fanout
for a,b,c,d in [
    (112.50, 104.98, 111.70, 104.98),
    (111.70, 104.98, 111.70, 105.60),
    (111.70, 105.60, 111.40, 105.60),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del PMID {k}")

# Delete CD path
for a,b,c,d in [
    (110.6, 106.8, 111.0, 106.8),
    (111.0, 106.8, 111.0, 106.95),
    (111.0, 106.95, 113.3, 106.95),
    (113.3, 106.95, 113.3, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del CD {k}")

# Move ILIM via to near R_ILIM (115.09,106.60) — west a bit (114.50, 106.60)
for oxs,oys in [("112.15","105.85"),("112.150","105.850")]:
    p = rf'(\t\(via\n\t\t\(at ){re.escape(oxs)} {re.escape(oys)}(\))'
    t2,n = re.subn(p, r'\g<1>114.50 106.60\g<2>', t, count=1)
    if n:
        t=t2; print("ILIM -> (114.50,106.60)"); break

# Also need ILIM F from U2 C2 (110.6,106.0) to via — check existing ILIM routing
# There was ILIM via at 110.75,106.0 — keep that; east via is for R_ILIM connection on B maybe

vs = netnum(t, "VSYS")
pm = netnum(t, "PMID")
cd = netnum(t, "CD")
gnd = netnum(t, "GND")

# VSYS: short F from B5 to via @(112.20, 105.60), B east to via @(117.412, 104.50), F to L_SYS + C_SYS
t = add_via(t, 112.20, 105.60, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.20, 105.60, 0.25, "F.Cu", vs)
t = add_via(t, 117.40, 104.50, 0.45, 0.30, vs)
t = add_segment(t, 112.20, 105.60, 117.40, 104.50, 0.30, "B.Cu", vs)  # diagonal OK? prefer manhattan
# Replace diagonal with manhattan B
# Actually delete diagonal approach — use manhattan:
# Remove the diagonal we can't easily — add manhattan instead of diagonal
# First don't add diagonal — add:
# (112.20,105.60)-(112.20,104.50)-(117.40,104.50) on B
# Wait I already would have added diagonal — fix by not adding it

save(t)  # temp — rewrite cleaner
