#!/usr/bin/env python3
"""nRESET B.Cu hop under SWDCLK spine — avoid 1.7mm J_SWD pads on F."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.05): return abs(a-b)<eps
F,B=pcbnew.F_Cu,pcbnew.B_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
def via(x,y,net,drill=0.25,width=0.50):
    # refuse seal
    if 90.5<=x<=101.5 and 108.5<=y<=117.0:
        raise RuntimeError(f"seal via {x},{y}")
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(drill))
    try: v.SetWidth(mm(width))
    except Exception: pass
    try: v.SetFrontWidth(mm(width)); v.SetBackWidth(mm(width))
    except Exception: pass
    v.SetNetCode(nc(net)); board.Add(v)

# Remove F crossing at y=107.2 and stub 88.4 up to it
to_rm=[]
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!="nRESET" or t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,107.20) and near(ey,107.20) and min(sx,ex)<=88.5 and max(sx,ex)>=91.5:
        to_rm.append(t)
    elif near(sx,88.40) and near(ex,88.40) and min(sy,ey)>=106.45 and max(sy,ey)<=107.25:
        to_rm.append(t)
for t in to_rm: board.Remove(t)

# From existing (88.4,106.5) end of west stub: short F to via west of SWDCLK pad (pad left edge ~88.23)
# Via at (88.00, 106.50) — south of pads (pad bottom ~107.15), east of SWDIO (right ~87.39)
# Clearance to SWDIO pad right 87.39: 88.00-87.39=0.61; via r=0.25 → gap 0.36 > 0.15 OK
# Clearance to SWDCLK pad left 88.23: 88.23-88.00=0.23; via r=0.25 → OVERLAP! 
# Move via to (87.70, 106.50): to SWDIO right 87.39: 0.31-0.25=0.06 < 0.15 tight
# Via at (87.80, 106.30) smaller approach
# Use (87.55, 106.90): SW_DBG pad is at 87.55,106.5 — via slightly north of pad center but still south of J_SWD pads
VX1,VY1=87.55,106.90
VX2,VY2=91.62,106.90
via(VX1,VY1,"nRESET",0.25,0.50)
via(VX2,VY2,"nRESET",0.25,0.50)
add(F,87.55,106.50,VX1,VY1,0.18,"nRESET")
add(B,VX1,VY1,VX2,VY2,0.18,"nRESET")
# F from via2 up to pad / existing spine
add(F,VX2,VY2,91.62,108.00,0.18,"nRESET")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"nRESET B-hop rem={len(to_rm)} vias=({VX1},{VY1})-({VX2},{VY2})")
