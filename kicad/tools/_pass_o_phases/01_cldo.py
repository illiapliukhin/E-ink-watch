#!/usr/bin/env python3
"""Shift C_LDO north clear of R_ILIM/C_PMID row; minimal 3V3_DISP reconnect."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6

# Target: north of passive row (R_ILIM y=106.15), keep ≤3mm to U2.C5
NEW = (113.80, 107.70)  # was (113.50,106.80); ΔY=+0.90
for fp in board.GetFootprints():
    if fp.GetReference() == "C_LDO":
        fp.SetPosition(pcbnew.VECTOR2I(mm(NEW[0]), mm(NEW[1])))
        break

# Remove only stubs that targeted old C_LDO pad2 @(113.5,106.32)
to_remove = []
for t in board.GetTracks():
    if t.GetNetname() != "3V3_DISP" or t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetLayerName() not in ("F.Cu",):
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    # old vertical stub to pad2
    if abs(sx-113.5)<0.05 and abs(ex-113.5)<0.05 and min(sy,ey)>=106.0 and max(sy,ey)<=106.40:
        to_remove.append(t)
    # old east-to-113.5 at y=106 then down
    elif abs(sy-106.0)<0.05 and abs(ey-106.0)<0.05 and max(sx,ex)>=113.4 and min(sx,ex)>=111.7:
        # keep the C5→113.0 segment; only drop ones ending at 113.5
        if abs(max(sx,ex)-113.5)<0.05:
            to_remove.append(t)
    elif abs(sx-113.0)<0.05 and abs(ex-113.0)<0.05 and min(sy,ey)>=106.0 and max(sy,ey)<=106.40:
        to_remove.append(t)
for t in to_remove:
    board.Remove(t)

F = pcbnew.F_Cu
ni = board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer, x1, y1, x2, y2, w, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

pads = {}
for fp in board.GetFootprints():
    if fp.GetReference() in ("C_LDO", "U2"):
        for p in fp.Pads():
            pads[f"{fp.GetReference()}.{p.GetNumber()}"] = (tomm(p.GetPosition().x), tomm(p.GetPosition().y))
c5 = pads["U2.C5"]
cldo2 = pads["C_LDO.2"]  # 3V3_DISP
# Keep existing C5→113.0@y=106 rail if present; add north jog to new pad
# Use thin 0.25 to avoid mash with R_ILIM @y=106.15
add(F, c5[0], c5[1], 113.00, 106.00, 0.25, "3V3_DISP")
add(F, 113.00, 106.00, 113.00, cldo2[1], 0.25, "3V3_DISP")
add(F, 113.00, cldo2[1], cldo2[0], cldo2[1], 0.25, "3V3_DISP")

dist = ((cldo2[0]-c5[0])**2+(cldo2[1]-c5[1])**2)**0.5
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"C_LDO->{NEW} rem={len(to_remove)} pad2={cldo2} distC5={dist:.3f}")
