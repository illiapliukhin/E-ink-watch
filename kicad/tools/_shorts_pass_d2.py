#!/usr/bin/env python3
"""Pass D2: FH12 stubs via B.Cu escapes + MAIN BUSY/CS/RST + crossings.
NEVER delete GND. No MAIN SCK F y-channel near GND via (B.Cu already done).
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
        print(f"  SKIP power via ({x:.3f},{y:.3f})")
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
        return False
    layer = t.GetLayer()
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    zero = is_zero(t)
    xmin, xmax = min(sx, ex), max(sx, ex)
    ymin, ymax = min(sy, ey), max(sy, ey)

    # L SCK F vertical through 3V3_DISP
    if net == "EPD_SCK" and layer == F_CU and not zero:
        if near(sx, 84.35, 0.1) and near(ex, 84.35, 0.1) and ymin <= 97.0 and ymax >= 100.0:
            return True
        if near(sy, 101.25, 0.1) and near(ey, 101.25, 0.1) and near(xmin, 83.15, 0.1) and xmax <= 84.5:
            return True

    # L DC F near GND@86,100
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 86.35, 0.1) and near(ex, 86.35, 0.1) and ymin <= 99.0 and ymax >= 100.0:
            return True
        if near(sy, 100.25, 0.1) and near(ey, 100.25, 0.1) and near(xmin, 83.15, 0.1) and xmax <= 86.5:
            return True

    # L RST F long into GND / BUSY
    if net == "EPD_RST" and layer == F_CU and not zero:
        if xmin <= 83.2 and xmax >= 87.0 and (
            (near(sy, 99.80, 0.15) and near(ey, 99.75, 0.15))
            or (near(sy, 99.75, 0.1) and near(ey, 99.75, 0.1))
            or (near(sy, 99.80, 0.1) and near(ey, 99.80, 0.1))
        ):
            return True

    # orphan RST via@87.5,99.5
    if net == "EPD_RST" and zero and near(sx, 87.50, 0.12) and near(sy, 99.50, 0.12):
        return True

    # L BUSY vertical + old pad horiz
    if net == "EPD_BUSY_L" and layer == F_CU and not zero:
        if near(sx, 90.20, 0.1) and near(ex, 90.20, 0.1) and ymin <= 97.5 and ymax >= 99.0:
            return True
        if near(sy, 99.25, 0.08) and near(ey, 99.25, 0.08) and near(xmin, 83.15, 0.1) and near(xmax, 90.20, 0.1):
            return True

    # R MOSI on GND via
    if net == "EPD_MOSI" and layer == F_CU and not zero:
        if near(sx, 114.65, 0.1) and near(ex, 114.65, 0.1) and ymin <= 98.0 and ymax >= 99.0:
            return True
        if near(sy, 99.25, 0.1) and near(ey, 99.25, 0.1) and near(xmax, 116.85, 0.1) and xmin >= 114.5:
            return True

    # R DC near CS_R via
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 113.65, 0.1) and near(ex, 113.65, 0.1) and ymin <= 99.0 and ymax >= 100.5:
            return True
        if near(sy, 100.75, 0.1) and near(ey, 100.75, 0.1) and near(xmax, 116.85, 0.1) and xmin >= 113.5:
            return True

    if net == "EPD_CS_R" and zero and near(sx, 114.0, 0.15) and near(sy, 100.0, 0.15):
        return True

    # MAIN BUSY
    if net == "EPD_BUSY_MAIN" and layer == F_CU and not zero:
        if near(sx, 105.40, 0.1) and near(ex, 105.40, 0.1):
            return True
        if near(sy, 87.05, 0.08) and near(ey, 87.05, 0.08):
            return True
        if near(sy, 90.15, 0.08) and near(ey, 90.15, 0.08) and xmin <= 104.0 and xmax >= 105.0:
            return True
        if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1) and (ymax >= 86.5 or near(ymin, 83.15, 0.15) or near(ymin, 85.20, 0.15)):
            return True

    # MAIN CS
    if net == "EPD_CS_MAIN" and layer == F_CU:
        if not zero:
            if near(sx, 100.80, 0.15) and near(ex, 101.00, 0.15) and near(sy, 86.35, 0.15) and near(ey, 86.40, 0.15):
                return True
            if near(sx, 100.80, 0.15) and near(ex, 101.00, 0.15) and near(sy, 86.40, 0.1) and near(ey, 86.40, 0.1):
                return True
            if near(sy, 86.40, 0.08) and near(ey, 86.40, 0.08) and xmin <= 99.8 and xmax >= 100.9:
                return True
            if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and ymax >= 86.3 and ymin <= 83.2:
                return True
            if near(sy, 85.20, 0.08) and near(ey, 85.20, 0.08) and 100.5 <= xmin and xmax <= 101.2:
                return True
        if zero and near(sx, 101.00, 0.12) and near(sy, 86.40, 0.12):
            return True

    # MAIN RST
    if net == "EPD_RST" and layer == F_CU and not zero:
        if near(sy, 86.35, 0.08) and near(ey, 86.35, 0.08) and xmin <= 102.7 and xmax >= 103.9:
            return True
        if near(sx, 102.60, 0.1) and near(ex, 102.60, 0.1) and ymin <= 85.6 and ymax >= 86.3:
            return True
        if near(sy, 85.55, 0.08) and near(ey, 85.55, 0.08) and xmin <= 100.8 and xmax >= 102.5:
            return True
        if near(sx, 100.75, 0.1) and near(ex, 100.75, 0.1) and ymin <= 83.2 and ymax >= 85.5:
            return True

    # MAIN DC channel y=85.40 — nudge later by delete+rebuild if RST conflict; delete horiz mash zone
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sy, 85.40, 0.08) and near(ey, 85.40, 0.08) and xmin <= 102.1 and xmax >= 99.0:
            return True
        if near(sx, 100.25, 0.1) and near(ex, 100.25, 0.1) and near(ymin, 83.15, 0.1) and ymax <= 85.5:
            return True

    # SWDCLK share CS_L Y
    if net == "SWDCLK" and layer == F_CU and not zero:
        if near(sy, 100.75, 0.08) and near(ey, 100.75, 0.08) and xmin <= 91.3 and xmax >= 89.0:
            return True

    # BTN2 through SWDIO
    if net == "BTN2" and layer == F_CU:
        if not zero:
            if near(sx, 95.45, 0.12) and near(ex, 95.45, 0.12) and ymin <= 95.0 and ymax >= 95.7:
                return True
            if near(sy, 94.95, 0.08) and near(ey, 94.95, 0.08) and xmin <= 95.5 and xmax >= 96.2:
                return True
        if zero and near(sx, 95.45, 0.12) and (near(sy, 95.75, 0.12) or near(sy, 95.95, 0.12)):
            return True
    if net == "BTN2" and layer == B_CU and not zero:
        if near(sx, 95.45, 0.12) and near(ex, 95.45, 0.12) and ymin <= 96.0 and ymax >= 110.0:
            return True
        if near(sy, 111.50, 0.08) and near(ey, 111.50, 0.08) and xmin <= 96.0 and xmax >= 112.0:
            return True  # rebuild clear of TP5

    return False


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    for t in doomed:
        board.Remove(t)
    pcbnew.SaveBoard(str(PCB), board)
    print(f"D2 deleted {len(doomed)}")

    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4

    # --- L SCK: B.Cu under 3V3_DISP ---
    add_track(board, 84.350, 96.800, 84.350, 101.250, B_CU, "EPD_SCK")
    add_track(board, 84.350, 101.250, 83.700, 101.250, B_CU, "EPD_SCK")
    if add_via(board, 83.700, 101.250, 0.45, "EPD_SCK"):
        add_track(board, 83.700, 101.250, 83.150, 101.250, F_CU, "EPD_SCK")

    # --- L DC: B.Cu around GND@86,100 ---
    add_track(board, 86.350, 98.800, 88.500, 98.800, B_CU, "EPD_DC")
    add_track(board, 88.500, 98.800, 88.500, 100.250, B_CU, "EPD_DC")
    add_track(board, 88.500, 100.250, 83.700, 100.250, B_CU, "EPD_DC")
    if add_via(board, 83.700, 100.250, 0.45, "EPD_DC"):
        add_track(board, 83.700, 100.250, 83.150, 100.250, F_CU, "EPD_DC")

    # --- L RST: F south then west (clear GND@86,100 and BUSY@99.25) ---
    add_track(board, 87.350, 99.800, 87.350, 98.400, F_CU, "EPD_RST")
    add_track(board, 87.350, 98.400, 83.500, 98.400, F_CU, "EPD_RST")
    add_track(board, 83.500, 98.400, 83.500, 99.750, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.750, 83.150, 99.750, F_CU, "EPD_RST")

    # --- L BUSY: north then west of GND@90.5,98.5 ---
    add_track(board, 90.200, 97.250, 90.200, 96.600, F_CU, "EPD_BUSY_L")
    add_track(board, 90.200, 96.600, 89.000, 96.600, F_CU, "EPD_BUSY_L")
    add_track(board, 89.000, 96.600, 89.000, 99.250, F_CU, "EPD_BUSY_L")
    add_track(board, 89.000, 99.250, 83.150, 99.250, F_CU, "EPD_BUSY_L")

    # --- R MOSI clear of GND vias ---
    if add_via(board, 115.400, 98.400, 0.45, "EPD_MOSI"):
        add_track(board, 115.400, 98.400, 115.400, 99.250, F_CU, "EPD_MOSI")
        add_track(board, 115.400, 99.250, 116.850, 99.250, F_CU, "EPD_MOSI")

    # --- R DC further west ---
    add_track(board, 113.650, 98.800, 113.650, 99.100, F_CU, "EPD_DC")
    add_track(board, 113.650, 99.100, 112.900, 99.100, F_CU, "EPD_DC")
    add_track(board, 112.900, 99.100, 112.900, 100.750, F_CU, "EPD_DC")
    add_track(board, 112.900, 100.750, 116.850, 100.750, F_CU, "EPD_DC")

    # --- MAIN BUSY west corridor ---
    add_track(board, 103.750, 90.150, 103.750, 87.600, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 103.750, 87.600, 101.550, 87.600, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 87.600, 101.550, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 84.000, 101.250, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.250, 84.000, 101.250, 83.150, F_CU, "EPD_BUSY_MAIN")

    # --- MAIN CS ---
    add_track(board, 100.800, 86.350, 100.800, 85.000, F_CU, "EPD_CS_MAIN")
    add_track(board, 100.800, 85.000, 99.750, 85.000, F_CU, "EPD_CS_MAIN")
    add_track(board, 99.750, 85.000, 99.750, 83.150, F_CU, "EPD_CS_MAIN")

    # --- MAIN RST at y=85.90 ---
    add_track(board, 104.000, 86.350, 104.000, 85.900, F_CU, "EPD_RST")
    add_track(board, 104.000, 85.900, 100.750, 85.900, F_CU, "EPD_RST")
    add_track(board, 100.750, 85.900, 100.750, 83.150, F_CU, "EPD_RST")

    # --- MAIN DC at y=85.40 restored stubs (channel was deleted) ---
    add_track(board, 102.000, 85.400, 100.250, 85.400, F_CU, "EPD_DC")
    add_track(board, 100.250, 85.400, 100.250, 83.150, F_CU, "EPD_DC")
    # keep link from via@99,85.4 if present
    add_track(board, 99.000, 85.400, 100.250, 85.400, F_CU, "EPD_DC")

    # --- SWDCLK south of CS_L pad Y ---
    add_track(board, 91.200, 100.400, 89.080, 100.400, F_CU, "SWDCLK")
    add_track(board, 89.080, 100.400, 89.080, 100.750, F_CU, "SWDCLK")

    # --- BTN2 south of pad, clear SWDIO; B clear of TP5@96,111 ---
    add_track(board, 96.250, 94.950, 96.250, 96.200, F_CU, "BTN2")
    if add_via(board, 96.250, 96.200, 0.45, "BTN2"):
        add_track(board, 96.250, 96.200, 96.250, 112.200, B_CU, "BTN2")
        add_track(board, 96.250, 112.200, 112.800, 112.200, B_CU, "BTN2")
        add_track(board, 112.800, 112.200, 112.800, 111.500, B_CU, "BTN2")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"D2 rebuild ok 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
