#!/usr/bin/env python3
"""Pass-W7: Remove stale VSYS via; jog VSYS B clear of ILIM; TS via west; CD clear SDA."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()

# Delete via at 112.25 105.60 if present
def del_via(t, x, y):
    pat = (
        rf'\t\(via\n'
        rf'\t\t\(at {x} {y}\)\n'
        rf'\t\t\(size [^\)]+\)\n'
        rf'\t\t\(drill [^\)]+\)\n'
        rf'\t\t\(layers [^)]+\)\n'
        rf'\t\t\(net \d+\)\n'
        rf'\t\t\(uuid "[^"]+"\)\n'
        rf'\t\)\n'
    )
    t2, n = re.subn(pat, '', t)
    # try without uuid (some vias)
    if n == 0:
        pat2 = (
            rf'\t\(via\n'
            rf'\t\t\(at {x} {y}\)\n'
            rf'(?:.*\n)*?'
            rf'\t\)\n'
        )
        # more careful line-based
        lines = t.splitlines(keepends=True)
        out = []; i = 0; n = 0
        while i < len(lines):
            if lines[i] == '\t(via\n' and i+1 < len(lines) and f'(at {x} {y})' in lines[i+1]:
                # skip until closing \t)\n at via level
                i += 1
                while i < len(lines) and not (lines[i] == '\t)\n' or lines[i] == '\t)'):
                    i += 1
                if i < len(lines):
                    i += 1
                n += 1
                continue
            out.append(lines[i]); i += 1
        return ''.join(out), n
    return t2, n

t, n = del_via(t, "112.25", "105.6")
print(f"del VSYS via 112.25,105.6 -> {n}")
t, n = del_via(t, "112.25", "105.60")
print(f"del VSYS via 112.25,105.60 -> {n}")

# Delete TS vias we added and CD path; redo
t, n = del_via(t, "111", "107.15")
print(f"del TS via 111,107.15 -> {n}")
t, n = del_via(t, "111.00", "107.15")
print(f"del TS via 111.00,107.15 -> {n}")
t, n = del_via(t, "108.20", "107.15")
print(f"del TS via 108.20 -> {n}")
t, n = del_via(t, "108.2", "107.15")
print(f"del TS via 108.2 -> {n}")

for a,b,c,d in [
    (111.00, 107.30, 111.00, 107.15),
    (111.00, 107.15, 108.20, 107.15),
    (110.6, 106.8, 111.2, 106.8),
    (111.2, 106.8, 111.2, 107.10),
    (111.2, 107.10, 113.3, 107.10),
    (113.3, 107.10, 113.3, 108.41),
    (112.55, 105.55, 112.55, 103.90),
    (112.55, 103.90, 117.40, 103.90),
    (117.40, 103.90, 117.40, 104.50),
    (111.80, 105.60, 112.55, 105.60),
    (112.55, 105.60, 112.55, 105.55),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del seg {k} ({a},{b})-({c},{d})")

vs, ts, cd = netnum(t,"VSYS"), netnum(t,"TS"), netnum(t,"CD")

# Ensure VSYS via at 112.55,105.55 exists
if '(at 112.55 105.55)' not in t:
    t = add_via(t, 112.55, 105.55, 0.45, 0.30, vs)
    print("added VSYS via 112.55")

t = add_segment(t, 111.80, 105.60, 112.55, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 112.55, 105.60, 112.55, 105.55, 0.25, "F.Cu", vs)
# B path y=103.70 clear of SW@104.5 and ILIM B ~105.35
t = add_segment(t, 112.55, 105.55, 112.55, 103.70, 0.30, "B.Cu", vs)
t = add_segment(t, 112.55, 103.70, 117.40, 103.70, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 103.70, 117.40, 104.50, 0.30, "B.Cu", vs)

# TS via at (110.50, 107.40) — west of SCL, south of SDA row
t = add_via(t, 110.50, 107.40, 0.40, 0.25, ts)
t = add_segment(t, 111.00, 107.30, 110.50, 107.30, 0.18, "F.Cu", ts)
t = add_segment(t, 110.50, 107.30, 110.50, 107.40, 0.18, "F.Cu", ts)
t = add_via(t, 108.20, 107.40, 0.40, 0.25, ts)
t = add_segment(t, 110.50, 107.40, 108.20, 107.40, 0.18, "B.Cu", ts)

# CD: from E2 south-east avoiding SDA — go to (110.6,106.8)-(110.9,106.8)-(110.9,108.0)-(113.3,108.0)-(113.3,108.41)
t = add_segment(t, 110.6, 106.8, 110.9, 106.8, 0.18, "F.Cu", cd)
t = add_segment(t, 110.9, 106.8, 110.9, 108.00, 0.18, "F.Cu", cd)
t = add_segment(t, 110.9, 108.00, 113.3, 108.00, 0.20, "F.Cu", cd)
t = add_segment(t, 113.3, 108.00, 113.3, 108.41, 0.20, "F.Cu", cd)

save(t)
print("W7 done")
