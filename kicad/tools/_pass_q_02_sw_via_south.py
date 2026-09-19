#!/usr/bin/env python3
"""Pass-Q2b: SW via to (112.20,103.70) SE of PMID cluster; F jog from A4 east then south."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.08): return abs(a-b)<eps
F,B=pcbnew.F_Cu,pcbnew.B_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    if abs(x1-x2)<1e-9 and abs(y1-y2)<1e-9: return
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

NX,NY=112.20,103.70
sw_via=None
to_rm=[]
for t in list(board.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T:
        if t.GetNetname()=="SW":
            x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
            if near(x,111.40) and near(y,104.90):
                sw_via=t
        continue
    if t.GetNetname()!="SW": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetLayerName()=="F.Cu":
        if near(sx,111.40) and near(ex,111.40) and min(sy,ey)>=104.45 and max(sy,ey)<=105.25:
            to_rm.append(t)
    if t.GetLayerName()=="B.Cu":
        if near(sy,104.90) and near(ey,104.90) and min(sx,ex)<=111.5 and max(sx,ex)>=114.9:
            to_rm.append(t)
        elif near(sx,115.00) and near(ex,115.00) and min(sy,ey)>=104.45 and max(sy,ey)<=104.95:
            to_rm.append(t)
for t in to_rm: board.Remove(t)
if sw_via is None: raise SystemExit("no via")
sw_via.SetPosition(pcbnew.VECTOR2I(mm(NX),mm(NY)))
# F: A4 (111.4,105.2) → (112.20,105.2) → via
add(F,111.400,105.200,NX,105.200,0.22,"SW")
add(F,NX,105.200,NX,NY,0.22,"SW")
add(B,NX,NY,115.000,NY,0.30,"SW")
add(B,115.000,NY,115.000,104.500,0.30,"SW")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"SW via → ({NX},{NY}) rem={len(to_rm)}")
