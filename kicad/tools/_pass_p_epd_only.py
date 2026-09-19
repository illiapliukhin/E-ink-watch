#!/usr/bin/env python3
"""Pass-P EPD-only: nudge EPD_BUSY_MAIN west of EPD_MOSI @x=101.60."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.05): return abs(a-b)<eps

F = pcbnew.F_Cu
ni = board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

NEW_X=100.90
to_rm=[]
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="EPD_BUSY_MAIN" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,101.55) and near(ex,101.55) and min(sy,ey)<=84.1 and max(sy,ey)>=87.9:
        to_rm.append(t)
    elif near(sy,88.10) and near(ey,88.10) and max(sx,ex)>=103.7 and min(sx,ex)<=101.6:
        to_rm.append(t)
    elif near(sy,84.00) and near(ey,84.00) and min(sx,ex)<=101.3 and max(sx,ex)>=101.5:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
add(F,103.750,88.100,NEW_X,88.100,0.18,"EPD_BUSY_MAIN")
add(F,NEW_X,88.100,NEW_X,84.000,0.18,"EPD_BUSY_MAIN")
add(F,NEW_X,84.000,101.250,84.000,0.18,"EPD_BUSY_MAIN")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"EPD-only rem={len(to_rm)} NEW_X={NEW_X}")
