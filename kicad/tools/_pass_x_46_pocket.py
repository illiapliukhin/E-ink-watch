#!/usr/bin/env python3
"""Pass-X46: VSYS B-hop + ILIM via only (from moves-only)."""
import re, sys
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()
vsys, ilim = netnum(t,"VSYS"), netnum(t,"ILIM")

def del_via_at(t, x, y):
    for xs in {str(x), f"{float(x):.2f}", f"{float(x):g}"}:
        for ys in {str(y), f"{float(y):.2f}", f"{float(y):g}"}:
            pat = (
                rf'\t\(via\n\t\t\(at {re.escape(xs)} {re.escape(ys)}\)\n'
                rf'\t\t\(size [^\)]+\)\n\t\t\(drill [^\)]+\)\n'
                rf'\t\t\(layers "[^"]+" "[^"]+"\)\n\t\t\(net \d+\)\n'
                rf'\t\t\(uuid "[^"]+"\)\n\t\)\n'
            )
            t2,c = re.subn(pat, '', t)
            if c: return t2, c
    return t, 0

for a,b,c,d in [
    (117.412,106.1,111.8,106.1),(117.412,104.5,117.412,106.1),
    (111.8,106.1,112.05,106.1),(112.05,106.1,112.05,105.6),
]:
    t,k=del_segments_at(t,a,b,c,d); print("VSYS del",k)

t = add_segment(t, 112.05, 105.6, 112.5, 105.6, 0.25, "F.Cu", vsys)
t = add_via(t, 112.5, 105.6, 0.45, 0.2, vsys)
t = add_segment(t, 112.5, 105.6, 117.4, 105.6, 0.25, "B.Cu", vsys)
t = add_segment(t, 117.4, 105.6, 117.4, 104.5, 0.25, "B.Cu", vsys)
t = add_via(t, 117.4, 104.5, 0.5, 0.25, vsys)
t = add_segment(t, 117.4, 104.5, 117.8, 104.5, 0.28, "F.Cu", vsys)
t = add_segment(t, 117.8, 104.5, 117.8, 104.08, 0.28, "F.Cu", vsys)

t,k=del_via_at(t,113.44,105.35); print("ILIM via",k)
t,k=del_segments_at(t,110.3,105.35,113.44,105.35); print("ILIM B",k)
t = add_segment(t, 110.3, 105.35, 110.3, 105.2, 0.15, "B.Cu", ilim)
t = add_segment(t, 110.3, 105.2, 114.7, 105.2, 0.15, "B.Cu", ilim)
t = add_segment(t, 114.7, 105.2, 114.7, 106.5, 0.15, "B.Cu", ilim)
t = add_via(t, 114.70, 106.50, 0.5, 0.25, ilim)

save(t)
print("X46 done")
