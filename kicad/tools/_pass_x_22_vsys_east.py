#!/usr/bin/env python3
"""Pass-X22: VSYS via further east; restore TS Pass-T; BTN2 west; delete CD via clash."""
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

# VSYS move via 115.80 → 116.60
for a,b,c,d in [
    (111.80, 105.60, 115.80, 105.60),
    (115.80, 105.60, 115.80, 105.50),
    (115.80, 105.50, 115.80, 103.70),
    (115.80, 103.70, 117.40, 103.70),
    (117.40, 103.70, 117.40, 104.50),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del VS {k}")
t, n = del_via_xy(t, 115.80, 105.50)
print(f"del VSYS via {n}")
vs = netnum(t, "VSYS")
t = add_via(t, 116.60, 105.50, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 116.60, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 116.60, 105.60, 116.60, 105.50, 0.25, "F.Cu", vs)
t = add_segment(t, 116.60, 105.50, 116.60, 104.50, 0.30, "B.Cu", vs)
t = add_segment(t, 116.60, 104.50, 117.40, 104.50, 0.30, "B.Cu", vs)

# Restore TS Pass-T spine
for a,b,c,d in [
    (111.0, 107.30, 111.0, 107.05),
    (111.0, 107.05, 108.2, 107.05),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del TS {k}")
ts = netnum(t, "TS")
t = add_segment(t, 111.0, 107.30, 111.0, 107.25, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.25, 108.2, 107.25, 0.18, "F.Cu", ts)

# CD: remove via at 110.60,107.05; use F-only path east at y=107.05 then south at x=113.3
# avoiding TS @107.25
for a,b,c,d in [
    (110.60, 106.80, 110.60, 107.05),
    (110.60, 107.05, 110.60, 108.50),
    (110.60, 108.50, 113.30, 108.50),
    (113.30, 108.50, 113.30, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del CD {k}")
t, n = del_via_xy(t, 110.60, 107.05)
print(f"del CD via {n}")
cd = netnum(t, "CD")
t = add_segment(t, 110.60, 106.80, 110.85, 106.80, 0.18, "F.Cu", cd)
t = add_segment(t, 110.85, 106.80, 110.85, 108.50, 0.18, "F.Cu", cd)
t = add_segment(t, 110.85, 108.50, 113.30, 108.50, 0.20, "F.Cu", cd)
t = add_segment(t, 113.30, 108.50, 113.30, 108.41, 0.20, "F.Cu", cd)

# BTN2 west
t, k = del_segments_at(t, 98.5, 95.6, 98.5, 112.2)
print(f"del BTN2 v {k}")
t, k = del_segments_at(t, 98.5, 112.2, 112.8, 112.2)
print(f"del BTN2 h {k}")
btn2 = netnum(t, "BTN2")
t = add_segment(t, 97.70, 95.6, 97.70, 112.2, 0.18, "B.Cu", btn2)
t = add_segment(t, 97.70, 112.2, 112.8, 112.2, 0.18, "B.Cu", btn2)

save(t)
print("X22 done")
