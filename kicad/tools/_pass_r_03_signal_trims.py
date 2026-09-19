#!/usr/bin/env python3
"""Pass-R3: (a) delete ILIM F stub east into J_STRAP_R MP; (b) jog TS west of C_BAT/PMIC_INT."""
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

# (a) ILIM stub into MP
ilim_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="ILIM" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,105.700) and near(ey,105.700) and max(sx,ex)>=113.65 and min(sx,ex)<=113.50:
        ilim_rm.append(t)
for t in ilim_rm: board.Remove(t)

# (b) TS: remove segments around 108.71 that skim C_BAT/PMIC_INT; rebuild west corridor
ts_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="TS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # vertical @108.71
    if near(sx,108.710) and near(ex,108.710):
        ts_rm.append(t)
    # diagonal 108.71,107 → 111,106
    elif near(sx,108.710) or near(ex,108.710):
        if max(sx,ex)>=110.9 and min(sy,ey)<=107.05:
            ts_rm.append(t)
for t in ts_rm: board.Remove(t)

# U2.C3 TS @(111.0,106.0) — escape north then west at y=107.40 (above PMIC_INT via y=106.7)
# Keep existing (111.0,107.3)-(111.0,106.0) if still there
has=False
for t in board.GetTracks():
    if t.GetNetname()!="TS" or t.Type()==pcbnew.PCB_VIA_T: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,111.000) and near(ex,111.000) and min(sy,ey)<=106.05 and max(sy,ey)>=107.2:
        has=True
if not has:
    add(F,111.000,106.000,111.000,107.400,0.18,"TS")
add(F,111.000,107.400,108.200,107.400,0.18,"TS")  # west, north of PMIC_INT
# if old TS continued somewhere west — leave dangling OK for now

pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"R3 ilim_rm={len(ilim_rm)} ts_rm={len(ts_rm)}")
