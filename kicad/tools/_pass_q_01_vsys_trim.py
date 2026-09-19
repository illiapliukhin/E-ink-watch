#!/usr/bin/env python3
"""Pass-Q1 KEPT: VSYS — remove F segments south of L_SYS that short J_STRAP_R pad10
and 3V3_DISP/IPRETERM vias; reconnect L_SYS.2 north of MP at y=106.10 to U2.B5.

Do NOT raise to y=106.55 (hits 3V3_DISP/CD). Do NOT B.Cu hop at 102–105 (congested).
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
    if abs(x1-x2)<1e-9 and abs(y1-y2)<1e-9: return
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

to_rm=[]
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="VSYS" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,117.412) and near(ex,117.412) and min(sy,ey)<=103.0 and max(sy,ey)>=104.4:
        to_rm.append(t)
    elif near(sy,102.950) and near(ey,102.950) and max(sx,ex)>=111.3:
        to_rm.append(t)
for t in to_rm: board.Remove(t)

NY,W=106.10,0.30
add(F,117.412,104.500,117.412,NY,W,"VSYS")
add(F,117.412,NY,111.800,NY,W,"VSYS")
add(F,111.800,NY,111.800,105.600,0.40,"VSYS")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"VSYS Q1 KEPT rem={len(to_rm)} NY={NY}")
