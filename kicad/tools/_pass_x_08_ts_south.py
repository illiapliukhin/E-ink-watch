#!/usr/bin/env python3
"""Pass-X8: TS B-hop at y=107.80; ILIM clear; BTN2 further west; leave SCL/LSCTRL for jog."""
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

# Remove current TS routing
for a,b,c,d in [
    (111.00, 106.00, 111.00, 106.20),
    (111.00, 106.20, 108.20, 106.20),
    (108.20, 106.20, 108.20, 107.25),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del TS {k}")
t, n = del_via_xy(t, 111.00, 106.20)
print(f"del via1 {n}")
t, n = del_via_xy(t, 108.20, 106.20)
print(f"del via2 {n}")

ts = netnum(t, "TS")
# From C3 south on F to (111, 107.80), via, B west, via, F to old west network
t = add_segment(t, 111.00, 106.00, 111.00, 107.80, 0.18, "F.Cu", ts)
t = add_via(t, 111.00, 107.80, 0.40, 0.25, ts)
t = add_segment(t, 111.00, 107.80, 108.20, 107.80, 0.18, "B.Cu", ts)
t = add_via(t, 108.20, 107.80, 0.40, 0.25, ts)
t = add_segment(t, 108.20, 107.80, 108.20, 107.25, 0.18, "F.Cu", ts)
# west spine remnant may need (108.2,107.25) connection — old network continues west on F from there

# ILIM: move B east run to y=105.50 (clear VSYS via@105.50? same y — use 105.20)
for a,b,c,d in [
    (110.30, 105.35, 110.30, 106.20),
    (110.30, 106.20, 114.70, 106.20),
    (114.70, 106.20, 114.70, 106.50),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del ILIM {k}")
ilim = netnum(t, "ILIM")
t = add_segment(t, 110.30, 105.35, 114.70, 105.35, 0.20, "B.Cu", ilim)
t = add_segment(t, 114.70, 105.35, 114.70, 106.50, 0.20, "B.Cu", ilim)

# BTN2 further west x=97.8
for a,b,c,d in [
    (98.25, 95.6, 98.25, 112.2),
    (98.25, 112.2, 112.8, 112.2),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del BTN2 {k}")
btn2 = netnum(t, "BTN2")
t = add_segment(t, 97.80, 95.6, 97.80, 112.2, 0.18, "B.Cu", btn2)
t = add_segment(t, 97.80, 112.2, 112.8, 112.2, 0.18, "B.Cu", btn2)

# Jog SCL track away from LSCTRL — find SCL near (111.8,106.8)
# Move R_SCL slightly east?
t = __import__('_pass_x_sexpr_lib', fromlist=['move_fp']).move_fp(t, "R_SCL", 112.00, 107.60)

save(t)
print("X8 done")
