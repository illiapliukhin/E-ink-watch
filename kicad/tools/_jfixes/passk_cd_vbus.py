"""Pass K Priority A:
1) R_SCL -0.25X — clear 3V3↔CD while keeping R_SCL.1 clear of R_SDA.2.
2) VBUS dogbone west around C_PMID — clear PMID↔VBUS mash.
Do NOT delete GND copper / latent via.
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

def tomm(v): return v / 1e6
def mm(v): return int(round(float(v) * 1e6))

n = 0

# --- 1) R_SCL west 0.25 ---
DX = -0.25
OLD = {"1": (111.390, 107.600), "2": (112.410, 107.600)}
NEW = {k: (x + DX, y) for k, (x, y) in OLD.items()}

for fp in board.GetFootprints():
    if fp.GetReference() != "R_SCL":
        continue
    x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x + DX), mm(y)))
    n += 1
    print(f"R_SCL -> {x+DX:.3f},{y:.3f}")

tracks = list(board.Tracks())
for t in tracks:
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "3V3":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if abs(x - OLD["2"][0]) < 0.05 and abs(y - OLD["2"][1]) < 0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(NEW["2"][0]), mm(NEW["2"][1])))
            n += 1
            print(f"3V3 via -> {NEW['2'][0]:.3f},{NEW['2'][1]:.3f}")

tracks = list(board.Tracks())
for t in tracks:
    if t.GetClass() == "PCB_VIA":
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

tracks = list(board.Tracks())
for t in tracks:
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

# --- 2) VBUS dogbone: collect removals first ---
to_remove = []
tracks = list(board.Tracks())
for t in tracks:
    if t.GetClass() == "PCB_VIA" or t.GetNetname() != "VBUS" or t.GetLayer() != pcbnew.F_Cu:
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    if abs(sx - 110.600) < 0.05 and abs(ex - 110.600) < 0.05:
        if min(sy, ey) < 105.05:
            to_remove.append(t)
            print(f"del VBUS vert ({sx:.3f},{sy:.3f})-({ex:.3f},{ey:.3f})")
    elif abs(sy - 102.900) < 0.05 and abs(ey - 102.900) < 0.05:
        if min(sx, ex) <= 108.15 and max(sx, ex) >= 110.55:
            to_remove.append(t)
            print(f"del VBUS horiz102.9 ({sx:.3f},{sy:.3f})-({ex:.3f},{ey:.3f})")

for t in to_remove:
    board.Remove(t); n += 1

nc = board.GetNetInfo().GetNetItem("VBUS").GetNetCode()
F = pcbnew.F_Cu
segs = [
    (110.600, 105.200, 110.600, 105.050, 0.30),
    (110.600, 105.050, 109.900, 105.050, 0.30),
    (109.900, 105.050, 109.900, 102.900, 0.30),
    (109.900, 102.900, 108.120, 102.900, 0.30),
]
for x1, y1, x2, y2, w in segs:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc)
    board.Add(t); n += 1
print(f"VBUS dogbone added, removed={len(to_remove)}")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
