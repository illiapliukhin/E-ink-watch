#!/usr/bin/env python3
"""Pass-S3: move ILIM via (113.44,105.70)→(113.44,105.35); retarget B/F stubs.
Clears skim vs VSYS @y=106.10.
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.08): return abs(a-b)<eps
F,B=pcbnew.F_Cu,pcbnew.B_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

NY=105.35
via=None; to_rm=[]
for t in list(board.GetTracks()):
    if t.GetNetname()!="ILIM": continue
    if t.Type()==pcbnew.PCB_VIA_T:
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if near(x,113.440) and near(y,105.700):
            via=t
        continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetLayerName()=="B.Cu":
        if near(sy,105.700) and near(ey,105.700) and max(sx,ex)>=113.3:
            to_rm.append(t)
        elif near(sx,110.300) and near(ex,110.300) and min(sy,ey)<=105.75 and max(sy,ey)>=105.65:
            to_rm.append(t)
for t in to_rm: board.Remove(t)
if via is None: raise SystemExit("ILIM via missing")
via.SetPosition(pcbnew.VECTOR2I(mm(113.440), mm(NY)))
# B rebuild: from west jog to new via y
add(B,110.300,106.000,110.300,NY,0.15,"ILIM")
add(B,110.300,NY,113.440,NY,0.15,"ILIM")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"S3 ILIM via→(113.44,{NY}) rem={len(to_rm)}")
