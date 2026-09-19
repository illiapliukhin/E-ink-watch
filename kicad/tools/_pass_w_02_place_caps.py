#!/usr/bin/env python3
"""Pass-W2: Relocate C_SYS / C_VINLS / C_LDO; strip old fanouts; leave nets to reconnect."""
import sys
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import (
    load, save, del_segments_at, move_fp, add_segment, add_via, netnum
)

t = load()

# --- Strip fanouts that will be invalid ---
dels = [
    # C_VINLS GND stubs
    (112.8, 105.32, 112.8, 105.4),
    (112.8, 105.4, 112.8, 105.4),  # zero-length blob
    # C_SYS / C_PMID shared GND
    (112.8, 103.52, 112.2, 103.52),
    (112.51, 103.5, 112.51, 102.4),
    # 3V3_DISP east past x=112.3 (truncate later more carefully)
    (111.8, 106.0, 113.0, 106.0),
    (111.8, 106.0, 113.5, 106.0),
    (113.5, 106.0, 113.5, 106.32),
    # B 3V3_DISP near old C_LDO
    (113.0, 106.0, 113.0, 107.4),
]
total = 0
for a,b,c,d in dels:
    t, k = del_segments_at(t, a, b, c, d)
    print(f"del ({a},{b})-({c},{d}) -> {k}")
    total += k

# Also delete zero-length GND at 112.8,105.4 via regex
import re
pat = re.compile(
    r'\t\(segment\n\t\t\(start 112\.8 105\.4\)\n\t\t\(end 112\.8 105\.4\)\n'
    r'\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net \d+\)\n'
    r'\t\t\(uuid "[^"]+"\)\n\t\)\n'
)
t, n0 = pat.subn('', t)
print(f"del zero-len GND blobs {n0}")

# Move footprints
# C_SYS north of J_STRAP_R MP (MP north edge ~103.65)
t = move_fp(t, "C_SYS", 112.8, 102.55)
# C_VINLS south-park near U2, clear of 3V3_DISP@106 and SW via@111.55,104.55
t = move_fp(t, "C_VINLS", 112.55, 104.55)
# C_LDO south-east, clear LSCTRL via@111.55,107.15 and 3V3 via@114.3,107.95
t = move_fp(t, "C_LDO", 113.2, 108.0)

save(t)
print(f"W2 placement done, dels~{total}")
