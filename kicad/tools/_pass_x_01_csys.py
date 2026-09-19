#!/usr/bin/env python3
"""Pass-X1: Move C_SYS to (117.80, 103.60) by L_SYS; strip old fanouts; reconnect VSYS/GND."""
import sys, re
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, add_via, netnum

t = load()
# Strip old C_SYS-area stubs that won't reach new pads
for a,b,c,d in [
    (112.8, 103.52, 112.2, 103.52),
    (112.51, 103.5, 112.51, 102.4),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k}")

t = move_fp(t, "C_SYS", 117.80, 103.60)
save(t)
print("X1 C_SYS moved")
