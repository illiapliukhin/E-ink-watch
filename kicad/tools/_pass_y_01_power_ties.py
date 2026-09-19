#!/usr/bin/env python3
"""Pass-Y1: high-value power copper ties + PMID via annular. Gate: shorting=0."""
import re, sys
sys.path.insert(0, "tools")
from _pass_y_sexpr_lib import load, save, add_segment, add_via, netnum, del_segments_at

t = load()
gnd = netnum(t, "GND")
iset = netnum(t, "ISET")
ipre = netnum(t, "IPRETERM")
vsys = netnum(t, "VSYS")
vbat = netnum(t, "VBAT")
disp = netnum(t, "3V3_DISP")
pmid = netnum(t, "PMID")

# 1) C_VINLS GND (112.5,104.02) -> GND track/C_PMID area @y=103.52
t = add_segment(t, 112.5, 104.02, 112.5, 103.52, 0.25, "F.Cu", gnd)
t = add_segment(t, 112.5, 103.52, 112.2, 103.52, 0.25, "F.Cu", gnd)
print("C_VINLS GND tied")

# 2) R_CD GND (112.8,107.24) -> C_LDO GND (113.5,107.28)
t = add_segment(t, 112.8, 107.24, 113.5, 107.28, 0.2, "F.Cu", gnd)
print("R_CD-C_LDO GND")

# 3) IPRETERM: R pad (114.29,102.9) -> via (113.29,102.8)
t = add_segment(t, 114.29, 102.9, 113.29, 102.9, 0.15, "F.Cu", ipre)
t = add_segment(t, 113.29, 102.9, 113.29, 102.8, 0.15, "F.Cu", ipre)
print("IPRETERM tied")

# 4) VBAT: bridge (108.12,105.6)-(110.2,105.6)
t = add_segment(t, 108.12, 105.6, 110.2, 105.6, 0.25, "F.Cu", vbat)
print("VBAT bridge")

# 5) 3V3_DISP: via at (113,106) to join F and B
t = add_via(t, 113.0, 106.0, 0.45, 0.2, disp)
print("3V3_DISP via")

# 6) ISET: R_ISET (109.71,103.5) to U2 C1 (110.2,106.0) via B
# F stub south/east then via, B to near C1, via up
t = add_segment(t, 109.71, 103.5, 109.71, 104.2, 0.15, "F.Cu", iset)
t = add_via(t, 109.71, 104.2, 0.4, 0.2, iset)
t = add_segment(t, 109.71, 104.2, 110.2, 104.2, 0.15, "B.Cu", iset)
t = add_segment(t, 110.2, 104.2, 110.2, 106.0, 0.15, "B.Cu", iset)
t = add_via(t, 110.2, 105.85, 0.4, 0.2, iset)  # below C1
t = add_segment(t, 110.2, 105.85, 110.2, 106.0, 0.15, "F.Cu", iset)
print("ISET tied")

# 7) VSYS: connect R_VSYS (107.1,104.625) east on B to VSYS network
# Existing stubs at (107.1,104.4)-(107.1,104.625). Via and B to (112.5,105.6) via area
t = add_via(t, 107.1, 104.5, 0.45, 0.2, vsys)
t = add_segment(t, 107.1, 104.625, 107.1, 104.5, 0.25, "F.Cu", vsys)
t = add_segment(t, 107.1, 104.5, 112.5, 104.5, 0.25, "B.Cu", vsys)
t = add_segment(t, 112.5, 104.5, 112.5, 105.6, 0.25, "B.Cu", vsys)
print("VSYS R_VSYS tied")

# 8) Enlarge PMID via 0.45/0.3 -> 0.5/0.3 (annular 0.1)
old = re.search(
    r'(\t\(via\n\t\t\(at 111\.35 103\.85\)\n\t\t\(size )0\.45(\n\t\t\(drill 0\.3\))',
    t,
)
if old:
    t = t[:old.start(1)] + old.group(1) + "0.5" + old.group(2) + t[old.end(2):]
    # fix: the replace is wrong. Do properly:
t = re.sub(
    r'(\t\(via\n\t\t\(at 111\.35 103\.85\)\n\t\t\(size )0\.45(\n\t\t\(drill 0\.3\)\n)',
    r'\g<1>0.5\2',
    t,
    count=1,
)
print("PMID via annular enlarged")

# 9) C_SYS GND (117.8,103.12) -> via or track; nearest J_STRAP pad9 (116.85,102.25)
t = add_segment(t, 117.8, 103.12, 117.8, 102.25, 0.25, "F.Cu", gnd)
t = add_segment(t, 117.8, 102.25, 116.85, 102.25, 0.25, "F.Cu", gnd)
print("C_SYS GND tied")

# 10) R_ILIM GND (116.11,106.6) -> nearby; B track mentioned at 115.55,106 - use via
t = add_segment(t, 116.11, 106.6, 116.11, 106.0, 0.2, "F.Cu", gnd)
t = add_via(t, 116.11, 106.0, 0.45, 0.2, gnd)
# try connect B toward 115.55,106
t = add_segment(t, 116.11, 106.0, 115.55, 106.0, 0.2, "B.Cu", gnd)
print("R_ILIM GND tied")

save(t)
print("Y1 saved")
