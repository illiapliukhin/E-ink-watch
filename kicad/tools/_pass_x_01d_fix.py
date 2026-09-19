#!/usr/bin/env python3
"""Pass-X1d: Restore PMIC_INT Pass-T; VSYS via east of MP; keep C_SYS + VSYS B path."""
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

# Remove bad PMIC_INT X1c copper
for a,b,c,d in [
    (110.6, 106.4, 110.6, 106.25),
    (110.60, 106.25, 109.45, 106.25),
    (109.45, 106.25, 109.45, 106.70),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del PI {k}")
t, n = del_via_xy(t, 110.60, 106.25)
print(f"del PI via {n}")

# Restore Pass-T PMIC_INT F stubs
pi = netnum(t, "PMIC_INT")
t = add_segment(t, 110.6, 106.4, 110.6, 106.7, 0.15, "F.Cu", pi)
t = add_segment(t, 110.6, 106.7, 110.4, 106.7, 0.15, "F.Cu", pi)

# Move VSYS via 114.20,105.70 → 115.30,105.70 (east of MP 114.6)
for a,b,c,d in [
    (111.80, 105.60, 114.20, 105.60),
    (114.20, 105.60, 114.20, 105.70),
    (114.20, 105.70, 114.20, 103.90),
    (114.20, 103.90, 117.40, 103.90),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del VSYS {k}")
t, n = del_via_xy(t, 114.20, 105.70)
print(f"del VSYS via {n}")

vs = netnum(t, "VSYS")
# F along y=105.60 from B5 to 115.30 — crosses above MP (MP south edge 105.65).
# Track half 0.125 → north edge of clearance: need center y >= 105.65+0.15+0.6? 
# MP pad extends to y=105.65. Track at 105.60 is INSIDE MP y-range!
# So F must be at y>=105.90 south of MP, or hop B before reaching MP x.
# Path: B5 (111.8,105.6) east to (112.8,105.6), via, B under MP to (115.30,103.90), via up, F to L_SYS
# Via west of MP: x<=113.2, y>=105.85 (south of? wait +y south, MP south edge is LARGER y = 105.65)
# Clear SOUTH of MP: y > 105.65 + clr + half = ~105.95
# Clear NORTH of MP: y < 103.65 - clr
# Clear WEST of MP: x < 113.4 - via_r - clr

t = add_via(t, 112.80, 105.95, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 112.80, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.80, 105.60, 112.80, 105.95, 0.25, "F.Cu", vs)
t = add_segment(t, 112.80, 105.95, 112.80, 103.90, 0.30, "B.Cu", vs)
t = add_segment(t, 112.80, 103.90, 117.40, 103.90, 0.30, "B.Cu", vs)
# existing via @117.40,104.50 and F to C_SYS should remain

# ILIM via away from MP: 113.44,105.35 → 114.70,106.50
t2, n = re.subn(r'(\t\(via\n\t\t\(at )113\.44 105\.35(\))', r'\g<1>114.70 106.50\g<2>', t, count=1)
if n:
    t = t2
    print("ILIM via -> (114.70,106.50)")

save(t)
print("X1d done")
