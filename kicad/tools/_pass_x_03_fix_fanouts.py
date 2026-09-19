#!/usr/bin/env python3
"""Pass-X3: Fix GND↔PMID fanouts, VSYS via vs 3V3_DISP, CD/PMIC_INT, TS↔SCL."""
import sys, re
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()

def del_via_xy(t, x, y):
    lines = t.splitlines(keepends=True)
    out = []; i = 0; n = 0
    while i < len(lines):
        if lines[i] == '\t(via\n' and i+1 < len(lines):
            m = re.match(r'\s*\(at ([0-9.]+) ([0-9.]+)\)', lines[i+1])
            if m and abs(float(m.group(1))-x)<0.01 and abs(float(m.group(2))-y)<0.01:
                i += 1
                while i < len(lines) and lines[i] not in ('\t)\n', '\t)'):
                    i += 1
                if i < len(lines): i += 1
                n += 1
                continue
        out.append(lines[i]); i += 1
    return ''.join(out), n

# --- PMID/GND fanouts redo ---
for a,b,c,d in [
    (112.50, 104.98, 112.95, 104.98),
    (112.95, 104.98, 112.95, 103.85),
    (112.95, 103.85, 111.35, 103.85),
    (112.50, 104.02, 112.80, 104.02),
    (112.80, 104.02, 112.80, 103.40),
    (112.80, 103.40, 112.68, 103.40),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del fan {k}")

pm, gnd = netnum(t,"PMID"), netnum(t,"GND")
# PMID: east to 113.30 then south (clear of pad2 and SW)
t = add_segment(t, 112.50, 104.98, 113.30, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 113.30, 104.98, 113.30, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 113.30, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)
# GND: west then south (away from PMID east path)
t = add_segment(t, 112.50, 104.02, 112.20, 104.02, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.20, 104.02, 112.20, 103.40, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.20, 103.40, 112.68, 103.40, 0.20, "F.Cu", gnd)

# --- VSYS via move clear of 3V3_DISP @y=106 ---
for a,b,c,d in [
    (111.80, 105.60, 112.80, 105.60),
    (112.80, 105.60, 112.80, 105.95),
    (112.80, 105.95, 112.80, 103.90),
    (112.80, 103.90, 117.40, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del vsys {k}")
t, n = del_via_xy(t, 112.80, 105.95)
print(f"del VSYS via {n}")

vs = netnum(t, "VSYS")
# Via at (113.60, 105.90): east of C_VINLS, south of 3V3_DISP (gap 106.0-105.90=0.10 — tight!)
# Need y>=106.0+0.15+0.225 = 106.375 for south of 3V3_DISP track, OR y<=105.85 with gap
# Track 3V3_DISP at 106.0 w=0.25 → edge 105.875. Via r=0.225 at y=105.90 → north edge 105.675. 
# Wait via center 105.90, north edge (smaller y) = 105.90-0.225=105.675. 3V3 south edge = 106.0+0.125=106.125.
# Gap = 106.125 - 105.675? No - north of via is toward smaller y. 3V3 is at LARGER y (south).
# Via south edge = 105.90+0.225=106.125. 3V3 north edge = 106.0-0.125=105.875. OVERLAP!
# So via must be at y <= 105.875 - 0.15 - 0.225 = 105.50, or at y >= 106.125+0.15+0.225=106.50
# Use y=105.50 for via, F from B5 at 105.60
t = add_via(t, 113.50, 105.50, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 113.50, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 113.50, 105.60, 113.50, 105.50, 0.25, "F.Cu", vs)
t = add_segment(t, 113.50, 105.50, 113.50, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 113.50, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)

# --- CD: remove F bar; via+B to CD via ---
t, k = del_segments_at(t, 110.6, 106.8, 112.8, 106.8)
print(f"del CD F {k}")
# PMIC_INT: remove vertical to 106.7 (keep only stub at pad for rats?) — go west at 106.4 only
t, k = del_segments_at(t, 110.6, 106.4, 110.6, 106.7)
print(f"del PI vert {k}")
t, k = del_segments_at(t, 110.6, 106.7, 110.4, 106.7)
print(f"del PI west {k}")

cd, pi = netnum(t,"CD"), netnum(t,"PMIC_INT")
# CD via south of E2 clear of SDA: (110.9, 106.95)
t = add_via(t, 110.90, 106.95, 0.40, 0.25, cd)
t = add_segment(t, 110.6, 106.8, 110.9, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 110.9, 106.8, 110.9, 106.95, 0.18, "F.Cu", cd)
# B jog south of LSCTRL@111.55,107.15 and 3V3 via@112.16,107.6
t = add_segment(t, 110.90, 106.95, 110.90, 108.20, 0.18, "B.Cu", cd)
t = add_segment(t, 110.90, 108.20, 113.30, 108.20, 0.20, "B.Cu", cd)
t = add_segment(t, 113.30, 108.20, 113.30, 108.41, 0.20, "B.Cu", cd)

# PMIC_INT: west on F at pad y, via, B south then west (clear IPRETERM vias)
t = add_segment(t, 110.6, 106.4, 110.45, 106.4, 0.15, "F.Cu", pi)
t = add_via(t, 110.45, 106.40, 0.35, 0.20, pi)
# B south to 106.9 then west — avoid IPRETERM @110.05,106.4 and @109.45,106.7
t = add_segment(t, 110.45, 106.40, 110.45, 106.90, 0.15, "B.Cu", pi)
t = add_segment(t, 110.45, 106.90, 109.20, 106.90, 0.15, "B.Cu", pi)
# Join toward existing B PMIC_INT vertical at x=94.2 — need connection; add via up? 
# Existing B (94.2,90.55)-(94.2,106.4). Extend (109.20,106.90)-(94.2,106.90)-(94.2,106.4)
t = add_segment(t, 109.20, 106.90, 94.20, 106.90, 0.18, "B.Cu", pi)
t = add_segment(t, 94.20, 106.90, 94.20, 106.40, 0.18, "B.Cu", pi)

# --- TS: spine to y=107.05 clear of R_SCL ---
t, k = del_segments_at(t, 111.0, 107.25, 108.2, 107.25)
print(f"del TS spine {k}")
t, k = del_segments_at(t, 111.0, 107.20, 111.0, 107.25)
print(f"del TS link {k}")
ts = netnum(t, "TS")
t = add_segment(t, 111.0, 107.20, 111.0, 107.05, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.05, 108.2, 107.05, 0.18, "F.Cu", ts)

save(t)
print("X3 done")
