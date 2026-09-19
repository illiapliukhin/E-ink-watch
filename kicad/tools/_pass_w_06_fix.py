#!/usr/bin/env python3
"""Pass-W6: Fix W5 shorts — PMID escape, VSYS B jog, TS B-hop, VSYS via."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()

dels = [
    # bad PMID vertical through GND pad
    (112.50, 104.98, 112.50, 103.85),
    (112.50, 103.85, 111.35, 103.85),
    # VSYS B path
    (112.25, 105.60, 112.25, 104.50),
    (112.25, 104.50, 117.40, 104.50),
    (111.80, 105.60, 112.25, 105.60),
    # TS
    (111.0, 107.05, 108.2, 107.05),
    (111.0, 107.30, 111.0, 107.05),
    # stitch may be ok — leave
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

# Move VSYS via 112.25,105.60 → 112.55,105.55 (east of B5 path, clear ILIM B)
for oxs,oys in [("112.25","105.60"),("112.250","105.600")]:
    p = rf'(\t\(via\n\t\t\(at ){re.escape(oxs)} {re.escape(oys)}(\))'
    t2,n = re.subn(p, r'\g<1>112.55 105.55\g<2>', t, count=1)
    if n:
        t=t2; print("VSYS via -> (112.55,105.55)"); break

vs, pm, gnd, ts = [netnum(t,n) for n in ("VSYS","PMID","GND","TS")]

# PMID: west from pad1 then south around pad2
# pad1 (112.5,104.98) -> (111.90,104.98) -> (111.90,103.85) -> (111.35,103.85)
t = add_segment(t, 112.50, 104.98, 111.90, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 111.90, 104.98, 111.90, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 111.90, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)

# VSYS F to new via, B at y=103.90 (clear SW via @104.50)
t = add_segment(t, 111.80, 105.60, 112.55, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.55, 105.60, 112.55, 105.55, 0.25, "F.Cu", vs)
t = add_segment(t, 112.55, 105.55, 112.55, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 112.55, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 103.90, 117.40, 104.50, 0.30, "B.Cu", vs)

# TS: via down to B at (111.0,107.15), B west, via up — avoid SDA/SCL/GND on F
t = add_via(t, 111.00, 107.15, 0.45, 0.25, ts)
t = add_segment(t, 111.00, 107.30, 111.00, 107.15, 0.18, "F.Cu", ts)
t = add_via(t, 108.20, 107.15, 0.45, 0.25, ts)
t = add_segment(t, 111.00, 107.15, 108.20, 107.15, 0.18, "B.Cu", ts)
# reconnect west TS network if needed — old spine deleted; check if 108.2,107.25 had more

save(t)
print("W6 done")
