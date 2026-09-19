#!/usr/bin/env python3
"""Pass-X13: From X11 tree — fix VSYS (no rise through C_LDO), TS via SE, LSCTRL N."""
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

# VSYS: replace 114.40/106.55 scheme with via at 115.20,105.50 only (no y-rise)
for a,b,c,d in [
    (111.80, 105.60, 114.40, 105.60),
    (114.40, 105.60, 114.40, 106.55),
    (114.40, 106.55, 114.40, 103.90),
    (114.40, 103.90, 117.40, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print("del VS", k)
t, n = del_via_xy(t, 114.40, 106.55)
print("del VSYS via", n)

vs = netnum(t, "VSYS")
t = add_via(t, 115.20, 105.50, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 115.20, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 115.20, 105.60, 115.20, 105.50, 0.25, "F.Cu", vs)
t = add_segment(t, 115.20, 105.50, 115.20, 104.50, 0.30, "B.Cu", vs)
t = add_segment(t, 115.20, 104.50, 117.40, 104.50, 0.30, "B.Cu", vs)
# Join existing via @117.40,104.50 — already there from earlier

# TS: move via from 111.80,108.10 to 112.50,108.40
for a,b,c,d in [
    (111.00, 106.00, 111.80, 106.00),
    (111.80, 106.00, 111.80, 108.10),
    (111.80, 108.10, 108.20, 108.10),
    (108.20, 108.10, 108.20, 107.25),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print("del TS", k)
t, n = del_via_xy(t, 111.80, 108.10)
t, n2 = del_via_xy(t, 108.20, 108.10)
print("del TS vias", n, n2)

ts = netnum(t, "TS")
# Path: C3 east to 112.50 along y=106 (on 3V3_DISP row!) — BAD
# C3 south first to 106.5 on x=111.15 (between ILIM and 3V3_DISP start), then east?
# Simpler: C3 → (111, 105.50) north F, via, B west @105.50 to 108.2 — ILIM B is @105.35
t = add_segment(t, 111.00, 106.00, 111.00, 105.50, 0.18, "F.Cu", ts)
t = add_via(t, 111.00, 105.50, 0.40, 0.25, ts)
t = add_segment(t, 111.00, 105.50, 107.50, 105.50, 0.18, "B.Cu", ts)
t = add_via(t, 107.50, 105.50, 0.40, 0.25, ts)
t = add_segment(t, 107.50, 105.50, 107.50, 107.25, 0.18, "F.Cu", ts)
t = add_segment(t, 107.50, 107.25, 108.20, 107.25, 0.18, "F.Cu", ts)

# LSCTRL via → 110.90, 107.20 (west of R_SCL)
for old in ["111.55 107.70", "111.40 107.90", "111.55 107.45", "111.55 107.15"]:
    t2, n = re.subn(
        rf'(\t\(via\n\t\t\(at ){re.escape(old)}(\))',
        r'\g<1>110.90 107.20\g<2>', t, count=1)
    if n:
        t = t2
        print("LSCTRL ->", old, "to 110.90,107.20")
        break

save(t)
print("X13 done")
