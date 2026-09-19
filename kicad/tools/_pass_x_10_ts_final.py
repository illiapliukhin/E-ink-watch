#!/usr/bin/env python3
"""Pass-X10: Final TS path east of ILIM/PMIC, via clear of 3V3."""
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
    (111.00, 106.00, 110.40, 106.00),
    (110.40, 106.00, 110.40, 107.90),
    (110.40, 107.90, 108.20, 107.90),
    (108.20, 107.90, 108.20, 107.25),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")
t, n = del_via_xy(t, 110.40, 107.90)
print(f"del via e {n}")
t, n = del_via_xy(t, 108.20, 107.90)
print(f"del via w {n}")

ts = netnum(t, "TS")
# C3 east then south to via @(111.20, 108.00) — south of 3V3/R_SDA row
t = add_segment(t, 111.00, 106.00, 111.20, 106.00, 0.18, "F.Cu", ts)
t = add_segment(t, 111.20, 106.00, 111.20, 108.00, 0.18, "F.Cu", ts)
t = add_via(t, 111.20, 108.00, 0.40, 0.25, ts)
t = add_segment(t, 111.20, 108.00, 108.20, 108.00, 0.18, "B.Cu", ts)
t = add_via(t, 108.20, 108.00, 0.40, 0.25, ts)
t = add_segment(t, 108.20, 108.00, 108.20, 107.25, 0.18, "F.Cu", ts)

save(t)
print("X10 done")
