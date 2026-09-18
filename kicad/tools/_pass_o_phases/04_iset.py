#!/usr/bin/env python3
"""ISET B.Cu west of x≈109.2 — escape U2.C1 then west spine."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
F, B = pcbnew.F_Cu, pcbnew.B_Cu
ni = board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer, x1, y1, x2, y2, w, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
def via(x, y, net, drill=0.25, width=0.50):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(drill))
    try: v.SetWidth(mm(width))
    except Exception: pass
    v.SetNetCode(nc(net)); board.Add(v)

# Clear any prior ISET copper
to_remove = [t for t in board.GetTracks() if t.GetNetname() == "ISET"]
for t in to_remove:
    board.Remove(t)

pads = {}
for fp in board.GetFootprints():
    if fp.GetReference() in ("R_ISET", "U2"):
        for p in fp.Pads():
            pads[f"{fp.GetReference()}.{p.GetNumber()}"] = (tomm(p.GetPosition().x), tomm(p.GetPosition().y))
c1 = pads["U2.C1"]       # ISET @(110.2,106.0)
riset = pads["R_ISET.2"] # ISET @(109.71,103.5)

# F micro-stub west of C1, via, B west of 109.2 then south to R_ISET
via(109.85, 106.00, "ISET", 0.25, 0.50)
add(F, c1[0], c1[1], 109.85, 106.00, 0.15, "ISET")
via(109.00, 103.50, "ISET", 0.25, 0.50)
add(B, 109.85, 106.00, 109.00, 106.00, 0.15, "ISET")
add(B, 109.00, 106.00, 109.00, 103.50, 0.15, "ISET")
add(B, 109.00, 103.50, riset[0], 103.50, 0.15, "ISET")
# F link via→pad if via not on pad
add(F, 109.00, 103.50, riset[0], riset[1], 0.15, "ISET")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"ISET B west x=109.00 C1={c1} pad={riset} rem={len(to_remove)}")
