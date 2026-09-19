#!/usr/bin/env python3
"""Pass-X28: TS spine y=107.40 (south of R_SDA) for shorting=0."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, netnum

t = load()
t, k = del_segments_at(t, 111.0, 107.25, 108.2, 107.25)
print(f"del spine {k}")
# reconnect vertical to new spine
ts = netnum(t, "TS")
# ensure vertical reaches 107.40
t, k = del_segments_at(t, 111.0, 106.0, 111.0, 107.25)
print(f"del vert {k}")
t, k = del_segments_at(t, 111.0, 106.0, 111.0, 107.30)
print(f"del vert2 {k}")
t = add_segment(t, 111.0, 106.0, 111.0, 107.40, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.40, 108.2, 107.40, 0.18, "F.Cu", ts)
# west network may expect 107.25 — add short jog
t = add_segment(t, 108.2, 107.40, 108.2, 107.25, 0.18, "F.Cu", ts)

save(t)
print("X28 done")
