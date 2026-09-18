"""Move R_CD +0.40X to clear R_SCL.2/3V3 via/track. MOVE (not delete) GND via
@113.30,108.41 further NE so CD pad1 does not mash it. Update CD/GND track ends.
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

def tomm(v): return v / 1e6
def mm(v): return int(round(float(v) * 1e6))

DX = 0.40
# R_CD pads current
OLD_P1 = (112.800, 107.860)  # CD
OLD_P2 = (112.800, 106.840)  # GND
NEW_P1 = (OLD_P1[0] + DX, OLD_P1[1])
NEW_P2 = (OLD_P2[0] + DX, OLD_P2[1])

n = 0
for fp in board.GetFootprints():
    if fp.GetReference() != "R_CD":
        continue
    x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x + DX), mm(y)))
    n += 1
    print(f"R_CD -> {x+DX:.3f},{y:.3f}")

# MOVE GND via 113.30,108.41 -> 114.00,108.90
OLD_VIA = (113.300, 108.410)
NEW_VIA = (114.000, 108.900)
for t in list(board.Tracks()):
    if t.GetClass() != "PCB_VIA" or t.GetNetname() != "GND":
        continue
    x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
    if abs(x - OLD_VIA[0]) < 0.05 and abs(y - OLD_VIA[1]) < 0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(NEW_VIA[0]), mm(NEW_VIA[1])))
        n += 1
        print(f"GND via -> {NEW_VIA[0]:.3f},{NEW_VIA[1]:.3f}")

# Update track ends on old pads / old via. Do NOT delete GND copper — retarget ends.
for t in list(board.Tracks()):
    if t.GetClass() == "PCB_VIA":
        continue
    for end_name in ("Start", "End"):
        pt = t.GetStart() if end_name == "Start" else t.GetEnd()
        px, py = tomm(pt.x), tomm(pt.y)
        targets = [
            (OLD_P1, NEW_P1),
            (OLD_P2, NEW_P2),
            (OLD_VIA, NEW_VIA),
            # GND stub left end was at 112.800,108.410 — extend toward new via
            ((112.800, 108.410), (NEW_VIA[0], NEW_VIA[1])),
        ]
        for (ox, oy), (nx, ny) in targets:
            if abs(px - ox) < 0.08 and abs(py - oy) < 0.08:
                if end_name == "Start":
                    t.SetStart(pcbnew.VECTOR2I(mm(nx), mm(ny)))
                else:
                    t.SetEnd(pcbnew.VECTOR2I(mm(nx), mm(ny)))
                n += 1

# CD vertical at x=112.8: shift x by DX for segments that served R_CD
for t in list(board.Tracks()):
    if t.GetClass() == "PCB_VIA" or t.GetNetname() != "CD" or t.GetLayer() != pcbnew.F_Cu:
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    ch = False
    # vertical spine at old x
    if abs(sx - 112.800) < 0.05 and abs(ex - 112.800) < 0.05:
        t.SetStart(pcbnew.VECTOR2I(mm(sx + DX), mm(sy)))
        t.SetEnd(pcbnew.VECTOR2I(mm(ex + DX), mm(ey)))
        ch = True
    else:
        # horizontal ending at old x=112.8,y=106.8
        if abs(sx - 112.800) < 0.05 and abs(sy - 106.800) < 0.05:
            t.SetStart(pcbnew.VECTOR2I(mm(sx + DX), mm(sy))); ch = True
        if abs(ex - 112.800) < 0.05 and abs(ey - 106.800) < 0.05:
            t.SetEnd(pcbnew.VECTOR2I(mm(ex + DX), mm(ey))); ch = True
    if ch:
        n += 1

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
