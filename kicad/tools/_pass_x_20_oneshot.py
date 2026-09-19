#!/usr/bin/env python3
"""Pass-X20 oneshot: pocket + minimal copper fixes proven to reduce shorts."""
import sys, re
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, add_via, netnum

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

# --- Deletes ---
dels = [
    (112.8, 103.52, 112.2, 103.52),
    (112.51, 103.5, 112.51, 102.4),
    (112.8, 105.32, 112.8, 105.4),
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    (113.0, 106.0, 113.0, 107.4),
    (111.8, 106.1, 112.05, 106.1),
    (112.05, 106.1, 112.05, 105.6),
    (117.412, 106.1, 111.8, 106.1),
    (117.412, 104.5, 117.412, 106.1),
    (112.05, 105.6, 111.8, 105.6),
    (110.6, 106.8, 112.8, 106.8),  # CD F bar — separate from PMIC_INT
    (110.6, 106.4, 110.6, 106.7),
    (110.6, 106.7, 110.4, 106.7),
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")
t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

# ILIM via east
t2, n = re.subn(r'(\t\(via\n\t\t\(at )113\.44 105\.35(\))', r'\g<1>114.70 106.50\g<2>', t, count=1)
if n: t=t2; print("ILIM via moved")

# Footprints
t = move_fp(t, "C_SYS", 117.80, 103.60)
t = move_fp(t, "C_VINLS", 112.50, 104.50)

vs, pm, gnd, d3, cd, pi, ilim = [netnum(t,n) for n in
    ("VSYS","PMID","GND","3V3_DISP","CD","PMIC_INT","ILIM")]

# 3V3_DISP to C_LDO
t = add_segment(t, 111.8, 106.0, 113.5, 106.0, 0.25, "F.Cu", d3)
t = add_segment(t, 113.5, 106.0, 113.5, 106.32, 0.25, "F.Cu", d3)

# VSYS: F @105.60 to via east of SW@115 and MP — (115.80,105.50)
t = add_via(t, 115.80, 105.50, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 115.80, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 115.80, 105.60, 115.80, 105.50, 0.25, "F.Cu", vs)
t = add_via(t, 117.40, 104.50, 0.50, 0.30, vs)
t = add_segment(t, 115.80, 105.50, 115.80, 104.50, 0.30, "B.Cu", vs)
t = add_segment(t, 115.80, 104.50, 117.40, 104.50, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 104.50, 117.80, 104.50, 0.28, "F.Cu", vs)
t = add_segment(t, 117.80, 104.50, 117.80, 104.08, 0.28, "F.Cu", vs)

# ILIM B reconnect to new via (avoid dangling)
t, k = del_segments_at(t, 110.3, 105.35, 113.44, 105.35)
print(f"del ILIM dang {k}")
t = add_segment(t, 110.30, 105.35, 110.30, 105.20, 0.20, "B.Cu", ilim)
t = add_segment(t, 110.30, 105.20, 114.70, 105.20, 0.20, "B.Cu", ilim)
t = add_segment(t, 114.70, 105.20, 114.70, 106.50, 0.20, "B.Cu", ilim)

# C_VINLS fanouts
t = add_segment(t, 112.50, 104.98, 112.00, 104.98, 0.20, "F.Cu", pm)
t = add_segment(t, 112.00, 104.98, 112.00, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 112.00, 103.85, 111.35, 103.85, 0.20, "F.Cu", pm)
t = add_segment(t, 112.50, 104.02, 112.50, 103.40, 0.20, "F.Cu", gnd)
t = add_segment(t, 112.50, 103.40, 112.68, 103.40, 0.20, "F.Cu", gnd)

# CD: F path clear of R_CD GND and PMIC_INT
t = add_segment(t, 110.6, 106.8, 111.5, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 111.5, 106.8, 111.5, 108.50, 0.18, "F.Cu", cd)
t = add_segment(t, 111.5, 108.50, 113.3, 108.50, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 108.50, 113.3, 108.41, 0.20, "F.Cu", cd)

# PMIC_INT: short stub only (pad escape west) — leave rat to B for later stitch
t = add_segment(t, 110.6, 106.4, 110.50, 106.4, 0.15, "F.Cu", pi)

# TS: leave Pass-T spine alone (still on board)

save(t)
print("X20 oneshot written")
