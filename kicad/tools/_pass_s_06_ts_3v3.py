#!/usr/bin/env python3
"""Pass-S6c: TS B.Cu west hop — via north of C3, B at y=107.20, via west; avoid F 3V3/GND."""
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
def via(x,y,net,drill=0.25,width=0.45):
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetDrill(mm(drill))
    try: v.SetFrontWidth(mm(width)); v.SetBackWidth(mm(width))
    except Exception: pass
    v.SetNetCode(nc(net)); board.Add(v)

to_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="TS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,107.400) and near(ey,107.400):
        to_rm.append(t)
    elif near(sx,111.000) and near(ex,111.000) and max(sy,ey)>=107.2:
        to_rm.append(t)
for t in to_rm: board.Remove(t)

# Keep (111,107.3)-(111,106) if present; else add short to via
via(111.000, 107.200, "TS", 0.25, 0.45)
add(F,111.000,106.000,111.000,107.200,0.18,"TS")
via(108.200, 107.200, "TS", 0.25, 0.45)
add(B,111.000,107.200,108.200,107.200,0.18,"TS")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"S6c B-hop rem={len(to_rm)}")
