#!/usr/bin/env python3
"""Pass-R4: raise VSYS north spine y=106.10→106.28 to clear ILIM via@(113.44,105.70)."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.06): return abs(a-b)<eps
F=pcbnew.F_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

to_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="VSYS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,106.100) and near(ey,106.100) and max(sx,ex)>=117.0:
        to_rm.append(t)
    elif near(sx,117.412) and near(ex,117.412) and min(sy,ey)>=104.4 and max(sy,ey)<=106.15:
        to_rm.append(t)
    elif near(sx,111.800) and near(ex,111.800) and min(sy,ey)>=105.55 and max(sy,ey)<=106.15:
        to_rm.append(t)
for t in to_rm: board.Remove(t)

NY=106.28
add(F,117.412,104.500,117.412,NY,0.30,"VSYS")
add(F,117.412,NY,111.800,NY,0.30,"VSYS")
add(F,111.800,NY,111.800,105.600,0.40,"VSYS")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"R4 VSYS NY={NY} rem={len(to_rm)}")
