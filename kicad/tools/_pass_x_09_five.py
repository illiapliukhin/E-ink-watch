#!/usr/bin/env python3
"""Pass-X9: Clear remaining 5 shorts; restore R_SCL; nudge vias/tracks."""
import sys, re
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, move_fp, netnum

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

# Restore R_SCL
t = move_fp(t, "R_SCL", 111.65, 107.60)

# TS via 111.00,107.80 → 110.40,107.90 (west of SCL track)
t, k = del_segments_at(t, 111.00, 106.00, 111.00, 107.80)
print(f"del TS vert {k}")
t, k = del_segments_at(t, 111.00, 107.80, 108.20, 107.80)
print(f"del TS B {k}")
t, n = del_via_xy(t, 111.00, 107.80)
print(f"del TS via {n}")
ts = netnum(t, "TS")
t = add_segment(t, 111.00, 106.00, 110.40, 106.00, 0.18, "F.Cu", ts)
t = add_segment(t, 110.40, 106.00, 110.40, 107.90, 0.18, "F.Cu", ts)
t = add_via(t, 110.40, 107.90, 0.40, 0.25, ts)
t = add_segment(t, 110.40, 107.90, 108.20, 107.90, 0.18, "B.Cu", ts)
# update west via y if needed
t, n = del_via_xy(t, 108.20, 107.80)
print(f"del west via {n}")
t, k = del_segments_at(t, 108.20, 107.80, 108.20, 107.25)
print(f"del west F {k}")
t = add_via(t, 108.20, 107.90, 0.40, 0.25, ts)
t = add_segment(t, 108.20, 107.90, 108.20, 107.25, 0.18, "F.Cu", ts)

# VSYS via 112.00,105.50 → 112.00,105.90 (south of ILIM B@105.35)
for a,b,c,d in [
    (111.80, 105.60, 112.00, 105.60),
    (112.00, 105.60, 112.00, 105.50),
    (112.00, 105.50, 112.00, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del VS {k}")
t, n = del_via_xy(t, 112.00, 105.50)
print(f"del VSYS via {n}")
vs = netnum(t, "VSYS")
# y=105.90 may hit 3V3_DISP@106.0 — use 105.75 with care, or 106.40 south of 3V3_DISP
# 3V3_DISP at 106.0 w=0.25 → edges 105.875-106.125. Via at 106.45 south: north edge 106.225, gap=0.1
# Via at 111.95, 105.70: south edge 105.925, 3V3 north 105.875 — gap -0.05 still bad
# So must be y<=105.875-0.15-0.225=105.50 (current, hits ILIM) OR y>=106.125+0.15+0.225=106.50
t = add_via(t, 112.00, 106.55, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.00, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.00, 105.60, 112.00, 106.55, 0.25, "F.Cu", vs)
t = add_segment(t, 112.00, 106.55, 112.00, 103.90, 0.30, "B.Cu", vs)
# Wait B from 106.55 to 103.90 on same via — OK through-via. But F vertical 105.60-106.55 crosses 3V3_DISP at 106.0!
# Need dogbone: F to via east of 3V3_DISP end. Truncate 3V3_DISP already ends at 113.5.
# F path: B5-(112,105.6) east to (113.8,105.6), north to (113.8,106.55), via, B west/south
t, n = del_via_xy(t, 112.00, 106.55)
# remove the bad segments just added
for a,b,c,d in [
    (111.80, 105.60, 112.00, 105.60),
    (112.00, 105.60, 112.00, 106.55),
    (112.00, 106.55, 112.00, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
t = add_via(t, 113.80, 106.55, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 113.80, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 113.80, 105.60, 113.80, 106.55, 0.25, "F.Cu", vs)
t = add_segment(t, 113.80, 106.55, 113.80, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 113.80, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)

# LSCTRL via 111.55,107.15 → 111.55,107.45 (south of SCL track)
t2, n = re.subn(r'(\t\(via\n\t\t\(at )111\.55 107\.15(\))', r'\g<1>111.55 107.45\g<2>', t, count=1)
if n:
    t = t2
    print("LSCTRL via -> 107.45")
# may need to extend LSCTRL F stub

# GND track near R_SDA: (109.6,107.8) length 0.6 — nudge south or delete if dangling
t, k = del_segments_at(t, 109.6, 107.8, 109.6, 107.2)  # guess
# find exact via pcbnew after
save(t)
print("X9 mid")
