#!/usr/bin/env python3
"""Pass-P: surgical signal shorts — EPD_BUSY/MOSI, nRESET/SWDCLK, PMID/SW via separation.
Does NOT move J_STRAP_R MP, C_LDO, or U2. Revert if power-priority shorts rise.
"""
import pcbnew
from pathlib import Path

PCB = Path("e-ink-watch.kicad_pcb")
board = pcbnew.LoadBoard(str(PCB))

def mm(v):
    return int(round(float(v) * 1e6))

def tomm(u):
    return u / 1e6

def near(a, b, eps=0.05):
    return abs(a - b) < eps

F = pcbnew.F_Cu
ni = board.GetNetInfo()

def nc(name):
    return ni.GetNetItem(name).GetNetCode()

def add(layer, x1, y1, x2, y2, w, net):
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w))
    t.SetLayer(layer)
    t.SetNetCode(nc(net))
    board.Add(t)

removed = []

# --- 1) EPD_BUSY_MAIN: move vertical corridor west of EPD_MOSI @x=101.60 ---
# Current: horiz @y=88.1 to x=101.55, vert 101.55 y=88.1→84, jog to 101.25
NEW_X = 100.90
to_rm = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetNetname() != "EPD_BUSY_MAIN" or t.GetLayerName() != "F.Cu":
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    # vertical at 101.55
    if near(sx, 101.55) and near(ex, 101.55) and min(sy, ey) <= 84.1 and max(sy, ey) >= 87.9:
        to_rm.append(t)
    # horiz 103.75→101.55 @ y=88.1
    elif near(sy, 88.10) and near(ey, 88.10) and max(sx, ex) >= 103.7 and min(sx, ex) <= 101.6:
        to_rm.append(t)
    # short jog 101.55→101.25 @ y=84
    elif near(sy, 84.00) and near(ey, 84.00) and min(sx, ex) <= 101.3 and max(sx, ex) >= 101.5:
        to_rm.append(t)
for t in to_rm:
    board.Remove(t)
    removed.append("EPD_BUSY")

# Rebuild: 103.75,88.1 → NEW_X,88.1 → NEW_X,84 → 101.25,84 (existing 101.25 down kept)
add(F, 103.750, 88.100, NEW_X, 88.100, 0.18, "EPD_BUSY_MAIN")
add(F, NEW_X, 88.100, NEW_X, 84.000, 0.18, "EPD_BUSY_MAIN")
add(F, NEW_X, 84.000, 101.250, 84.000, 0.18, "EPD_BUSY_MAIN")

# --- 2) nRESET: remove east-west that crosses SWDCLK spine @x=89.08; route north ---
to_rm2 = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetNetname() != "nRESET" or t.GetLayerName() != "F.Cu":
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    # (88.4,107.2)-(91.62,107.2) crosses SWDCLK
    if near(sy, 107.20) and near(ey, 107.20) and min(sx, ex) <= 88.5 and max(sx, ex) >= 91.5:
        to_rm2.append(t)
    # (88.4,106.5)-(88.4,107.2) stub into that horiz
    elif near(sx, 88.40) and near(ex, 88.40) and min(sy, ey) >= 106.45 and max(sy, ey) <= 107.25:
        to_rm2.append(t)
for t in to_rm2:
    board.Remove(t)
    removed.append("nRESET")

# From (88.4,106.5) existing west stub end: go north around pads then to 91.62 spine
# Existing (91.62,101.25)-(91.62,108) remains
add(F, 88.400, 106.500, 88.400, 109.200, 0.18, "nRESET")
add(F, 88.400, 109.200, 91.620, 109.200, 0.18, "nRESET")
add(F, 91.620, 109.200, 91.620, 108.000, 0.18, "nRESET")

# --- 3) PMID↔SW: move SW via east away from PMID vias @111.00/111.35,104.35 ---
# SW via was (111.40,104.90); move to (111.90,104.90) and retarget SW F stub from A4
sw_via = None
for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T:
        continue
    if t.GetNetname() != "SW":
        continue
    x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
    if near(x, 111.40, 0.08) and near(y, 104.90, 0.08):
        sw_via = t
        break

sw_trk_rm = []
if sw_via is not None:
    # Remove short F dogbones into old via near A4
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() != "SW" or t.GetLayerName() != "F.Cu":
            continue
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        # segments that touch old via location
        if (near(sx, 111.40, 0.08) and near(sy, 104.90, 0.08)) or (
            near(ex, 111.40, 0.08) and near(ey, 104.90, 0.08)
        ):
            sw_trk_rm.append(t)
        # tiny stub from A4 (111.4,105.2) down
        elif near(sx, 111.40) and near(ex, 111.40) and min(sy, ey) >= 104.85 and max(sy, ey) <= 105.25:
            sw_trk_rm.append(t)
    for t in sw_trk_rm:
        board.Remove(t)
        removed.append("SW_trk")
    # Move via
    sw_via.SetPosition(pcbnew.VECTOR2I(mm(111.90), mm(104.90)))
    removed.append("SW_via_move")
    # A4 @(111.4,105.2) → (111.90,105.2) → (111.90,104.90)
    add(F, 111.400, 105.200, 111.900, 105.200, 0.20, "SW")
    add(F, 111.900, 105.200, 111.900, 104.900, 0.20, "SW")

pcbnew.SaveBoard(str(PCB), board)
print(f"Pass-P applied rem_tags={removed} NEW_X={NEW_X} sw_via={'moved' if sw_via else 'NOT_FOUND'} sw_trk_rm={len(sw_trk_rm)}")
