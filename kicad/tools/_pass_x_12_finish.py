#!/usr/bin/env python3
"""Pass-X12: Clean VSYS/TS/LSCTRL for shorting=0; keep C_SYS+C_VINLS pocket."""
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

# --- Strip all our VSYS F/B near U2 (keep L_SYS/C_SYS F stubs) ---
for a,b,c,d in [
    (111.80, 105.60, 114.40, 105.60),
    (114.40, 105.60, 114.40, 106.55),
    (114.40, 106.55, 114.40, 103.90),
    (114.40, 103.90, 117.40, 103.90),
    (111.80, 105.60, 113.80, 105.60),
    (113.80, 105.60, 113.80, 106.55),
    (113.80, 106.55, 113.80, 103.90),
    (113.80, 103.90, 117.40, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
t, n = del_via_xy(t, 114.40, 106.55)
t, n2 = del_via_xy(t, 113.80, 106.55)
print(f"cleared VSYS vias {n},{n2}")

# --- Strip TS ---
for a,b,c,d in [
    (111.00, 106.00, 111.80, 106.00),
    (111.80, 106.00, 111.80, 108.10),
    (111.80, 108.10, 108.20, 108.10),
    (108.20, 108.10, 108.20, 107.25),
    (111.00, 106.00, 111.20, 106.00),
    (111.20, 106.00, 111.20, 108.00),
    (111.20, 108.00, 108.20, 108.00),
    (108.20, 108.00, 108.20, 107.25),
]:
    t, k = del_segments_at(t, a, b, c, d)
for xy in [(111.80,108.10),(108.20,108.10),(111.20,108.00),(108.20,108.00)]:
    t, n = del_via_xy(t, *xy)
    if n: print(f"del TS via {xy}")

vs, ts = netnum(t,"VSYS"), netnum(t,"TS")

# VSYS: F @y=105.60 to x=115.5 (east of ILIM via 114.7), via @115.50,105.50, B to L_SYS
t = add_via(t, 115.50, 105.50, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 115.50, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 115.50, 105.60, 115.50, 105.50, 0.25, "F.Cu", vs)
t = add_segment(t, 115.50, 105.50, 115.50, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 115.50, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)

# TS: C3 → east 111.3 → south on B via (111.3,105.70) B west @105.70 to (108.2,105.70) — north of ILIM B@105.35?
# ILIM B at 105.35, TS B at 105.70 — gap 0.35-0.1-0.1=0.15 OK
# Via at 111.3,105.70 clear of ILIM via 110.75,106 and 3V3_DISP
t = add_segment(t, 111.00, 106.00, 111.30, 106.00, 0.18, "F.Cu", ts)
t = add_via(t, 111.30, 105.70, 0.40, 0.25, ts)
t = add_segment(t, 111.30, 106.00, 111.30, 105.70, 0.18, "F.Cu", ts)
t = add_segment(t, 111.30, 105.70, 108.20, 105.70, 0.18, "B.Cu", ts)
t = add_via(t, 108.20, 105.70, 0.40, 0.25, ts)
t = add_segment(t, 108.20, 105.70, 108.20, 107.25, 0.18, "F.Cu", ts)

# LSCTRL via to (111.40, 107.90) — south, clear R_SCL
for oldy in ("107.70", "107.45", "107.15"):
    t2, n = re.subn(
        rf'(\t\(via\n\t\t\(at )111\.55 {oldy}(\))',
        r'\g<1>111.40 107.90\g<2>', t, count=1)
    if n:
        t = t2
        print(f"LSCTRL from {oldy} -> 111.40,107.90")
        break

save(t)
print("X12 done")
