"""R_CD +0.30X; MOVE GND via NE; rebuild CD to enter pad1 from north (no pad2 cross)."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

def tomm(v): return v / 1e6
def mm(v): return int(round(float(v) * 1e6))

DX = 0.30
n = 0
tracks = list(board.GetTracks())

for fp in board.GetFootprints():
    if fp.GetReference() != "R_CD":
        continue
    x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x + DX), mm(y)))
    n += 1
    print(f"R_CD -> {x+DX:.3f},{y:.3f}")

NEW_P1 = (112.800 + DX, 107.860)
NEW_P2 = (112.800 + DX, 106.840)  # GND pad — no CD copper here
OLD_VIA = (113.300, 108.410)
NEW_VIA = (114.100, 109.000)

to_remove = []
for t in tracks:
    cls = t.GetClass(); net = t.GetNetname()
    if cls == "PCB_VIA" and net == "GND":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if abs(x - OLD_VIA[0]) < 0.05 and abs(y - OLD_VIA[1]) < 0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(NEW_VIA[0]), mm(NEW_VIA[1])))
            n += 1
            print(f"GND via -> {NEW_VIA}")
        continue
    if cls == "PCB_VIA":
        continue
    # Remove old CD routes near R_CD (will rebuild)
    if net == "CD" and t.GetLayer() == pcbnew.F_Cu:
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        # verticals/horizontals that used x=112.8 in the R_CD column
        if (abs(sx - 112.800) < 0.05 or abs(ex - 112.800) < 0.05) and max(sy, ey) >= 106.7:
            to_remove.append(t)
            print(f"del CD ({sx:.3f},{sy:.3f})-({ex:.3f},{ey:.3f})")
    # Retarget GND stub track ends from old via / 112.8,108.41
    if net == "GND" and t.GetLayer() == pcbnew.F_Cu:
        for end_name in ("Start", "End"):
            pt = t.GetStart() if end_name == "Start" else t.GetEnd()
            px, py = tomm(pt.x), tomm(pt.y)
            if abs(px - OLD_VIA[0]) < 0.08 and abs(py - OLD_VIA[1]) < 0.08:
                if end_name == "Start":
                    t.SetStart(pcbnew.VECTOR2I(mm(NEW_VIA[0]), mm(NEW_VIA[1])))
                else:
                    t.SetEnd(pcbnew.VECTOR2I(mm(NEW_VIA[0]), mm(NEW_VIA[1])))
                n += 1
            if abs(px - 112.800) < 0.08 and abs(py - 108.410) < 0.08:
                # keep left dangling end but don't delete — leave as-is (GND copper preserve)
                pass

for t in to_remove:
    board.Remove(t); n += 1

# Rebuild CD: U2 E2 (110.6,106.8) → east to 113.1 @106.8 → north to 108.20 → east/west to pad1 x → south to pad1
# Avoid y=106.84 pad2: go north of pad1 then down.
nc = board.GetNetInfo().GetNetItem("CD").GetNetCode()
F = pcbnew.F_Cu
px, py = NEW_P1
segs = [
    (110.600, 106.800, 113.100, 106.800, 0.18),  # east, south of pad2? pad2 at 106.84 — skim!
    # Better: leave U2 at 106.8, jog south first then east then north to pad1
]
# Safer path: (110.6,106.8)->(110.6,108.20)->(px,108.20)->(px,py)
segs = [
    (110.600, 106.800, 110.600, 108.200, 0.18),
    (110.600, 108.200, px, 108.200, 0.18),
    (px, 108.200, px, py, 0.18),
]
for x1, y1, x2, y2, w in segs:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc)
    board.Add(t); n += 1
print(f"CD rebuilt to pad1 {px:.3f},{py:.3f}")

# Extend GND stub to new via without deleting old copper: add segment from 112.8,108.41 to new via
# (old track may still end at 113.3 — retarget already done)
gnc = board.GetNetInfo().GetNetItem("GND").GetNetCode()
# ensure connection 112.8,108.41 -> new via if needed
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(112.800), mm(108.410)))
t.SetEnd(pcbnew.VECTOR2I(mm(NEW_VIA[0]), mm(NEW_VIA[1])))
t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(gnc)
board.Add(t); n += 1

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
