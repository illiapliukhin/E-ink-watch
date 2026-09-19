#!/usr/bin/env python3
"""Pass-X4: Clean CD/PMIC/ILIM/VSYS/PMID around MP; keep C_SYS+C_VINLS."""
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

# === Remove X3 CD/PMIC mess ===
for a,b,c,d in [
    (110.6, 106.8, 110.9, 106.8),
    (110.9, 106.8, 110.9, 106.95),
    (110.9, 106.95, 110.9, 108.20),
    (110.9, 108.20, 113.3, 108.20),
    (113.3, 108.20, 113.3, 108.41),
    (110.6, 106.4, 110.45, 106.4),
    (110.45, 106.4, 110.45, 106.9),
    (110.45, 106.9, 109.2, 106.9),
    (109.2, 106.9, 94.2, 106.9),
    (94.2, 106.9, 94.2, 106.4),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")
t, n = del_via_xy(t, 110.90, 106.95)
print(f"del CD via {n}")
t, n = del_via_xy(t, 110.45, 106.40)
print(f"del PI via {n}")

# === Remove bad PMID/GND/VSYS ===
for a,b,c,d in [
    (112.50, 104.98, 113.30, 104.98),
    (113.30, 104.98, 113.30, 103.85),
    (113.30, 103.85, 111.35, 103.85),
    (112.50, 104.02, 112.20, 104.02),
    (112.20, 104.02, 112.20, 103.40),
    (112.20, 103.40, 112.68, 103.40),
    (111.80, 105.60, 113.50, 105.60),
    (113.50, 105.60, 113.50, 105.50),
    (113.50, 105.50, 113.50, 103.90),
    (113.50, 103.90, 117.40, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del2 {k}")
t, n = del_via_xy(t, 113.50, 105.50)
print(f"del VSYS via {n}")

# === ILIM: reconnect B to via @114.70,106.50; remove dangling to 113.44 ===
t, k = del_segments_at(t, 110.3, 105.35, 113.44, 105.35)
print(f"del ILIM B dang {k}")
ilim = netnum(t, "ILIM")
t = add_segment(t, 110.30, 105.35, 110.30, 106.50, 0.20, "B.Cu", ilim)
t = add_segment(t, 110.30, 106.50, 114.70, 106.50, 0.20, "B.Cu", ilim)

# === CD: F east at y=106.95 from via east of E2 ===
cd, pi, pm, gnd, vs, ts = [netnum(t,n) for n in
    ("CD","PMIC_INT","PMID","GND","VSYS","TS")]
t = add_via(t, 111.20, 106.95, 0.40, 0.25, cd)
t = add_segment(t, 110.6, 106.8, 110.6, 106.95, 0.18, "F.Cu", cd)
t = add_segment(t, 110.6, 106.95, 111.20, 106.95, 0.18, "F.Cu", cd)
t = add_segment(t, 111.20, 106.95, 111.20, 108.20, 0.18, "B.Cu", cd)
t = add_segment(t, 111.20, 108.20, 113.30, 108.20, 0.20, "B.Cu", cd)
t = add_segment(t, 113.30, 108.20, 113.30, 108.41, 0.20, "B.Cu", cd)

# === PMIC_INT: short stub only (no overlap with CD@106.95) — leave unconnected to B for now ===
t = add_segment(t, 110.6, 106.4, 110.6, 106.55, 0.15, "F.Cu", pi)
t = add_segment(t, 110.6, 106.55, 110.35, 106.55, 0.15, "F.Cu", pi)
t = add_via(t, 110.35, 106.55, 0.35, 0.20, pi)
t = add_segment(t, 110.35, 106.55, 110.35, 107.00, 0.15, "B.Cu", pi)
t = add_segment(t, 110.35, 107.00, 94.20, 107.00, 0.18, "B.Cu", pi)
t = add_segment(t, 94.20, 107.00, 94.20, 106.40, 0.18, "B.Cu", pi)

# === PMID fanout: west corridor x=112.0 ===
t = add_segment(t, 112.50, 104.98, 112.00, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 112.00, 104.98, 112.00, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 112.00, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)
# GND south-west
t = add_segment(t, 112.50, 104.02, 112.50, 103.40, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.50, 103.40, 112.68, 103.40, 0.20, "F.Cu", gnd)

# === VSYS: via @ (112.00, 105.85) after ILIM B moved off y=105.35 ===
t = add_via(t, 112.00, 105.85, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.00, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.00, 105.60, 112.00, 105.85, 0.25, "F.Cu", vs)
t = add_segment(t, 112.00, 105.85, 112.00, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 112.00, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)

# === TS: keep @107.05; if SDA still hits, move to 106.95 ===
# already at 107.05 from X3 — check remaining TS segs
t, k = del_segments_at(t, 111.0, 107.05, 108.2, 107.05)
t, k2 = del_segments_at(t, 111.0, 107.20, 111.0, 107.05)
print(f"refresh TS {k},{k2}")
t = add_segment(t, 111.0, 107.20, 111.0, 106.95, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 106.95, 108.2, 106.95, 0.18, "F.Cu", ts)

save(t)
print("X4 done")
