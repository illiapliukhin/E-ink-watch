#!/usr/bin/env python3
"""Pass-W11: Fix W10 shorts — PMID path, VSYS via, ILIM, CD/PMIC, C_SYS."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, add_via, netnum

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

# Remove bad segments
for a,b,c,d in [
    (112.50, 104.98, 111.85, 104.98),
    (111.85, 104.98, 111.85, 103.85),
    (111.85, 103.85, 111.35, 103.85),
    (111.80, 105.60, 112.30, 105.60),
    (112.30, 105.60, 112.30, 103.80),
    (112.30, 103.80, 117.40, 103.80),
    (117.40, 103.80, 117.40, 104.50),
    (117.50, 103.02, 117.50, 102.50),
    (110.6, 106.8, 112.8, 106.8),
    (110.6, 106.4, 110.6, 106.7),
    (110.6, 106.7, 110.4, 106.7),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")

t, n = del_via_xy(t, 112.30, 105.60)
print(f"del VSYS via {n}")

# ILIM via 113.44,105.35 -> 114.60,106.60
t2, n = re.subn(
    r'(\t\(via\n\t\t\(at )113\.44 105\.35(\))',
    r'\g<1>114.60 106.60\g<2>', t, count=1)
if n: t=t2; print("ILIM moved")

t = move_fp(t, "C_SYS", 118.20, 103.80)  # further from strap pad10

vs, pm, cd, pi, gnd = [netnum(t,n) for n in ("VSYS","PMID","CD","PMIC_INT","GND")]

# PMID fanout: go EAST around SW via then south to island
# pad1 (112.5,104.98) -> (112.5,103.85) but clear of C_SYS/old — SW is at 111.55
# Path: (112.5,104.98)-(112.9,104.98)-(112.9,103.85)-(111.35,103.85)
t = add_segment(t, 112.50, 104.98, 112.90, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 112.90, 104.98, 112.90, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 112.90, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)

# VSYS via at (113.0, 105.60) — check ILIM B: was to 113.44, if ILIM via moved, B track may still run
# Use via at (112.0, 105.55) west? B5 is 111.8. Try (115.0, 105.55) far east on F then B
t = add_via(t, 115.00, 105.55, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 115.00, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 115.00, 105.60, 115.00, 105.55, 0.25, "F.Cu", vs)
t = add_segment(t, 115.00, 105.55, 115.00, 103.80, 0.30, "B.Cu", vs)
t = add_segment(t, 115.00, 103.80, 117.40, 103.80, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 103.80, 117.40, 104.50, 0.30, "B.Cu", vs)
# C_SYS pads now @(118.20, 104.28) VSYS / (118.20, 103.32) GND
t = add_segment(t, 117.40, 104.50, 118.20, 104.50, 0.28, "F.Cu", vs)
t = add_segment(t, 118.20, 104.50, 118.20, 104.28, 0.28, "F.Cu", vs)

# CD / PMIC_INT separation
t = add_segment(t, 110.6, 106.4, 110.35, 106.4, 0.15, "F.Cu", pi)
t = add_segment(t, 110.6, 106.8, 110.6, 107.00, 0.18, "F.Cu", cd)
t = add_segment(t, 110.6, 107.00, 112.8, 107.00, 0.20, "F.Cu", cd)
t = add_segment(t, 112.8, 107.00, 112.8, 108.26, 0.20, "F.Cu", cd)

save(t)
print("W11 done")
