#!/usr/bin/env python3
"""Pass-X21: Fix VSYS B vs GND; CD clear of LSCTRL; minimal TS/EPD jogs."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()

# VSYS B: use y=103.70 instead of 104.50 path near GND@106
for a,b,c,d in [
    (115.80, 105.50, 115.80, 104.50),
    (115.80, 104.50, 117.40, 104.50),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del VS {k}")
vs = netnum(t, "VSYS")
t = add_segment(t, 115.80, 105.50, 115.80, 103.70, 0.30, "B.Cu", vs)
t = add_segment(t, 115.80, 103.70, 117.40, 103.70, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 103.70, 117.40, 104.50, 0.30, "B.Cu", vs)

# CD redo: south then east on F at y=108.50 only, never along y=106.8 past E3
for a,b,c,d in [
    (110.6, 106.8, 111.5, 106.8),
    (111.5, 106.8, 111.5, 108.50),
    (111.5, 108.50, 113.3, 108.50),
    (113.3, 108.50, 113.3, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del CD {k}")
cd = netnum(t, "CD")
# Via right next to E2, B south-east
t = add_via(t, 110.60, 107.05, 0.40, 0.25, cd)
t = add_segment(t, 110.60, 106.80, 110.60, 107.05, 0.18, "F.Cu", cd)
t = add_segment(t, 110.60, 107.05, 110.60, 108.50, 0.18, "B.Cu", cd)
t = add_segment(t, 110.60, 108.50, 113.30, 108.50, 0.20, "B.Cu", cd)
t = add_segment(t, 113.30, 108.50, 113.30, 108.41, 0.20, "B.Cu", cd)

# TS spine 107.25 → 107.05
t, k = del_segments_at(t, 111.0, 107.25, 108.2, 107.25)
print(f"del TS {k}")
t, k = del_segments_at(t, 111.0, 107.30, 111.0, 107.25)
print(f"del TS link {k}")
ts = netnum(t, "TS")
t = add_segment(t, 111.0, 107.30, 111.0, 107.05, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.05, 108.2, 107.05, 0.18, "F.Cu", ts)

# EPD_RST nudge x 100.75→100.55
for a,b,c,d in [
    (104.0, 85.9, 100.75, 85.9),
    (100.75, 85.9, 100.75, 83.15),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del EPD {k}")
rst = netnum(t, "EPD_RST")
t = add_segment(t, 104.0, 85.9, 100.55, 85.9, 0.18, "F.Cu", rst)
t = add_segment(t, 100.55, 85.9, 100.55, 83.15, 0.18, "F.Cu", rst)

# GND dangling near SDA if zero-len
t = __import__('re').sub(
    r'\t\(segment\n\t\t\(start 109\.9 108\.6\)\n\t\t\(end 109\.9 108\.6\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

save(t)
print("X21 done")
