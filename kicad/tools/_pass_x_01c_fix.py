#!/usr/bin/env python3
"""Pass-X1c: Move VSYS via east; kill GND blob; separate CD/PMIC_INT; trim TS stub."""
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

# Remove VSYS path to old via
for a,b,c,d in [
    (111.80, 105.60, 112.50, 105.60),
    (112.50, 105.60, 112.50, 105.65),
    (112.50, 105.65, 112.50, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")
t, n = del_via_xy(t, 112.50, 105.65)
print(f"del via {n}")

# Zero-len GND blob
t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)
t, k = del_segments_at(t, 112.8, 105.32, 112.8, 105.4)
print(f"del GND stub {k}")

# CD/PMIC_INT: remove PMIC_INT vertical kiss; keep west only from pad
t, k = del_segments_at(t, 110.6, 106.4, 110.6, 106.7)
print(f"del PI vert {k}")
t, k = del_segments_at(t, 110.6, 106.7, 110.4, 106.7)
print(f"del PI west {k}")

# TS: remove tiny stub (111,107.3)-(111,107.25) that with vertical causes SCL issue?
# Actually short is (111,107.3) length 0.05 — the connector to spine. Move spine to 107.15? 
# Better: shorten vertical TS so it ends at 107.20 not 107.30
t, k = del_segments_at(t, 111.0, 107.30, 111.0, 107.25)
print(f"del TS link {k}")
t, k = del_segments_at(t, 111.0, 107.30, 111.0, 106.0)
print(f"del TS vert {k}")

vs, pi, ts, cd = [netnum(t,n) for n in ("VSYS","PMIC_INT","TS","CD")]

# VSYS via at (114.20, 105.70) — east of ILIM B end ~113.44, west of SW via@115
t = add_via(t, 114.20, 105.70, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 114.20, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 114.20, 105.60, 114.20, 105.70, 0.25, "F.Cu", vs)
t = add_segment(t, 114.20, 105.70, 114.20, 103.90, 0.30, "B.Cu", vs)
# reconnect to existing B (112.50 was deleted vertical; horizontal 112.50-117.40 at 103.90 may remain)
# Check — we deleted only vertical from 112.50. Horizontal (112.50,103.90)-(117.40,103.90) may still ref old start
t, k = del_segments_at(t, 112.50, 103.90, 117.40, 103.90)
print(f"del old B horiz {k}")
t = add_segment(t, 114.20, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)

# PMIC_INT west from pad only, via down, join existing B network carefully
# Existing B IPRETERM at 110.05 — stay clear. Via at (110.45, 106.25) south of pad?
t = add_segment(t, 110.6, 106.4, 110.6, 106.25, 0.15, "F.Cu", pi)
t = add_via(t, 110.60, 106.25, 0.40, 0.25, pi)
# B west to meet old PMIC_INT B at x=94.2 — use (110.60,106.25)-(94.2,106.25) too long; 
# old had (110.4,106.7)-(109.45,106.7) and via 109.45. Simpler: B to (110.60,106.25)-(109.45,106.25)-(109.45,106.7)
t = add_segment(t, 110.60, 106.25, 109.45, 106.25, 0.15, "B.Cu", pi)
t = add_segment(t, 109.45, 106.25, 109.45, 106.70, 0.15, "B.Cu", pi)

# TS vertical only to 107.20, spine at 107.25 — small gap OK with link
t = add_segment(t, 111.0, 106.0, 111.0, 107.20, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.20, 111.0, 107.25, 0.18, "F.Cu", ts)

save(t)
print("X1c done")
