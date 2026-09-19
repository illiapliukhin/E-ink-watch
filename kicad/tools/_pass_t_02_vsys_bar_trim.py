#!/usr/bin/env python3
"""Pass-T2a KEEP: delete dangling VSYS F bar (112.8,104.48)-(111.8,104.48).
Already unconnected to B5; frees SW SE landing for C_PMID corridor attempt."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(u): return u/1e6
def near(a,b,eps=0.08): return abs(a-b)<eps
to_rm=[]
for t in board.GetTracks():
    if t.GetNetname()!="VSYS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,104.480) and near(ey,104.480) and min(sx,ex)<=111.85 and max(sx,ex)>=112.7:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"T2a deleted VSYS bar rem={len(to_rm)}")
