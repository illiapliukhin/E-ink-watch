#!/usr/bin/env python3
"""Pass-S4: (a) jog VSYS B5 stub east of PMID B3-B4; (b) move PMIC_INT via east off R_TS."""
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

# (a) replace VSYS (111.8,106.1)-(111.8,105.6)
to_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="VSYS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,111.800) and near(ex,111.800) and min(sy,ey)>=105.55 and max(sy,ey)<=106.15:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
add(F,111.800,106.100,112.050,106.100,0.28,"VSYS")
add(F,112.050,106.100,112.050,105.600,0.25,"VSYS")
add(F,112.050,105.600,111.800,105.600,0.25,"VSYS")

# (b) PMIC_INT via 109.1,106.7 → 109.45,106.70
via=None
for t in board.GetTracks():
    if t.Type()!=pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if near(x,109.100) and near(y,106.700):
        via=t
        break
if via is not None:
    via.SetPosition(pcbnew.VECTOR2I(mm(109.450), mm(106.700)))
    try: via.SetFrontWidth(mm(0.45)); via.SetBackWidth(mm(0.45))
    except Exception: pass
# retarget B PMIC_INT if ends at old via
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="B.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # (110.4,106.7)-(109.1,106.7) from S2c
    if near(sy,106.700) and near(ey,106.700) and min(sx,ex)<=109.2:
        board.Remove(t)
        add(pcbnew.B_Cu,110.400,106.700,109.450,106.700,0.15,"PMIC_INT")
        break

pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"S4 VSYS jog rem={len(to_rm)} PMIC_via={'moved' if via else 'MISSING'}")
