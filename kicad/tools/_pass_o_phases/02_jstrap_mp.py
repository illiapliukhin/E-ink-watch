#!/usr/bin/env python3
"""Ease J_STRAP_R inner MP GND: shrink to match J_STRAP_L + nudge east toward connector."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6

# Mechanical: J_STRAP_L inner MP is 1.0×1.4; R was oversized 1.2×2.0 at (114.0,104.65).
# Nudge east toward connector body (fp x=115) to free C_PMID corridor; keep y=104.65.
TARGET = (114.70, 104.650)
SIZE = (1.000, 1.400)
moved = False
for fp in board.GetFootprints():
    if fp.GetReference() != "J_STRAP_R":
        continue
    for pad in fp.Pads():
        if pad.GetNumber() != "MP":
            continue
        p = pad.GetPosition()
        if abs(tomm(p.y)-104.65)<0.05 and abs(tomm(p.x)-114.0)<0.2:
            pad.SetPosition(pcbnew.VECTOR2I(mm(TARGET[0]), mm(TARGET[1])))
            pad.SetSize(pcbnew.VECTOR2I(mm(SIZE[0]), mm(SIZE[1])))
            moved = True
            print(f"MP eased (114.0,104.65)1.2x2.0 -> {TARGET}{SIZE}")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
if not moved:
    print("MP not found / already eased")
    raise SystemExit(1)
