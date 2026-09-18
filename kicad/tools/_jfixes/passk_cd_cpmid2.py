"""Priority A: R_SCL -0.25 + TS spur del.
Priority B careful: C_PMID → 111.75, rebuild PMID fanout east of VBUS (no VBUS edits).
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
    fp.SetPosition(pcbnew.VECTOR2I(mm(x + DX), mm(y))); n += 1
    print(f"R_SCL -> {x+DX:.3f},{y:.3f}")

to_remove = []
for t in tracks:
    cls = t.GetClass(); net = t.GetNetname()
    if cls == "PCB_VIA" and net == "3V3":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if abs(x - OLD["2"][0]) < 0.05 and abs(y - OLD["2"][1]) < 0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(NEW["2"][0]), mm(NEW["2"][1]))); n += 1
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
    # Old C_PMID PMID copper that skims VBUS
    if net == "PMID" and t.GetLayer() == pcbnew.F_Cu:
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        # vertical on pad1 x
        if abs(sx - 110.520) < 0.05 and abs(ex - 110.520) < 0.05:
            if min(sy, ey) <= 104.35 and max(sy, ey) >= 104.25:
                to_remove.append(t)
        # diagonal from pad1
        if (abs(sx - 110.520) < 0.05 and abs(sy - 104.300) < 0.05) or \
           (abs(ex - 110.520) < 0.05 and abs(ey - 104.300) < 0.05):
            to_remove.append(t)
        # stub (111.0,105.2)-(110.52,105.2)
        if abs(sy - 105.200) < 0.05 and abs(ey - 105.200) < 0.05:
            if min(sx, ex) <= 110.55 and max(sx, ex) >= 110.95:
                to_remove.append(t)

seen=set()
uniq=[]
for t in to_remove:
    i=id(t)
    if i in seen: continue
    seen.add(i); uniq.append(t)
for t in uniq:
    board.Remove(t); n += 1
print(f"removed {len(uniq)}")

# Move C_PMID
NEW_CX, NEW_CY = 111.750, 104.300
NEW_P1 = (111.270, 104.300)  # -0.48
NEW_P2 = (112.230, 104.300)
for fp in board.GetFootprints():
    if fp.GetReference() != "C_PMID":
        continue
    fp.SetPosition(pcbnew.VECTOR2I(mm(NEW_CX), mm(NEW_CY))); n += 1
    print(f"C_PMID -> {NEW_CX},{NEW_CY}")

# Rebuild PMID: pad1 -> up to y=105.20 at x=111.27 -> to U2 A3/B3 area (111.0,105.2)
nc = board.GetNetInfo().GetNetItem("PMID").GetNetCode(); F = pcbnew.F_Cu
for x1, y1, x2, y2, w in [
    (NEW_P1[0], NEW_P1[1], NEW_P1[0], 105.200, 0.25),
    (NEW_P1[0], 105.200, 111.000, 105.200, 0.25),
]:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc)
    board.Add(t); n += 1
print("PMID fanout rebuilt")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
