#!/usr/bin/env python3
"""Pass-X24: CD via @(110.75,107.15) clear of E1/IPRETERM."""
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

for a,b,c,d in [
    (110.60, 106.80, 110.45, 106.80),
    (110.45, 106.80, 110.45, 106.95),
    (110.45, 106.95, 110.45, 108.50),
    (110.45, 108.50, 113.30, 108.50),
    (113.30, 108.50, 113.30, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")
t, n = del_via_xy(t, 110.45, 106.95)
print(f"del via {n}")

cd = netnum(t, "CD")
# From E2 (110.6,106.8) east slightly then south to via — stay clear of TS@111 and LSCTRL@111.55
t = add_segment(t, 110.60, 106.80, 110.60, 107.20, 0.18, "F.Cu", cd)
t = add_via(t, 110.60, 107.20, 0.40, 0.25, cd)
t = add_segment(t, 110.60, 107.20, 110.60, 108.50, 0.18, "B.Cu", cd)
t = add_segment(t, 110.60, 108.50, 113.30, 108.50, 0.20, "B.Cu", cd)
t = add_segment(t, 113.30, 108.50, 113.30, 108.41, 0.20, "B.Cu", cd)

save(t)
print("X24 done")
