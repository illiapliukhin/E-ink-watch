#!/usr/bin/env python3
"""Pass D: clear remaining FH12/CS/DC/RST stubs + signal crossings.
NEVER delete GND copper. Avoid power corridor. No MAIN SCK y near GND@98.25,84.25
without ≥0.54mm center clearance (use y=84.85).
"""
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)
POWER = dict(xmin=105.0, xmax=118.5, ymin=101.5, ymax=109.0)


def mm(v):
    return int(round(float(v) * 1e6))


def tomm(v):
    return float(v) / 1e6


def near(a, b, eps=0.08):
    return abs(a - b) < eps


def is_zero(t):
    return abs(tomm(t.GetStart().x) - tomm(t.GetEnd().x)) < 1e-4 and abs(
        tomm(t.GetStart().y) - tomm(t.GetEnd().y)
    ) < 1e-4


def netcode(board, name):
    return board.GetNetInfo().GetNetItem(name).GetNetCode()


def add_track(board, x1, y1, x2, y2, layer, net, w=W):
    if near(x1, x2, 1e-9) and near(y1, y2, 1e-9):
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w))
    t.SetLayer(layer)
    t.SetNetCode(netcode(board, net))
    board.Add(t)


def add_via(board, x, y, d, net):
    if POGO["xmin"] <= x <= POGO["xmax"] and POGO["ymin"] <= y <= POGO["ymax"]:
        print(f"  SKIP seal via ({x:.3f},{y:.3f})")
        return False
    if POWER["xmin"] <= x <= POWER["xmax"] and POWER["ymin"] <= y <= POWER["ymax"]:
        print(f"  SKIP power-corridor via ({x:.3f},{y:.3f})")
        return False
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetWidth(mm(d))
    t.SetLayer(F_CU)
    t.SetNetCode(netcode(board, net))
    board.Add(t)
    return True


def should_delete(t) -> bool:
    net = t.GetNetname()
    if net == "GND":
        return False  # HARD RULE
    layer = t.GetLayer()
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    zero = is_zero(t)
    xmin, xmax = min(sx, ex), max(sx, ex)
    ymin, ymax = min(sy, ey), max(sy, ey)

    # --- L strap: SCK vertical through 3V3_DISP ---
    if net == "EPD_SCK" and layer == F_CU and not zero:
        if near(sx, 84.35, 0.1) and near(ex, 84.35, 0.1) and ymin <= 97.0 and ymax >= 100.0:
            return True
        if near(sy, 101.25, 0.1) and near(ey, 101.25, 0.1) and near(xmin, 83.15, 0.1) and near(xmax, 84.35, 0.1):
            return True

    # --- L strap: DC near GND via@86,100 ---
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 86.35, 0.1) and near(ex, 86.35, 0.1) and ymin <= 99.0 and ymax >= 100.0:
            return True
        if near(sy, 100.25, 0.1) and near(ey, 100.25, 0.1) and near(xmin, 83.15, 0.1) and xmax <= 86.5:
            return True

    # --- L strap: RST through GND via / BUSY ---
    if net == "EPD_RST" and layer == F_CU and not zero:
        if near(sy, 99.80, 0.15) and near(ey, 99.75, 0.15) and xmin <= 83.2 and xmax >= 87.0:
            return True
        if near(sy, 99.75, 0.1) and near(ey, 99.75, 0.1) and xmin <= 83.2 and xmax >= 87.0:
            return True
        if near(sy, 99.80, 0.1) and near(ey, 99.80, 0.1) and xmin <= 83.2 and xmax >= 87.0:
            return True

    # --- L strap: BUSY_L vertical skim GND via@90.5,98.5 ---
    if net == "EPD_BUSY_L" and layer == F_CU and not zero:
        if near(sx, 90.20, 0.1) and near(ex, 90.20, 0.1) and ymin <= 97.5 and ymax >= 99.0:
            return True

    # --- R strap: MOSI on GND via@114.65,97.8 ---
    if net == "EPD_MOSI" and layer == F_CU and not zero:
        if near(sx, 114.65, 0.1) and near(ex, 114.65, 0.1) and ymin <= 98.0 and ymax >= 99.0:
            return True
        if near(sy, 99.25, 0.1) and near(ey, 99.25, 0.1) and near(xmax, 116.85, 0.1) and xmin >= 114.5:
            return True

    # --- R strap: DC skim CS_R via@114,100 ---
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 113.65, 0.1) and near(ex, 113.65, 0.1) and ymin <= 99.0 and ymax >= 100.5:
            return True
        if near(sy, 100.75, 0.1) and near(ey, 100.75, 0.1) and near(xmax, 116.85, 0.1) and xmin >= 113.5:
            return True

    # orphan CS_R via shorting DC
    if net == "EPD_CS_R" and zero and near(sx, 114.0, 0.15) and near(sy, 100.0, 0.15):
        return True

    # --- MAIN BUSY through MP / CS via ---
    if net == "EPD_BUSY_MAIN" and layer == F_CU and not zero:
        if near(sx, 105.40, 0.1) and near(ex, 105.40, 0.1):
            return True
        if near(sy, 87.05, 0.08) and near(ey, 87.05, 0.08):
            return True
        if near(sy, 90.15, 0.08) and near(ey, 90.15, 0.08) and xmin <= 104.0 and xmax >= 105.0:
            return True
        if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1) and ymax >= 86.5:
            return True
        if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1) and near(ymin, 83.15, 0.1):
            return True
        if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1) and near(ymin, 85.20, 0.1):
            return True

    # --- MAIN CS mash ---
    if net == "EPD_CS_MAIN" and layer == F_CU:
        if not zero:
            if near(sx, 100.80, 0.12) and near(sy, 86.35, 0.12) and near(ex, 101.00, 0.12) and near(ey, 86.40, 0.12):
                return True
            if near(sx, 100.80, 0.12) and near(sy, 86.40, 0.12) and near(ex, 101.00, 0.12) and near(ey, 86.40, 0.12):
                return True
            if near(sy, 86.40, 0.08) and near(ey, 86.40, 0.08) and xmin <= 99.8 and xmax >= 100.9:
                return True
            if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and ymax >= 86.3 and ymin <= 83.2:
                return True
            if near(sy, 85.20, 0.08) and near(ey, 85.20, 0.08) and xmin <= 100.9 and xmax >= 100.7:
                return True
        if zero and near(sx, 101.00, 0.12) and near(sy, 86.40, 0.12):
            return True

    # --- MAIN RST through U1 empty pads / DC / CS ---
    if net == "EPD_RST" and layer == F_CU and not zero:
        if near(sy, 86.35, 0.08) and near(ey, 86.35, 0.08) and xmin <= 102.7 and xmax >= 103.9:
            return True
        if near(sx, 102.60, 0.1) and near(ex, 102.60, 0.1) and ymin <= 85.6 and ymax >= 86.3:
            return True
        if near(sy, 85.55, 0.08) and near(ey, 85.55, 0.08) and xmin <= 100.8 and xmax >= 102.5:
            return True
        if near(sx, 100.75, 0.1) and near(ex, 100.75, 0.1) and ymin <= 83.2 and ymax >= 85.5:
            return True

    # --- MAIN SCK y=83.85 (between 3V3_DISP pad and GND via) → move to 84.85 ---
    if net == "EPD_SCK" and layer == F_CU:
        if not zero:
            if near(sy, 83.85, 0.08) and near(ey, 83.85, 0.08) and xmax - xmin > 1.0:
                return True
            if near(sx, 99.25, 0.1) and near(ex, 99.25, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 83.85, 0.15):
                return True
        if zero and near(sx, 97.00, 0.12) and near(sy, 83.85, 0.12):
            return True  # move via with channel (NOT GND)

    # --- SWDCLK shares CS_L pad-Y at 100.75 ---
    if net == "SWDCLK" and layer == F_CU and not zero:
        if near(sy, 100.75, 0.08) and near(ey, 100.75, 0.08) and xmin <= 91.3 and xmax >= 89.0:
            return True
        # vertical stub that met that Y from below — keep 89.08 vertical but reconnect
        # only delete the horiz conflict; vertical 89.08 stays

    # --- BTN2 through SWDIO pad ---
    if net == "BTN2" and layer == F_CU:
        if not zero:
            if near(sx, 95.45, 0.12) and near(ex, 95.45, 0.12) and ymin <= 95.0 and ymax >= 95.7:
                return True
            if near(sy, 94.95, 0.08) and near(ey, 94.95, 0.08) and xmin <= 95.5 and xmax >= 96.2:
                return True
        if zero and near(sx, 95.45, 0.12) and (near(sy, 95.75, 0.12) or near(sy, 95.95, 0.12)):
            return True
    if net == "BTN2" and layer == B_CU and not zero:
        # old B vertical from 95.45,95.75 — will rebuild from new via
        if near(sx, 95.45, 0.12) and near(ex, 95.45, 0.12) and ymin <= 96.0 and ymax >= 110.0:
            return True

    # leftover MAIN MOSI dup stub
    if net == "EPD_MOSI" and layer == F_CU and not zero:
        if near(sx, 98.75, 0.1) and near(ex, 98.75, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 85.20, 0.1):
            return True

    return False


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    for t in doomed:
        board.Remove(t)
    pcbnew.SaveBoard(str(PCB), board)
    print(f"pass D deleted {len(doomed)}")

    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4

    # EPD_SCK L: east of 3V3_DISP spine x≈84.45
    add_track(board, 84.350, 96.800, 85.700, 96.800, F_CU, "EPD_SCK")
    add_track(board, 85.700, 96.800, 85.700, 101.250, F_CU, "EPD_SCK")
    add_track(board, 85.700, 101.250, 83.150, 101.250, F_CU, "EPD_SCK")

    # EPD_DC L: east of GND via@86,100
    add_track(board, 86.350, 98.800, 87.150, 98.800, F_CU, "EPD_DC")
    add_track(board, 87.150, 98.800, 87.150, 100.250, F_CU, "EPD_DC")
    add_track(board, 87.150, 100.250, 83.150, 100.250, F_CU, "EPD_DC")

    # EPD_RST L: south of GND via / clear BUSY_L @99.25
    add_track(board, 87.350, 99.800, 87.350, 99.500, F_CU, "EPD_RST")
    add_track(board, 87.350, 99.500, 83.500, 99.500, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.500, 83.500, 99.750, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.750, 83.150, 99.750, F_CU, "EPD_RST")

    # EPD_BUSY_L: jog west of GND via@90.5,98.5
    add_track(board, 90.200, 97.250, 89.500, 97.250, F_CU, "EPD_BUSY_L")
    add_track(board, 89.500, 97.250, 89.500, 99.250, F_CU, "EPD_BUSY_L")
    add_track(board, 89.500, 99.250, 83.150, 99.250, F_CU, "EPD_BUSY_L")
    # remove old direct pad horiz if still present — handled if same as deleted vertical's partner
    # keep existing (90.2,99.25)-(83.15,99.25) if not deleted — may duplicate; OK for connectivity
    # Actually old horiz still there — new path also to pad. Old horiz from 90.2 is fine remnant.
    # Wait: old horiz (90.2,99.25)-(83.15,99.25) was NOT deleted. New path joins at 89.5,99.25.
    # Old vertical deleted. Good. But old horiz still from 90.2 — orphan stub from nowhere?
    # Connect: we have via@90.2,97.25 → west → down → pad. Old horiz from 90.2,99.25 still exists
    # as dangling stub — harmless unless shorts. Leave it or delete.
    # Better delete leftover (90.2,99.25)-(83.15,99.25) since rebuild covers pad link.
    # Done in second pass below after save? Do now by scanning:

    # EPD_MOSI R: clear of GND vias@114.65/114.5
    if add_via(board, 115.40, 98.40, 0.45, "EPD_MOSI"):
        add_track(board, 115.400, 98.400, 115.400, 99.250, F_CU, "EPD_MOSI")
        add_track(board, 115.400, 99.250, 116.850, 99.250, F_CU, "EPD_MOSI")

    # EPD_DC R: further west then to pad (clear of former CS via zone)
    add_track(board, 113.650, 98.800, 113.650, 99.100, F_CU, "EPD_DC")
    add_track(board, 113.650, 99.100, 112.900, 99.100, F_CU, "EPD_DC")
    add_track(board, 112.900, 99.100, 112.900, 100.750, F_CU, "EPD_DC")
    add_track(board, 112.900, 100.750, 116.850, 100.750, F_CU, "EPD_DC")

    # EPD_SCK MAIN channel y=84.85 (north of GND via@98.25,84.25 by 0.60 ≥ 0.54)
    add_track(board, 105.500, 84.850, 97.000, 84.850, F_CU, "EPD_SCK")
    add_track(board, 97.000, 84.850, 99.250, 84.850, F_CU, "EPD_SCK")
    add_track(board, 99.250, 84.850, 99.250, 83.150, F_CU, "EPD_SCK")
    add_via(board, 97.000, 84.850, 0.45, "EPD_SCK")

    # EPD_BUSY_MAIN: west corridor, clear MP@105.1,86.8 and CS
    add_track(board, 103.750, 90.150, 103.750, 87.600, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 103.750, 87.600, 101.550, 87.600, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 87.600, 101.550, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 84.000, 101.250, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.250, 84.000, 101.250, 83.150, F_CU, "EPD_BUSY_MAIN")

    # EPD_CS_MAIN clean (pad U1.22 @100.8,86.35 → south → pad)
    add_track(board, 100.800, 86.350, 100.800, 85.000, F_CU, "EPD_CS_MAIN")
    add_track(board, 100.800, 85.000, 99.750, 85.000, F_CU, "EPD_CS_MAIN")
    add_track(board, 99.750, 85.000, 99.750, 83.150, F_CU, "EPD_CS_MAIN")

    # EPD_RST MAIN: south then west at 85.90 (clear DC@85.40)
    add_track(board, 104.000, 86.350, 104.000, 85.900, F_CU, "EPD_RST")
    add_track(board, 104.000, 85.900, 100.750, 85.900, F_CU, "EPD_RST")
    add_track(board, 100.750, 85.900, 100.750, 83.150, F_CU, "EPD_RST")

    # SWDCLK: meet CS_L column at y=100.40 (south of CS pad Y 100.75)
    add_track(board, 91.200, 100.400, 89.080, 100.400, F_CU, "SWDCLK")
    add_track(board, 89.080, 100.400, 89.080, 100.750, F_CU, "SWDCLK")  # join existing vertical

    # BTN2: south from pad then via, clear of SWDIO@95.35,95.35
    add_track(board, 96.250, 94.950, 96.250, 96.200, F_CU, "BTN2")
    if add_via(board, 96.250, 96.200, 0.45, "BTN2"):
        add_track(board, 96.250, 96.200, 96.250, 111.500, B_CU, "BTN2")
        # join existing B horiz to switch if present at y=111.5
        add_track(board, 96.250, 111.500, 112.800, 111.500, B_CU, "BTN2")

    pcbnew.SaveBoard(str(PCB), board)

    # cleanup leftover BUSY_L old pad-horiz duplicate from 90.2 (optional)
    board = pcbnew.LoadBoard(str(PCB))
    extra = []
    for t in list(board.GetTracks()):
        if t.GetNetname() != "EPD_BUSY_L" or t.GetLayer() != F_CU or is_zero(t):
            continue
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        if near(sy, 99.25, 0.08) and near(ey, 99.25, 0.08):
            if near(min(sx, ex), 83.15, 0.1) and near(max(sx, ex), 90.20, 0.1):
                extra.append(t)  # replaced by 89.5→83.15 path
    for t in extra:
        board.Remove(t)
    if extra:
        pcbnew.SaveBoard(str(PCB), board)
        print(f"cleaned {len(extra)} leftover BUSY_L horiz")

    print(f"pass D rebuild ok; 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
