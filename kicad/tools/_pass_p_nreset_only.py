#!/usr/bin/env python3
"""Pass-P nRESET-only: route north around SWDCLK spine @x=89.08."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.05): return abs(a-b)<eps
F=pcbnew.F_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
to_rm=[]
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="nRESET" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,107.20) and near(ey,107.20) and min(sx,ex)<=88.5 and max(sx,ex)>=91.5:
        to_rm.append(t)
    elif near(sx,88.40) and near(ex,88.40) and min(sy,ey)>=106.45 and max(sy,ey)<=107.25:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
add(F,88.400,106.500,88.400,109.200,0.18,"nRESET")
add(F,88.400,109.200,91.620,109.200,0.18,"nRESET")
add(F,91.620,109.200,91.620,108.000,0.18,"nRESET")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"nRESET rem={len(to_rm)}")
