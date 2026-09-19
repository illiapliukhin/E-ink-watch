#!/usr/bin/env python3
"""Pass-W2b: Better cap placement + strip + VSYS 106.1 cleanup."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp

t = load()

dels = [
    (112.8, 105.32, 112.8, 105.4),
    (112.8, 103.52, 112.2, 103.52),
    (112.51, 103.5, 112.51, 102.4),
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    (113.0, 106.0, 113.0, 107.4),
    # VSYS near C5 / y=106.1
    (111.8, 106.1, 112.05, 106.1),
    (112.05, 106.1, 112.05, 105.6),
    (117.412, 106.1, 111.8, 106.1),
    (117.412, 104.5, 117.412, 106.1),
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    print(f"del ({a},{b})-({c},{d}) -> {k}")

t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

# Placement — keep clear of MP@(114,104.65), IPRETERM via@(113.29,102.8), R_CD, CD via
t = move_fp(t, "C_SYS", 114.50, 102.20)   # east of IPRETERM, north of MP
t = move_fp(t, "C_VINLS", 112.50, 104.50) # south park by U2
t = move_fp(t, "C_LDO", 115.00, 108.80)   # SE, away from R_CD / CD via
# nudge C_PMID slightly east to open stitch corridor west
t = move_fp(t, "C_PMID", 112.40, 103.35)

save(t)
print("W2b done")
