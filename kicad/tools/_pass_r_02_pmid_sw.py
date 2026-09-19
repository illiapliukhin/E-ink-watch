#!/usr/bin/env python3
"""Pass-R2b: PMID via (111.35,104.35)→(111.35,103.85); shrink annular 0.45."""
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

NY=103.85
via=None; to_rm=[]
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMID": continue
    if t.Type()==pcbnew.PCB_VIA_T:
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if near(x,111.350) and near(y,104.350):
            via=t
        continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,111.350) and near(ex,111.350) and min(sy,ey)<=104.4 and max(sy,ey)>=103.3:
        to_rm.append(t)
    elif near(sy,103.400) and near(ey,103.400) and min(sx,ex)<=111.40 and max(sx,ex)>=111.70:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
if via is None: raise SystemExit("no via")
via.SetPosition(pcbnew.VECTOR2I(mm(111.350), mm(NY)))
try: via.SetFrontWidth(mm(0.45)); via.SetBackWidth(mm(0.45))
except Exception: pass
add(F,111.350,NY,111.350,103.400,0.28,"PMID")
add(F,111.350,103.400,111.720,103.400,0.28,"PMID")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"R2b via→(111.35,{NY}) rem={len(to_rm)}")
