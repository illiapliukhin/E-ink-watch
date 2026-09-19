#!/usr/bin/env python3
"""Pass-S1g: delete ONLY VBAT tracks shorting into D1 IPRETERM. B1–B2 stitch only.
West VBAT reconnect deferred (F/B corridors congested).
"""
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
    if t.GetNetname()!="VBAT" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,110.200) and near(ex,110.200) and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        to_rm.append(t)
    elif near(sy,106.400) and near(ey,106.400) and max(sx,ex)>=110.15 and min(sx,ex)<=106.3:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
has=False
for t in board.GetTracks():
    if t.GetNetname()!="VBAT" or t.Type()==pcbnew.PCB_VIA_T: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,105.600) and near(ey,105.600) and min(sx,ex)<=110.25 and max(sx,ex)>=110.55:
        has=True
if not has:
    add(F,110.200,105.600,110.600,105.600,0.28,"VBAT")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"S1g rem={len(to_rm)} (no west reconnect)")
