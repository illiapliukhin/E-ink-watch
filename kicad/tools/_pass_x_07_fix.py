#!/usr/bin/env python3
"""Pass-X7: ILIM y, CD y, TS B-hop, EPD reconnect, BTN2 jog."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()

# ILIM B to y=106.20
for a,b,c,d in [
    (110.30, 105.35, 110.30, 105.80),
    (110.30, 105.80, 114.70, 105.80),
    (114.70, 105.80, 114.70, 106.50),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del ILIM {k}")
ilim = netnum(t, "ILIM")
t = add_segment(t, 110.30, 105.35, 110.30, 106.20, 0.20, "B.Cu", ilim)
t = add_segment(t, 110.30, 106.20, 114.70, 106.20, 0.20, "B.Cu", ilim)
t = add_segment(t, 114.70, 106.20, 114.70, 106.50, 0.20, "B.Cu", ilim)

# CD horizontal at y=108.50
for a,b,c,d in [
    (110.6, 106.8, 111.5, 106.8),
    (111.5, 106.8, 111.5, 108.20),
    (111.5, 108.20, 113.3, 108.20),
    (113.3, 108.20, 113.3, 108.41),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del CD {k}")
cd = netnum(t, "CD")
t = add_segment(t, 110.6, 106.8, 111.5, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 111.5, 106.8, 111.5, 108.50, 0.18, "F.Cu", cd)
t = add_segment(t, 111.5, 108.50, 113.3, 108.50, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 108.50, 113.3, 108.41, 0.20, "F.Cu", cd)

# TS: remove F jog; B-hop
for a,b,c,d in [
    (111.0, 106.0, 111.25, 106.0),
    (111.25, 106.0, 111.25, 107.25),
    (111.25, 107.25, 111.0, 107.25),
    (111.0, 107.25, 108.2, 107.25),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del TS {k}")
ts = netnum(t, "TS")
t = add_via(t, 111.00, 106.20, 0.40, 0.25, ts)
t = add_segment(t, 111.00, 106.00, 111.00, 106.20, 0.18, "F.Cu", ts)
t = add_via(t, 108.20, 106.20, 0.40, 0.25, ts)
t = add_segment(t, 111.00, 106.20, 108.20, 106.20, 0.18, "B.Cu", ts)
# reconnect west TS network — old spine fed west from 108.2,107.25; add F stub up
t = add_segment(t, 108.20, 106.20, 108.20, 107.25, 0.18, "F.Cu", ts)

# EPD_RST: ensure connection from (104,85.9) to vertical at 100.55
# After nudge we have (104,85.9)-(100.55,85.9) and (100.55,85.9)-(100.55,83.15)
# May need link from original tree at 100.75 — check unc later

# BTN2: move vertical x=98.5 → 98.25 to clear TP6 OPT @99.0
t, k = del_segments_at(t, 98.5, 95.6, 98.5, 112.2)
print(f"del BTN2 vert {k}")
# also horiz at 112.2 from 98.5
t, k = del_segments_at(t, 98.5, 112.2, 112.8, 112.2)
print(f"del BTN2 horiz {k}")
btn2 = netnum(t, "BTN2")
t = add_segment(t, 98.25, 95.6, 98.25, 112.2, 0.18, "B.Cu", btn2)
t = add_segment(t, 98.25, 112.2, 112.8, 112.2, 0.18, "B.Cu", btn2)

save(t)
print("X7 done")
