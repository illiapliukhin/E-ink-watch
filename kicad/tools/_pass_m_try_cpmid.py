#!/usr/bin/env python3
"""Try one C_PMID placement; args: cx cy rot base_short"""
import pcbnew, sys, shutil, subprocess, re
from collections import Counter
from pathlib import Path

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
cx, cy, rot = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
base = int(sys.argv[4]) if len(sys.argv)>4 else 17

def mm_to(v): return int(round(float(v)*1e6))
def to_mm(u): return u/1e6

shutil.copy2(ROOT/"backups/_passm_p1b.kicad_pcb", PCB)
board = pcbnew.LoadBoard(str(PCB))
pads = None
for fp in board.GetFootprints():
    if fp.GetReference() == "C_PMID":
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(mm_to(cx), mm_to(cy)))
        pads = [(p.GetNumber(), p.GetNetname(), to_mm(p.GetPosition().x), to_mm(p.GetPosition().y)) for p in fp.Pads()]

to_del = []
for t in board.GetTracks():
    if t.GetNetname() != "PMID" or t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetLayerName() != "F.Cu":
        continue
    a, b = t.GetStart(), t.GetEnd()
    if any(abs(to_mm(y) - 103.85) < 0.08 for y in (a.y, b.y)):
        to_del.append(t)
for t in to_del:
    board.Remove(t)

pmid = board.GetNetsByName()["PMID"]
p1 = [p for p in pads if p[0] == "1"][0]
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm_to(111.00), mm_to(104.35)))
t.SetEnd(pcbnew.VECTOR2I(mm_to(p1[2]), mm_to(p1[3])))
t.SetWidth(mm_to(0.45)); t.SetLayer(pcbnew.F_Cu); t.SetNet(pmid); board.Add(t)
pcbnew.SaveBoard(str(PCB), board)
print("EDIT", cx, cy, rot, "pads", pads)
