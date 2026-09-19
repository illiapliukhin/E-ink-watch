#!/usr/bin/env python3
"""Pass-Q4: SWDCLK_POGO vertical x=95.0 → 95.60 clear of J_SWD GND pad5 @(94.16,108) r≈0.85."""
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
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

to_rm=[]
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="SWDCLK_POGO" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,95.00) and near(ex,95.00) and min(sy,ey)<=105.6 and max(sy,ey)>=110.9:
        to_rm.append(t)
    elif near(sy,105.50) and near(ey,105.50) and min(sx,ex)<=93.5 and max(sx,ex)>=94.9:
        to_rm.append(t)
for t in to_rm: board.Remove(t)

NEWX=95.60
add(F,93.450,105.500,NEWX,105.500,0.18,"SWDCLK_POGO")
add(F,NEWX,105.500,NEWX,111.000,0.18,"SWDCLK_POGO")
add(F,NEWX,111.000,93.000,111.000,0.18,"SWDCLK_POGO")  # to TP4 corridor @93,111
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"SWDCLK_POGO → x={NEWX} rem={len(to_rm)}")
