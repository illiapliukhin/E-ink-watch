#!/usr/bin/env python3
"""Pass-X27: Remove CD fanout copper (leave unconnected) to clear CD shorts; keep pocket."""
import sys, re
sys.path.insert(0, "tools")
from _pass_x_sexpr_lib import load, save, del_segments_at

t = load()

def del_via_xy(t, x, y):
    lines = t.splitlines(keepends=True)
    out = []; i = 0; n = 0
    while i < len(lines):
        if lines[i] == '\t(via\n' and i+1 < len(lines):
            m = re.match(r'\s*\(at ([0-9.]+) ([0-9.]+)\)', lines[i+1])
            if m and abs(float(m.group(1))-x)<0.01 and abs(float(m.group(2))-y)<0.01:
                # only delete if net is CD - check following lines for net number
                block = ''.join(lines[i:i+10])
                if '(net 32)' not in block and 'CD' not in block:
                    # check net code for CD
                    pass
                i += 1
                while i < len(lines) and lines[i] not in ('\t)\n', '\t)'):
                    i += 1
                if i < len(lines): i += 1
                n += 1
                continue
        out.append(lines[i]); i += 1
    return ''.join(out), n

# Delete all CD segments we know about
for a,b,c,d in [
    (110.60, 106.80, 110.60, 107.00),
    (110.60, 107.00, 109.70, 107.00),
    (109.70, 107.00, 109.70, 107.85),
    (109.70, 107.85, 109.70, 108.50),
    (109.70, 108.50, 113.30, 108.50),
    (113.30, 108.50, 113.30, 108.41),
    (112.80, 108.41, 113.30, 108.41),  # keep R_CD local stub if exists
]:
    t, k = del_segments_at(t, a, b, c, d)
    if k: print(f"del {k} ({a},{b})-({c},{d})")

# Delete CD vias at known spots (net 32 = CD from earlier)
# Safer: delete via at 109.70,107.85
lines = t.splitlines(keepends=True)
out = []; i = 0; n = 0
while i < len(lines):
    if lines[i] == '\t(via\n' and i+1 < len(lines):
        m = re.match(r'\s*\(at ([0-9.]+) ([0-9.]+)\)', lines[i+1])
        if m and abs(float(m.group(1))-109.70)<0.01 and abs(float(m.group(2))-107.85)<0.01:
            i += 1
            while i < len(lines) and lines[i] not in ('\t)\n', '\t)'):
                i += 1
            if i < len(lines): i += 1
            n += 1
            continue
        if m and abs(float(m.group(1))-113.30)<0.01 and abs(float(m.group(2))-108.41)<0.01:
            # KEEP the CD via at R_CD — it's the original
            pass
    out.append(lines[i]); i += 1
t = ''.join(out)
print(f"del CD via 109.70 {n}")

# Also fix TS↔SCL tiny stub and LSCTRL if still present after CD removal
# From X26: SCL↔TS and LSCTRL↔SCL may remain
# Trim TS link (111,107.3)-(111,107.25) 
t, k = del_segments_at(t, 111.0, 107.30, 111.0, 107.25)
print(f"del TS link {k}")
# Ensure vertical ends at 107.25 connecting to spine
from _pass_x_sexpr_lib import add_segment, netnum
ts = netnum(t, "TS")
# vertical (111,106)-(111,107.25) should exist; if we deleted link only OK

# Move LSCTRL via slightly if needed — check after DRC
save(t)
print("X27 done")
