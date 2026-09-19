#!/usr/bin/env python3
"""Pass-W8: Restore TS Pass-T routing; clear stale TS vias; VSYS via east; CD on B."""
import sys, re
sys.path.insert(0, "tools")
from _pass_w_sexpr_lib import load, save, del_segments_at, add_segment, add_via, netnum

t = load()

def del_via_xy(t, x, y):
    lines = t.splitlines(keepends=True)
    out = []; i = 0; n = 0
    targets = {f'(at {x} {y})', f'(at {x:.2f} {y:.2f})', f'(at {x:.1f} {y:.1f})',
               f'(at {x:g} {y:g})'}
    # also int forms
    if float(x)==int(float(x)) and float(y)==int(float(y)):
        targets.add(f'(at {int(float(x))} {int(float(y))})')
    while i < len(lines):
        if lines[i] == '\t(via\n' and i+1 < len(lines):
            at = lines[i+1].strip()
            if any(at.startswith(s) or s in at for s in targets) or at in {f'(at {x} {y})'}:
                # match more loosely
                m = re.match(r'\(at ([0-9.]+) ([0-9.]+)\)', at)
                if m and abs(float(m.group(1))-float(x))<0.01 and abs(float(m.group(2))-float(y))<0.01:
                    i += 1
                    while i < len(lines) and lines[i] not in ('\t)\n', '\t)'):
                        i += 1
                    if i < len(lines):
                        i += 1
                    n += 1
                    continue
        out.append(lines[i]); i += 1
    return ''.join(out), n

for x,y in [(111.0,107.15),(111.00,107.15),(110.50,107.40),(110.5,107.4),
            (108.20,107.40),(108.2,107.4),(108.20,107.15)]:
    t, n = del_via_xy(t, x, y)
    if n: print(f"del via ({x},{y}) n={n}")

# Remove our TS F/B segments
for a,b,c,d in [
    (111.00,107.30,110.50,107.30),
    (110.50,107.30,110.50,107.40),
    (110.50,107.40,108.20,107.40),
    (110.6,106.8,110.9,106.8),
    (110.9,106.8,110.9,108.00),
    (110.9,108.00,113.3,108.00),
    (113.3,108.00,113.3,108.41),
    (111.80,105.60,112.55,105.60),
    (112.55,105.60,112.55,105.55),
    (112.55,105.55,112.55,103.70),
    (112.55,103.70,117.40,103.70),
    (117.40,103.70,117.40,104.50),
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

t, n = del_via_xy(t, 112.55, 105.55)
print(f"del VSYS via 112.55 n={n}")

vs, ts, cd, pi = [netnum(t,n) for n in ("VSYS","TS","CD","PMIC_INT")]

# Restore TS west spine at y=107.25 (Pass-T)
t = add_segment(t, 111.0, 107.25, 108.2, 107.25, 0.18, "F.Cu", ts)
t = add_segment(t, 111.0, 107.30, 111.0, 107.25, 0.18, "F.Cu", ts)

# VSYS via farther east (113.20, 105.55) — clear ILIM B ending ~113?
# ILIM B (110.3,105.35) length 3.14 → ends ~113.44. Via at 113.8,105.55
t = add_via(t, 113.80, 105.55, 0.45, 0.30, vs)
t = add_segment(t, 111.80, 105.60, 113.80, 105.60, 0.25, "F.Cu", vs)
t = add_segment(t, 113.80, 105.60, 113.80, 105.55, 0.25, "F.Cu", vs)
t = add_segment(t, 113.80, 105.55, 113.80, 103.70, 0.30, "B.Cu", vs)
t = add_segment(t, 113.80, 103.70, 117.40, 103.70, 0.30, "B.Cu", vs)
t = add_segment(t, 117.40, 103.70, 117.40, 104.50, 0.30, "B.Cu", vs)

# CD on B: via near E2, B east, via to R_CD
t = add_via(t, 110.60, 106.95, 0.40, 0.25, cd)
t = add_segment(t, 110.60, 106.80, 110.60, 106.95, 0.18, "F.Cu", cd)
t = add_via(t, 113.30, 108.41, 0.45, 0.30, cd)  # may already exist — check
# if CD via already at 113.3,108.41, don't duplicate
if t.count('(at 113.3 108.41)') + t.count('(at 113.30 108.41)') < 1:
    t = add_via(t, 113.30, 108.41, 0.45, 0.30, cd)
t = add_segment(t, 110.60, 106.95, 113.30, 108.41, 0.20, "B.Cu", cd)

# Ensure PMIC_INT west stub exists
if '(start 110.6 106.4)' not in t and '(start 110.60 106.40)' not in t:
    t = add_segment(t, 110.6, 106.4, 110.4, 106.4, 0.15, "F.Cu", pi)

save(t)
print("W8 done")
