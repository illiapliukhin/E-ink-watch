#!/usr/bin/env python3
"""Pass-Q3c: EPD_BUSY_R — south then east at y=89.20 (below U1.12/vias), then north."""
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
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="EPD_BUSY_R" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if (near(sx,104.65) and near(sy,89.75) and near(ex,109.80,0.15) and near(ey,99.25,0.15)) or \
       (near(ex,104.65) and near(ey,89.75) and near(sx,109.80,0.15) and near(sy,99.25,0.15)):
        to_rm.append(t)
for t in to_rm: board.Remove(t)

# Stay east of EPD_BUSY_MAIN (≤103.75). South of pad (bottom~90.35).
add(F,104.650,89.750,104.650,89.200,0.18,"EPD_BUSY_R")
add(F,104.650,89.200,107.600,89.200,0.18,"EPD_BUSY_R")
add(F,107.600,89.200,107.600,92.500,0.18,"EPD_BUSY_R")
add(F,107.600,92.500,109.800,99.250,0.18,"EPD_BUSY_R")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"EPD_BUSY_R Q3c rem={len(to_rm)}")
