#!/usr/bin/env python3
"""Pass-X11: Clear last 3 — VSYS east of C_LDO, TS via, LSCTRL via."""
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

# VSYS: move via 113.80,106.55 → 114.40,106.55
for a,b,c,d in [
    (111.80, 105.60, 113.80, 105.60),
    (113.80, 105.60, 113.80, 106.55),
    (113.80, 106.55, 113.80, 103.90),
    (113.80, 103.90, 117.40, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del VS {k}")
t, n = del_via_xy(t, 113.80, 106.55)
print(f"del VSYS via {n}")
vs = netnum(t, "VSYS")
t = add_via(t, 114.40, 106.55, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 114.40, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 114.40, 105.60, 114.40, 106.55, 0.25, "F.Cu", vs)
t = add_segment(t, 114.40, 106.55, 114.40, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 114.40, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)

# TS via 111.20,108.00 → 111.80,108.10
for a,b,c,d in [
    (111.00, 106.00, 111.20, 106.00),
    (111.20, 106.00, 111.20, 108.00),
    (111.20, 108.00, 108.20, 108.00),
    (108.20, 108.00, 108.20, 107.25),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del TS {k}")
t, n = del_via_xy(t, 111.20, 108.00)
print(f"del TS via e {n}")
t, n = del_via_xy(t, 108.20, 108.00)
print(f"del TS via w {n}")
ts = netnum(t, "TS")
t = add_segment(t, 111.00, 106.00, 111.80, 106.00, 0.18, "F.Cu", ts)
t = add_segment(t, 111.80, 106.00, 111.80, 108.10, 0.18, "F.Cu", ts)
t = add_via(t, 111.80, 108.10, 0.40, 0.25, ts)
t = add_segment(t, 111.80, 108.10, 108.20, 108.10, 0.18, "B.Cu", ts)
t = add_via(t, 108.20, 108.10, 0.40, 0.25, ts)
t = add_segment(t, 108.20, 108.10, 108.20, 107.25, 0.18, "F.Cu", ts)

# LSCTRL via back south of R_SCL: 111.55,107.70
t2, n = re.subn(r'(\t\(via\n\t\t\(at )111\.55 107\.45(\))', r'\g<1>111.55 107.70\g<2>', t, count=1)
if n:
    t = t2
    print("LSCTRL -> 107.70")
else:
    t2, n = re.subn(r'(\t\(via\n\t\t\(at )111\.55 107\.15(\))', r'\g<1>111.55 107.70\g<2>', t, count=1)
    if n:
        t = t2
        print("LSCTRL from 107.15 -> 107.70")

save(t)
print("X11 done")
