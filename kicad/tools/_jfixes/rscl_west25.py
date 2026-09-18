"""R_SCL -0.25X. Clears 3V3↔CD. Only move SCL/3V3 track ends + on-pad via.
Do NOT drag foreign nets (TS) that happen to end near pad1.
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

def tomm(v): return v / 1e6
def mm(v): return int(round(float(v) * 1e6))

DX = -0.25
OLD = {"1": (111.390, 107.600), "2": (112.410, 107.600)}
NEW = {k: (x + DX, y) for k, (x, y) in OLD.items()}
ALLOW = {"SCL", "3V3"}

n = 0
for fp in board.GetFootprints():
    if fp.GetReference() != "R_SCL":
        continue
    x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x + DX), mm(y)))
    n += 1
    print(f"R_SCL -> {x+DX:.3f},{y:.3f}")

for t in list(board.Tracks()):
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "3V3":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if abs(x - OLD["2"][0]) < 0.05 and abs(y - OLD["2"][1]) < 0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(NEW["2"][0]), mm(NEW["2"][1])))
            n += 1
            print(f"3V3 via -> {NEW['2'][0]:.3f},{NEW['2'][1]:.3f}")

for t in list(board.Tracks()):
    if t.GetClass() == "PCB_VIA":
        continue
    if t.GetNetname() not in ALLOW:
        continue
    for end_name in ("Start", "End"):
        pt = t.GetStart() if end_name == "Start" else t.GetEnd()
        px, py = tomm(pt.x), tomm(pt.y)
        for key, (ox, oy) in OLD.items():
            if abs(px - ox) < 0.08 and abs(py - oy) < 0.08:
                nx, ny = NEW[key]
                if end_name == "Start":
                    t.SetStart(pcbnew.VECTOR2I(mm(nx), mm(ny)))
                else:
                    t.SetEnd(pcbnew.VECTOR2I(mm(nx), mm(ny)))
                n += 1

# 3V3 F spine at old pad2 x
for t in list(board.Tracks()):
    if t.GetClass() == "PCB_VIA" or t.GetNetname() != "3V3" or t.GetLayer() != pcbnew.F_Cu:
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    ch = False
    if abs(sx - OLD["2"][0]) < 0.05:
        t.SetStart(pcbnew.VECTOR2I(mm(sx + DX), mm(sy))); ch = True
    if abs(ex - OLD["2"][0]) < 0.05:
        t.SetEnd(pcbnew.VECTOR2I(mm(ex + DX), mm(ey))); ch = True
    if ch:
        n += 1

# Truncate TS track that incorrectly ended on R_SCL pad1 — stop short west of pad1
# Old end (111.390,107.600); pad1 new left ~110.87. Stop at 110.70 or reconnect properly.
# Actually TS should go to U2 C3 @111.000,106.000 / R_TS — not R_SCL.
# Baseline has TS (107.690,107.550)->(111.390,107.600) which skims SCL pad — leave geometry
# but ensure we didn't move it. (We won't, due to ALLOW filter.)

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
