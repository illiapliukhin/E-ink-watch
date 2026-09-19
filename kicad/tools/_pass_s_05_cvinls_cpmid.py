#!/usr/bin/env python3
"""Pass-S5a: only trim 3V3_DISP stub @(113.0,106.0-106.32) off C_VINLS PMID pad.
C_PMID↔U2 B.Cu stitch DEFERRED (raises PMID↔SW/GND).
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(u): return u/1e6
def near(a,b,eps=0.06): return abs(a-b)<eps
to_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="3V3_DISP" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,113.000) and near(ex,113.000) and min(sy,ey)>=106.0 and max(sy,ey)<=106.4:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"S5a rem={len(to_rm)}")
