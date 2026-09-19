#!/usr/bin/env python3
"""Pass-T1c KEEP: SW via (111.40,104.90)→(111.55,104.55); F down@111.40 then east; B jog to y=104.90.

Requires T2a (VSYS bar deleted) first. Opens F west PMID corridor vs VBUS@110.6
(hole_clearance 0.25). Gate: shorting=0 / power=0 / PMID↔VBUS=0.
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

NX,NY=111.550,104.550
sw_via=None
to_rm=[]
for t in list(board.GetTracks()):
    if t.GetNetname()!="SW": continue
    if t.Type()==pcbnew.PCB_VIA_T:
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if near(x,111.400) and near(y,104.900):
            sw_via=t
        continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    ly=t.GetLayerName()
    if ly=="F.Cu" and near(sx,111.400) and near(ex,111.400) and min(sy,ey)<=105.25 and max(sy,ey)>=104.4:
        to_rm.append(t)
    if ly=="B.Cu" and near(sy,104.900) and near(ey,104.900) and (near(sx,111.400) or near(ex,111.400)):
        to_rm.append(t)

if sw_via is None:
    raise SystemExit("SW via not found at (111.40,104.90) — already moved?")
for t in to_rm: board.Remove(t)
sw_via.SetPosition(pcbnew.VECTOR2I(mm(NX),mm(NY)))
add(F, 111.400, 105.200, 111.400, NY, 0.22, "SW")
add(F, 111.400, NY, NX, NY, 0.22, "SW")
add(B, NX, NY, NX, 104.900, 0.28, "SW")
add(B, NX, 104.900, 115.000, 104.900, 0.28, "SW")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"T1c SW via →({NX},{NY}) rem={len(to_rm)}")
