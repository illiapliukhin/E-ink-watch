#!/usr/bin/env python3
"""Pass-W2c: Cap + neighbor rearrange to open PMIC pocket."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, move_fp, add_segment, add_via, netnum

t = load()

# Strip invalid fanouts + VSYS@106.1 bar
dels = [
    (112.8, 105.32, 112.8, 105.4),
    (112.8, 103.52, 112.2, 103.52),
    (112.51, 103.5, 112.51, 102.4),
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    (113.0, 106.0, 113.0, 107.4),
    (111.8, 106.1, 112.05, 106.1),
    (112.05, 106.1, 112.05, 105.6),
    (117.412, 106.1, 111.8, 106.1),
    (117.412, 104.5, 117.412, 106.1),
    # CD east from U2 — will re-route
    (110.6, 106.8, 112.8, 106.8),
    # PMIC_INT stub that kisses CD
    (110.6, 106.4, 110.6, 106.7),
    (110.6, 106.7, 110.4, 106.7),
]
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    print(f"del ({a},{b})-({c},{d}) -> {k}")

t = re.sub(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n', '', t)

# Move ILIM via 113.44,105.35 → 113.20,105.90 (north, clear MP)
# Via move via regex
def move_via(t, ox, oy, nx, ny):
    pat = rf'(\t\(via\n\t\t\(at ){ox} {oy}(\)\n)'
    # try float variants
    for oxs in [str(ox), f"{ox:.2f}", f"{ox:.3f}"]:
        for oys in [str(oy), f"{oy:.2f}", f"{oy:.3f}"]:
            p = rf'(\t\(via\n\t\t\(at ){re.escape(oxs)} {re.escape(oys)}(\))'
            if re.search(p, t):
                t2, n = re.subn(p, rf'\g<1>{nx} {ny}\g<2>', t, count=1)
                if n:
                    print(f"via ({oxs},{oys})->({nx},{ny})")
                    return t2
    print(f"WARN via ({ox},{oy}) not found")
    return t

t = move_via(t, 113.44, 105.35, 113.15, 105.95)

# Footprints
t = move_fp(t, "C_SYS", 113.20, 102.00)
t = move_fp(t, "C_VINLS", 112.50, 104.50)
t = move_fp(t, "C_LDO", 112.40, 109.20)
t = move_fp(t, "C_PMID", 112.30, 103.30)
t = move_fp(t, "R_IPRETERM", 115.60, 102.90)  # east clear of C_SYS
t = move_fp(t, "J_STRAP_R", 116.20, 100.50)  # +1.2mm east → MP ~115.2,104.65

save(t)
print("W2c placement saved")
