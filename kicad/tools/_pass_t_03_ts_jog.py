#!/usr/bin/env python3
"""Pass-T3 KEEP: TS west spine y=107.40→107.25 to clear 3V3 after SW via move (SaveBoard flake)."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.08): return abs(a-b)<eps
F=pcbnew.F_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
to_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="TS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,107.400) and near(ey,107.400):
        to_rm.append(t)
for t in to_rm: board.Remove(t)
add(F, 111.000, 107.300, 111.000, 107.250, 0.18, "TS")
add(F, 111.000, 107.250, 108.200, 107.250, 0.18, "TS")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"T3 TS y→107.25 rem={len(to_rm)}")
