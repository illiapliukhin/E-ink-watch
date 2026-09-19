#!/usr/bin/env python3
"""Pass-S2 KEPT state helper — IPRETERM B @x=110.05 (clears GND via@109.55).
Also trim PMIC_INT F west stub that skims IPRETERM via@(110.05,106.40).
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.06): return abs(a-b)<eps
F=pcbnew.F_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

# Trim PMIC_INT (110.6,106.7)-(109.1,106.7) — stop east of IPRETERM via
to_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="PMIC_INT" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,106.700) and near(ey,106.700) and min(sx,ex)<=109.2 and max(sx,ex)>=110.5:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
# rebuild shorter: from D2 column to x=110.40 only (east of via@110.05)
add(F,110.600,106.700,110.400,106.700,0.15,"PMIC_INT")
# keep via at 109.1 if exists — reconnect via B or leave; check
# Relink to existing via@(109.1,106.7) on B.Cu
B=pcbnew.B_Cu
add(B,110.400,106.700,109.100,106.700,0.15,"PMIC_INT")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"S2+ PMIC_INT trim rem={len(to_rm)}")
