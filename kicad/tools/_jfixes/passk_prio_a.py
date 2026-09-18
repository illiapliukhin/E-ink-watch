"""Pass K Priority A combined:
1) R_SCL -0.25X — clear 3V3↔CD (only SCL/3V3 geometry)
2) Delete dangling TS spur into R_SCL pad1
3) PMIC_INT via south micro-nudge to clear VBAT @y=106.4
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

def tomm(v): return v / 1e6
def mm(v): return int(round(float(v) * 1e6))

n = 0
tracks = list(board.GetTracks())  # snapshot once

# --- 1) R_SCL west ---
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
    cls = t.GetClass()
    net = t.GetNetname()
    if cls == "PCB_VIA" and net == "3V3":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if abs(x - OLD["2"][0]) < 0.05 and abs(y - OLD["2"][1]) < 0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(NEW["2"][0]), mm(NEW["2"][1])))
            n += 1
            print(f"3V3 via -> {NEW['2'][0]:.3f},{NEW['2'][1]:.3f}")
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

    # TS spur
    if net == "TS" and t.GetLayer() == pcbnew.F_Cu:
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        if ((abs(sx - 107.690) < 0.05 and abs(sy - 107.550) < 0.05 and
             abs(ex - 111.390) < 0.05 and abs(ey - 107.600) < 0.05) or
            (abs(ex - 107.690) < 0.05 and abs(ey - 107.550) < 0.05 and
             abs(sx - 111.390) < 0.05 and abs(sy - 107.600) < 0.05)):
            to_remove.append(t)

    # PMIC_INT via + stub
    if cls == "PCB_VIA" and net == "PMIC_INT":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if abs(x - 109.500) < 0.05 and abs(y - 106.400) < 0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(109.500), mm(106.720)))
            n += 1
            print("PMIC_INT via -> 109.500,106.720")
    if cls != "PCB_VIA" and net == "PMIC_INT" and t.GetLayer() == pcbnew.F_Cu:
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        if abs(sy - 106.400) < 0.05 and abs(ey - 106.400) < 0.05:
            if min(sx, ex) <= 109.55 and max(sx, ex) >= 110.55:
                to_remove.append(t)
    if cls != "PCB_VIA" and net == "PMIC_INT" and t.GetLayer() != pcbnew.F_Cu:
        for end_name in ("Start", "End"):
            pt = t.GetStart() if end_name == "Start" else t.GetEnd()
            px, py = tomm(pt.x), tomm(pt.y)
            if abs(px - 109.500) < 0.05 and abs(py - 106.400) < 0.05:
                if end_name == "Start":
                    t.SetStart(pcbnew.VECTOR2I(mm(109.500), mm(106.720)))
                else:
                    t.SetEnd(pcbnew.VECTOR2I(mm(109.500), mm(106.720)))
                n += 1
                print("updated B.Cu PMIC_INT end")

for t in to_remove:
    board.Remove(t); n += 1
print(f"removed {len(to_remove)}")

nc = board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode()
F = pcbnew.F_Cu
for x1, y1, x2, y2, w in [
    (110.600, 106.400, 110.600, 106.720, 0.15),
    (110.600, 106.720, 109.500, 106.720, 0.15),
]:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc)
    board.Add(t); n += 1
print("PMIC_INT dogbone added")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
