#!/usr/bin/env python3
"""Safe pass A: delete mash only (no B.Cu rebuild, no FP nudge)."""
import shutil
from datetime import datetime
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
BACKUP = Path("/workspace/e-ink-watch-kicad/backups") / f"e-ink-watch.kicad_pcb.pre-sclsda-safe-{datetime.now():%H%M%S}"
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu

def tomm(v): return float(v)/1e6
def near(a,b,eps=0.08): return abs(a-b)<eps
def is_zero(t,eps=1e-4):
    return abs(tomm(t.GetStart().x)-tomm(t.GetEnd().x))<eps and abs(tomm(t.GetStart().y)-tomm(t.GetEnd().y))<eps

def should_delete(t):
    net=t.GetNetname(); layer=t.GetLayer()
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    zero=is_zero(t)
    if net=="SDA":
        if layer==F_CU and not zero and near(sy,87.25) and near(ey,87.25):
            if near(min(sx,ex),98.8,0.1) and near(max(sx,ex),99.4,0.1): return True
        if layer==F_CU and not zero and near(sx,99.4,0.1) and near(ex,99.4,0.1):
            if min(sy,ey)>=87.2 and max(sy,ey)<=88.1: return True
        if zero and near(sx,99.4,0.1) and near(sy,88.05,0.1): return True
        if zero and near(sx,111.25,0.12) and near(sy,107.45,0.12): return True
        if layer==F_CU and not zero:
            if ((near(sx,111.4,0.15) and near(ex,111.25,0.15)) or (near(ex,111.4,0.15) and near(sx,111.25,0.15))):
                if max(sy,ey)<=107.55 and min(sy,ey)>=106.7: return True
        if layer==B_CU and max(sy,ey)<=107.6 and min(sy,ey)>=106.9 and min(sx,ex)>=109.0: return True
    if net=="SCL":
        if layer==F_CU and not zero and near(sy,87.25) and near(ey,87.25):
            if near(min(sx,ex),98.0,0.1) and near(max(sx,ex),98.6,0.1): return True
        if layer==F_CU and not zero and near(sx,98.6,0.1) and near(ex,98.6,0.1):
            if min(sy,ey)>=87.2 and max(sy,ey)<=88.1: return True
        if zero and near(sx,98.6,0.1) and near(sy,88.05,0.1): return True
        if zero and near(sx,112.55,0.12) and near(sy,107.85,0.12): return True
        if layer==F_CU and not zero:
            if (near(sx,111.8,0.15) or near(ex,111.8,0.15)) and (near(sx,112.55,0.15) or near(ex,112.55,0.15)):
                return True
        if layer==B_CU and near(sx,112.55,0.15) and near(ex,112.55,0.15): return True
    if net=="3V3" and layer==F_CU and not zero:
        if near(sy,107.6,0.08) and near(ey,107.6,0.08):
            if near(min(sx,ex),110.01,0.12) and near(max(sx,ex),112.01,0.12): return True
    if net=="GND" and zero and near(sx,98.25,0.12) and near(sy,84.25,0.12): return True
    # GND stub between NTC and R_SDA that reports as short
    if net=="GND" and layer==F_CU and not zero:
        if near(sx,108.71,0.1) and near(ex,108.71,0.1):
            if near(min(sy,ey),107.8,0.1) and near(max(sy,ey),108.6,0.1):
                return True  # will re-add further north if needed
    if net=="EPD_SCK" and layer==F_CU:
        if near(sy,84.4,0.08) and near(ey,84.4,0.08) and abs(sx-ex)>2.0: return True
        if zero and near(sx,97.0,0.1) and near(sy,84.4,0.1): return True
        if not zero and near(min(sx,ex),97.0,0.1) and near(max(sx,ex),99.25,0.1) and near(sy,84.4,0.1) and near(ey,84.4,0.1):
            return True
    if net=="EPD_RST" and layer==F_CU:
        if near(sx,104.0,0.12) and near(ex,104.0,0.12) and min(sy,ey)<=86.4 and max(sy,ey)>=85.0: return True
        if near(sy,85.9,0.1) and near(ey,85.9,0.1) and max(sx,ex)>=103.5: return True
        if zero and near(sx,104.0,0.15) and near(sy,87.5,0.15): return True
        if zero and near(sx,100.0,0.1) and near(sy,85.9,0.1): return True
    if net=="EPD_BUSY_MAIN" and layer==F_CU:
        if near(sx,105.8,0.12) and near(ex,105.8,0.12): return True
        if near(sy,86.9,0.1) and near(ey,86.9,0.1) and max(sx,ex)>=101.5: return True
        if zero and near(sx,102.0,0.1) and near(sy,86.9,0.1): return True
        if near(min(sx,ex),101.25,0.15) and near(max(sx,ex),102.0,0.15) and near(sy,86.9,0.15) and near(ey,86.9,0.15):
            return True
    return False

shutil.copy2(PCB, BACKUP)
print("backup", BACKUP.name)
board=pcbnew.LoadBoard(str(PCB))
assert board.GetCopperLayerCount()==4
doomed=[t for t in list(board.GetTracks()) if should_delete(t)]
for t in list(board.GetTracks()):
    if t in doomed: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)>1e-4 or abs(sy-ey)>1e-4: continue
    net=t.GetNetname()
    if net=="SDA" and near(sx,99.4,0.1) and near(sy,88.05,0.1): doomed.append(t)
    if net=="SCL" and near(sx,98.6,0.1) and near(sy,88.05,0.1): doomed.append(t)
for t in doomed: board.Remove(t)
print("deleted", len(doomed))
pcbnew.SaveBoard(str(PCB), board)
print("safe A saved")
