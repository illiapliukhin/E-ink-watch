#!/usr/bin/env python3
"""Pass-W min2: move C_VINLS only + delete 3V3_DISP overlap stubs. No new copper."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp

t = load()
dels = [
    (112.8, 105.32, 112.8, 105.4),
    (111.8, 106.0, 113.0, 106.0),  # keeps (111.8,106)-(113.5,106)? delete both east arms
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    print(f"del {k}")
t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

t = move_fp(t, "C_VINLS", 112.50, 104.50)
# Do NOT move C_SYS this time
save(t)
print("min2 move-only")
