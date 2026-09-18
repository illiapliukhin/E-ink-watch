#!/usr/bin/env python3
"""C_VINLS→PMID stitch on B.Cu avoiding 3V3_DISP F rail @y=106."""
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
def via(x, y, net, drill=0.25, width=0.55):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(drill))
    try: v.SetWidth(mm(width))
    except Exception: pass
    v.SetNetCode(nc(net)); board.Add(v)

pads = {}
for fp in board.GetFootprints():
    if fp.GetReference() in ("C_VINLS", "C_PMID"):
        for p in fp.Pads():
            pads[f"{fp.GetReference()}.{p.GetNumber()}"] = (tomm(p.GetPosition().x), tomm(p.GetPosition().y))
cvin = pads["C_VINLS.1"]  # PMID @(112.8,106.28)
cpmid = pads["C_PMID.1"]  # PMID

# Via just south of C_VINLS pad (avoid 3V3_DISP at y=106 F), B east/south to C_PMID via corridor
# C_VINLS pad is at y=106.28 — drop via at pad then B south to y=105.5 then east to C_PMID
via(cvin[0], cvin[1], "PMID", 0.25, 0.55)  # on pad
# Find existing C_PMID via from dogbone phase @ (cpmid.x, 104.80)
add(B, cvin[0], cvin[1], cvin[0], 105.50, 0.40, "PMID")
add(B, cvin[0], 105.50, cpmid[0], 105.50, 0.40, "PMID")
add(B, cpmid[0], 105.50, cpmid[0], 104.80, 0.40, "PMID")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"C_VINLS stitch B cvin={cvin} cpmid={cpmid}")
