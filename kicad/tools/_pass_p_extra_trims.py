#!/usr/bin/env python3
"""Trim SWDCLK_POGO off J_SWD GND pad; jog EPD_BUSY_R around U1.12 no-net pad."""
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
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

# --- SWDCLK_POGO: move vertical x=95.0 → 95.60 ---
to_rm=[]
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="SWDCLK_POGO" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # vertical at 95.0
    if near(sx,95.00) and near(ex,95.00) and min(sy,ey)<=105.6 and max(sy,ey)>=110.9:
        to_rm.append(t)
    # horiz 93.45→95.0 @ y=105.5
    elif near(sy,105.50) and near(ey,105.50) and min(sx,ex)<=93.5 and max(sx,ex)>=94.9:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
NEWX=95.60
add(F,93.450,105.500,NEWX,105.500,0.18,"SWDCLK_POGO")
add(F,NEWX,105.500,NEWX,111.000,0.18,"SWDCLK_POGO")
# reconnect to TP4 path at 93,111 if needed: existing (93,108)-(93,111); need NEWX,111 → 93,111 or via TP
# TP4 @93,111 SWDCLK_POGO — add horiz
add(F,NEWX,111.000,93.000,111.000,0.18,"SWDCLK_POGO")

# --- EPD_BUSY_R: jog around U1.12 @(104.65,90.55) ---
# Current diagonal/long track (104.65,89.75)-(109.8,99.25) hits pad
to_rm2=[]
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="EPD_BUSY_R" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,104.65) and near(sy,89.75) and near(ex,109.80,0.1) and near(ey,99.25,0.1):
        to_rm2.append(t)
    elif near(ex,104.65) and near(ey,89.75) and near(sx,109.80,0.1) and near(sy,99.25,0.1):
        to_rm2.append(t)
for t in to_rm2: board.Remove(t)
# Route west of pad then north-east: pad extends ~104.65±0.3 x, 90.55±0.2 y
# From (104.65,89.75) go west to 103.90, up past pad to 91.20, then toward (109.8,99.25)
add(F,104.650,89.750,103.900,89.750,0.18,"EPD_BUSY_R")
add(F,103.900,89.750,103.900,91.200,0.18,"EPD_BUSY_R")
add(F,103.900,91.200,109.800,99.250,0.18,"EPD_BUSY_R")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"extra rem_pogo={len(to_rm)} rem_busy={len(to_rm2)} NEWX={NEWX}")
