#!/usr/bin/env python3
"""Pass-X5: Simplify — PMIC_INT stub-only; CD F-only; VSYS via y=105.50; TS Pass-T spine."""
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

# Remove PMIC_INT via+B (keep short F stubs)
for a,b,c,d in [
    (110.6, 106.4, 110.6, 106.55),
    (110.6, 106.55, 110.35, 106.55),
    (110.35, 106.55, 110.35, 107.00),
    (110.35, 107.00, 94.20, 107.00),
    (94.20, 107.00, 94.20, 106.40),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del PI {k}")
t, n = del_via_xy(t, 110.35, 106.55)
print(f"del PI via {n}")
# Leave tiny F stub so pad isn't fully open for future: (110.6,106.4)-(110.5,106.4)
pi = netnum(t, "PMIC_INT")
t = add_segment(t, 110.6, 106.4, 110.50, 106.4, 0.15, "F.Cu", pi)

# Remove CD via+B; use F routing to R_CD via x=113.3
for a,b,c,d in [
    (110.6, 106.8, 110.6, 106.95),
    (110.6, 106.95, 111.20, 106.95),
    (111.20, 106.95, 111.20, 108.20),
    (111.20, 108.20, 113.30, 108.20),
    (113.30, 108.20, 113.30, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del CD {k}")
t, n = del_via_xy(t, 111.20, 106.95)
print(f"del CD via {n}")
cd = netnum(t, "CD")
# F: E2 south to 106.95, east to 113.3, north to via (existing via @113.3,108.41)
t = add_segment(t, 110.6, 106.8, 110.6, 106.95, 0.18, "F.Cu", cd)
t = add_segment(t, 110.6, 106.95, 113.3, 106.95, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 106.95, 113.3, 108.41, 0.20, "F.Cu", cd)

# VSYS via: move 112.00,105.85 → 112.00,105.50
for a,b,c,d in [
    (111.80, 105.60, 112.00, 105.60),
    (112.00, 105.60, 112.00, 105.85),
    (112.00, 105.85, 112.00, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del VS {k}")
t, n = del_via_xy(t, 112.00, 105.85)
print(f"del VSYS via {n}")
vs = netnum(t, "VSYS")
t = add_via(t, 112.00, 105.50, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.00, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.00, 105.60, 112.00, 105.50, 0.25, "F.Cu", vs)
t = add_segment(t, 112.00, 105.50, 112.00, 103.90, 0.30, "B.Cu", vs)
# B horiz to 117.40 should still exist from X4

# TS restore Pass-T-ish @107.25 (clear CD @106.95)
for a,b,c,d in [
    (111.0, 107.20, 111.0, 106.95),
    (111.0, 106.95, 108.2, 106.95),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del TS {k}")
ts = netnum(t, "TS")
# vertical may still be (111,106)-(111,107.2)
t, k = del_segments_at(t, 111.0, 106.0, 111.0, 107.20)
if k: print(f"del TSv {k}")
t = add_segment(t, 111.0, 106.0, 111.0, 107.25, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.25, 108.2, 107.25, 0.18, "F.Cu", ts)

save(t)
print("X5 done")
