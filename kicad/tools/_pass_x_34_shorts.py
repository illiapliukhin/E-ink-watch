#!/usr/bin/env python3
"""Pass-X34: fix SCL B-hop, VSYS vs MP, ILIM vs TS."""
import sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum
import re

t = load()

# --- SCL: remove X33 hop, redo ---
scl = netnum(t, "SCL")
for a,b,c,d in [
    (111.8,106.8,112.55,106.8),
    (112.55,106.8,112.55,108.65),
    (112.55,108.65,111.14,108.65),
    (111.14,108.65,111.14,108.2),
]:
    t, k = del_segments_at(t, a,b,c,d); print(f"del SCL seg {k}")

# delete SCL vias at 112.55,106.8 and 111.14,108.65
def del_via_at(t, x, y):
    pat = (
        rf'\t\(via\n'
        rf'\t\t\(at {x} {y}\)\n'
        rf'\t\t\(size [^\)]+\)\n'
        rf'\t\t\(drill [^\)]+\)\n'
        rf'\t\t\(layers "[^"]+" "[^"]+"\)\n'
        rf'\t\t\(net \d+\)\n'
        rf'\t\t\(uuid "[^"]+"\)\n'
        rf'\t\)\n'
    )
    # also try float variants
    n = 0
    def repl(m):
        nonlocal n; n += 1; return ''
    t2, c = re.subn(pat, repl, t)
    if c == 0:
        # try with .0
        pat2 = pat.replace(f'{x} {y}', f'{x:.2f} {y}' if isinstance(y,float) else f'{x} {y}')
    return t2 if c else t, c

t, k = del_via_at(t, 112.55, 106.8); print("del via1", k)
t, k = del_via_at(t, "112.55", "106.8"); print("del via1b", k)
t, k = del_via_at(t, 111.14, 108.65); print("del via2", k)

# New SCL: F east to 112.25, via, B east to 113.9 (clear 3V3 via + R_CD), south, west, via up to pad
t = add_segment(t, 111.8, 106.8, 112.25, 106.8, 0.18, "F.Cu", scl)
t = add_via(t, 112.25, 106.8, 0.4, 0.2, scl)
t = add_segment(t, 112.25, 106.8, 113.9, 106.8, 0.18, "B.Cu", scl)
t = add_segment(t, 113.9, 106.8, 113.9, 108.65, 0.18, "B.Cu", scl)
t = add_segment(t, 113.9, 108.65, 111.14, 108.65, 0.18, "B.Cu", scl)
t = add_via(t, 111.14, 108.65, 0.4, 0.2, scl)
t = add_segment(t, 111.14, 108.65, 111.14, 108.2, 0.18, "F.Cu", scl)

# --- VSYS jog clear of J_STRAP MP ---
vsys = netnum(t, "VSYS")
t, k = del_segments_at(t, 111.8, 105.6, 116.6, 105.6); print("del VSYS bar", k)
t, k = del_segments_at(t, 116.6, 105.6, 116.6, 105.5); print("del VSYS stub", k)
# (111.8,105.6)-(112.8,105.6)-(112.8,106.10)-(116.6,106.10)-(116.6,105.5)
t = add_segment(t, 111.8, 105.6, 112.8, 105.6, 0.25, "F.Cu", vsys)
t = add_segment(t, 112.8, 105.6, 112.8, 106.10, 0.25, "F.Cu", vsys)
t = add_segment(t, 112.8, 106.10, 116.6, 106.10, 0.25, "F.Cu", vsys)
t = add_segment(t, 116.6, 106.10, 116.6, 105.5, 0.25, "F.Cu", vsys)

# --- ILIM via nudge west/south of TS pad ---
ilim = netnum(t, "ILIM")
t, k = del_segments_at(t, 110.6, 106, 110.75, 106); print("del ILIM F", k)
t, k = del_segments_at(t, 110.75, 106, 110.3, 106); print("del ILIM B", k)
# delete via 110.75,106
t, k = del_via_at(t, 110.75, 106); print("del ILIM via", k)
t, k = del_via_at(t, "110.75", "106"); print("del ILIM via b", k)
# new: F stub to (110.45, 106.25), via there, B to (110.3,106.25)-(110.3,105.35) network
t = add_segment(t, 110.6, 106.0, 110.45, 106.25, 0.15, "F.Cu", ilim)
t = add_via(t, 110.45, 106.25, 0.45, 0.2, ilim)
t = add_segment(t, 110.45, 106.25, 110.3, 106.25, 0.15, "B.Cu", ilim)
t = add_segment(t, 110.3, 106.25, 110.3, 105.35, 0.15, "B.Cu", ilim)
# old B (110.3,106)-(110.3,105.35) may remain - ok parallel

save(t)
print("X34 done")
