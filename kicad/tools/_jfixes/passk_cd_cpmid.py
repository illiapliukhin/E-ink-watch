"""R_SCL -0.25X + TS spur del + C_PMID +0.50X (clear PMID↔VBUS vs VBUS@x=110.6).
Do not touch VBUS tracks near y=102.9 / latent via.
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

def tomm(v): return v / 1e6
def mm(v): return int(round(float(v) * 1e6))

n = 0
tracks = list(board.GetTracks())

# --- R_SCL ---
DX = -0.25
OLD = {"1": (111.390, 107.600), "2": (112.410, 107.600)}
NEW = {k: (x + DX, y) for k, (x, y) in OLD.items()}
ALLOW = {"SCL", "3V3"}

for fp in board.GetFootprints():
    if fp.GetReference() != "R_SCL":
        continue
    x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x + DX), mm(y)))
    n += 1
    print(f"R_SCL -> {x+DX:.3f},{y:.3f}")

to_remove = []
for t in tracks:
    cls = t.GetClass(); net = t.GetNetname()
    if cls == "PCB_VIA" and net == "3V3":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if abs(x - OLD["2"][0]) < 0.05 and abs(y - OLD["2"][1]) < 0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(NEW["2"][0]), mm(NEW["2"][1])))
            n += 1
        continue
    if cls == "PCB_VIA":
        continue
    if net in ALLOW:
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
        if net == "3V3" and t.GetLayer() == pcbnew.F_Cu:
            sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
            ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
            if abs(sx - OLD["2"][0]) < 0.05:
                t.SetStart(pcbnew.VECTOR2I(mm(sx + DX), mm(sy))); n += 1
            if abs(ex - OLD["2"][0]) < 0.05:
                t.SetEnd(pcbnew.VECTOR2I(mm(ex + DX), mm(ey))); n += 1
    if net == "TS" and t.GetLayer() == pcbnew.F_Cu:
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        if ((abs(sx - 107.690) < 0.05 and abs(sy - 107.550) < 0.05 and
             abs(ex - 111.390) < 0.05 and abs(ey - 107.600) < 0.05) or
            (abs(ex - 107.690) < 0.05 and abs(ey - 107.550) < 0.05 and
             abs(sx - 111.390) < 0.05 and abs(sy - 107.600) < 0.05)):
            to_remove.append(t)

for t in to_remove:
    board.Remove(t); n += 1
print(f"TS removed {len(to_remove)}")

# --- C_PMID +0.50X ---
CP_DX = 0.50
OLD_CP1 = (110.520, 104.300)  # PMID
OLD_CP2 = (111.480, 104.300)  # GND
NEW_CP1 = (OLD_CP1[0] + CP_DX, OLD_CP1[1])
NEW_CP2 = (OLD_CP2[0] + CP_DX, OLD_CP2[1])
# refresh tracks list after removes — load from board carefully
tracks2 = []
try:
    tracks2 = list(board.GetTracks())
except TypeError:
    # fallback: reopen
    pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
    board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
    tracks2 = list(board.GetTracks())

for fp in board.GetFootprints():
    if fp.GetReference() != "C_PMID":
        continue
    x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x + CP_DX), mm(y)))
    n += 1
    print(f"C_PMID -> {x+CP_DX:.3f},{y:.3f}")

for t in tracks2:
    if t.GetClass() == "PCB_VIA":
        continue
    if t.GetNetname() not in ("PMID", "GND"):
        continue
    # only retarget ends that sat on C_PMID pads — do not move latent via or random GND
    for end_name in ("Start", "End"):
        pt = t.GetStart() if end_name == "Start" else t.GetEnd()
        px, py = tomm(pt.x), tomm(pt.y)
        for (ox, oy), (nx, ny) in [(OLD_CP1, NEW_CP1), (OLD_CP2, NEW_CP2)]:
            if abs(px - ox) < 0.10 and abs(py - oy) < 0.10:
                if end_name == "Start":
                    t.SetStart(pcbnew.VECTOR2I(mm(nx), mm(ny)))
                else:
                    t.SetEnd(pcbnew.VECTOR2I(mm(nx), mm(ny)))
                n += 1

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
