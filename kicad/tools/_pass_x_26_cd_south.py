#!/usr/bin/env python3
"""Pass-X26: CD via @(109.70,107.85) south of TS spine and IPRETERM."""
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
    (110.60, 106.80, 110.60, 107.00),
    (110.60, 107.00, 109.70, 107.00),
    (109.70, 107.00, 109.70, 108.50),
    (109.70, 108.50, 113.30, 108.50),
    (113.30, 108.50, 113.30, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")
t, n = del_via_xy(t, 109.70, 107.00)
print(f"del via {n}")

cd = netnum(t, "CD")
t = add_segment(t, 110.60, 106.80, 110.60, 107.00, 0.15, "F.Cu", cd)
t = add_segment(t, 110.60, 107.00, 109.70, 107.00, 0.15, "F.Cu", cd)
t = add_segment(t, 109.70, 107.00, 109.70, 107.85, 0.15, "F.Cu", cd)
t = add_via(t, 109.70, 107.85, 0.40, 0.25, cd)
t = add_segment(t, 109.70, 107.85, 109.70, 108.50, 0.18, "B.Cu", cd)
t = add_segment(t, 109.70, 108.50, 113.30, 108.50, 0.20, "B.Cu", cd)
t = add_segment(t, 113.30, 108.50, 113.30, 108.41, 0.20, "B.Cu", cd)

save(t)
print("X26 done")
