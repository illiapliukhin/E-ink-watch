#!/usr/bin/env python3
"""Pass-X6: Fix remaining 4 shorts — CD, ILIM/TS, ILIM/IPRETERM, EPD."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, netnum

t = load()

# CD: avoid R_CD GND — route east then south near via
for a,b,c,d in [
    (110.6, 106.8, 110.6, 106.95),
    (110.6, 106.95, 113.3, 106.95),
    (113.3, 106.95, 113.3, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del CD {k}")
cd = netnum(t, "CD")
t = add_segment(t, 110.6, 106.8, 111.5, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 111.5, 106.8, 111.5, 108.20, 0.18, "F.Cu", cd)
t = add_segment(t, 111.5, 108.20, 113.3, 108.20, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 108.20, 113.3, 108.41, 0.20, "F.Cu", cd)

# ILIM B: avoid IPRETERM — east at y=105.80 then to via
for a,b,c,d in [
    (110.30, 105.35, 110.30, 106.50),
    (110.30, 106.50, 114.70, 106.50),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del ILIM {k}")
ilim = netnum(t, "ILIM")
t = add_segment(t, 110.30, 105.35, 110.30, 105.80, 0.20, "B.Cu", ilim)
t = add_segment(t, 110.30, 105.80, 114.70, 105.80, 0.20, "B.Cu", ilim)
t = add_segment(t, 114.70, 105.80, 114.70, 106.50, 0.20, "B.Cu", ilim)

# TS: jog around ILIM via — from C3 (111,106) east to 111.25 then north
t, k = del_segments_at(t, 111.0, 106.0, 111.0, 107.25)
print(f"del TS vert {k}")
ts = netnum(t, "TS")
t = add_segment(t, 111.0, 106.0, 111.25, 106.0, 0.18, "F.Cu", ts)
t = add_segment(t, 111.25, 106.0, 111.25, 107.25, 0.18, "F.Cu", ts)
t = add_segment(t, 111.25, 107.25, 111.0, 107.25, 0.18, "F.Cu", ts)
# spine (111,107.25)-(108.2,107.25) should remain

# EPD_RST vs EPD_BUSY_MAIN — jog EPD_RST
# Short: EPD_RST @(100.75,85.9) len 2.75 vs EPD_BUSY @(100.9,88.1) and @(100.9,84.0)
# Find and nudge EPD_RST track
import re
# List EPD tracks via quick search in file after save — do geometric nudge
# Delete crossing region and re-route EPD_RST slightly west
# From DRC: Track EPD_RST on F length 2.75 @100.75,85.9 — likely vertical or horiz
# Fetch from board in companion — use known coords from earlier Pass-W:
# Try delete segments near (100.75,85.9) and add at x=100.55

save(t)
print("X6 partial (CD/ILIM/TS) saved — EPD next")
