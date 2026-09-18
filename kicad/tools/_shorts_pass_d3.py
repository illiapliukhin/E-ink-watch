#!/usr/bin/env python3
"""Pass D3: polish D2 regressions. Never delete GND."""
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

    # L DC B path that still skims GND through-via@86,100
    if net == "EPD_DC" and layer == B_CU and not zero:
        if near(sy, 100.25, 0.1) and near(ey, 100.25, 0.1) and xmin <= 84.0 and xmax >= 88.0:
            return True
        if near(sx, 88.50, 0.1) and near(ex, 88.50, 0.1) and ymin <= 99.0 and ymax >= 100.0:
            return True
        if near(sy, 98.80, 0.1) and near(ey, 98.80, 0.1) and near(xmin, 86.35, 0.1) and near(xmax, 88.50, 0.1):
            return True
    if net == "EPD_DC" and layer == F_CU:
        if zero and near(sx, 83.70, 0.1) and near(sy, 100.25, 0.1):
            return True
        if not zero and near(sy, 100.25, 0.1) and near(ey, 100.25, 0.1) and near(xmin, 83.15, 0.1) and near(xmax, 83.70, 0.1):
            return True

    # L RST F at y=98.40 through 3V3_DISP / DC via
    if net == "EPD_RST" and layer == F_CU and not zero:
        if near(sy, 98.40, 0.1) and near(ey, 98.40, 0.1) and xmin <= 83.6 and xmax >= 87.0:
            return True
        if near(sx, 87.35, 0.1) and near(ex, 87.35, 0.1) and near(ymin, 98.40, 0.1) and near(ymax, 99.80, 0.1):
            return True
        if near(sx, 83.50, 0.1) and near(ex, 83.50, 0.1) and near(ymin, 98.40, 0.1) and near(ymax, 99.75, 0.1):
            return True
        if near(sy, 99.75, 0.08) and near(ey, 99.75, 0.08) and near(xmin, 83.15, 0.1) and near(xmax, 83.50, 0.1):
            return True

    # R MOSI via/tracks near SCK@115.65
    if net == "EPD_MOSI" and layer == F_CU:
        if zero and near(sx, 115.40, 0.12) and near(sy, 98.40, 0.12):
            return True
        if not zero and near(sx, 115.40, 0.12) and near(ex, 115.40, 0.12) and ymin <= 98.5 and ymax >= 99.2:
            return True
        if not zero and near(sy, 99.25, 0.1) and near(ey, 99.25, 0.1) and near(xmax, 116.85, 0.1) and near(xmin, 115.40, 0.15):
            return True

    # R DC near RST via
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 112.90, 0.1) and near(ex, 112.90, 0.1) and ymin <= 99.2 and ymax >= 100.5:
            return True
        if near(sy, 99.10, 0.1) and near(ey, 99.10, 0.1) and xmin <= 112.95 and xmax >= 113.6:
            return True
        if near(sy, 100.75, 0.1) and near(ey, 100.75, 0.1) and near(xmax, 116.85, 0.1) and near(xmin, 112.90, 0.15):
            return True
        if near(sx, 113.65, 0.1) and near(ex, 113.65, 0.1) and near(ymin, 98.80, 0.1) and near(ymax, 99.10, 0.1):
            return True

    # MAIN SCK via@99.25,84.90 on MOSI channel
    if net == "EPD_SCK" and layer == F_CU:
        if zero and near(sx, 99.25, 0.12) and near(sy, 84.90, 0.12):
            return True
        if not zero and near(sx, 99.25, 0.1) and near(ex, 99.25, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 84.90, 0.15):
            return True
    if net == "EPD_SCK" and layer == B_CU and not zero:
        if near(sy, 84.90, 0.1) and near(ey, 84.90, 0.1) and xmin <= 99.5 and xmax >= 105.0:
            return True

    # MAIN CS y=85.00 near MOSI 84.90
    if net == "EPD_CS_MAIN" and layer == F_CU and not zero:
        if near(sy, 85.00, 0.08) and near(ey, 85.00, 0.08):
            return True
        if near(sx, 100.80, 0.1) and near(ex, 100.80, 0.1) and near(ymin, 85.00, 0.1) and near(ymax, 86.35, 0.1):
            return True
        if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 85.00, 0.1):
            return True

    # MAIN BUSY horiz@87.60 near DC pad@87.25
    if net == "EPD_BUSY_MAIN" and layer == F_CU and not zero:
        if near(sy, 87.60, 0.08) and near(ey, 87.60, 0.08):
            return True
        if near(sx, 103.75, 0.1) and near(ex, 103.75, 0.1) and near(ymin, 87.60, 0.1) and near(ymax, 90.15, 0.1):
            return True
        if near(sx, 101.55, 0.1) and near(ex, 101.55, 0.1) and ymax <= 87.7 and ymin >= 83.9:
            return True
        if near(sy, 84.00, 0.08) and near(ey, 84.00, 0.08) and near(xmin, 101.25, 0.1) and near(xmax, 101.55, 0.1):
            return True
        if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 84.00, 0.1):
            return True

    # BTN2 bad corridor
    if net == "BTN2":
        if layer == F_CU:
            if not zero and near(sx, 96.25, 0.1) and near(ex, 96.25, 0.1) and near(ymin, 94.95, 0.1) and near(ymax, 96.20, 0.15):
                return True
            if zero and near(sx, 96.25, 0.1) and near(sy, 96.20, 0.1):
                return True
        if layer == B_CU and not zero:
            if near(sx, 96.25, 0.1) and near(ex, 96.25, 0.1):
                return True
            if near(sy, 112.20, 0.1) and near(ey, 112.20, 0.1):
                return True
            if near(sx, 112.80, 0.1) and near(ex, 112.80, 0.1) and near(ymin, 111.50, 0.1) and near(ymax, 112.20, 0.1):
                return True

    return False


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    for t in doomed:
        board.Remove(t)
    pcbnew.SaveBoard(str(PCB), board)
    print(f"D3 deleted {len(doomed)}")

    board = pcbnew.LoadBoard(str(PCB))

    # L DC B: approach at y=101.00 (clear of GND via@86,100)
    add_track(board, 86.350, 98.800, 88.500, 98.800, B_CU, "EPD_DC")
    add_track(board, 88.500, 98.800, 88.500, 101.000, B_CU, "EPD_DC")
    add_track(board, 88.500, 101.000, 83.700, 101.000, B_CU, "EPD_DC")
    if add_via(board, 83.700, 101.000, 0.45, "EPD_DC"):
        add_track(board, 83.700, 101.000, 83.700, 100.250, F_CU, "EPD_DC")
        add_track(board, 83.700, 100.250, 83.150, 100.250, F_CU, "EPD_DC")

    # L RST: B.Cu escape
    add_track(board, 87.350, 99.800, 87.350, 97.500, B_CU, "EPD_RST")
    add_track(board, 87.350, 97.500, 83.700, 97.500, B_CU, "EPD_RST")
    add_track(board, 83.700, 97.500, 83.700, 99.750, B_CU, "EPD_RST")
    if add_via(board, 83.700, 99.750, 0.45, "EPD_RST"):
        add_track(board, 83.700, 99.750, 83.150, 99.750, F_CU, "EPD_RST")

    # R MOSI: east of SCK vertical@115.65
    if add_via(board, 116.200, 98.600, 0.45, "EPD_MOSI"):
        add_track(board, 116.200, 98.600, 116.200, 99.250, F_CU, "EPD_MOSI")
        add_track(board, 116.200, 99.250, 116.850, 99.250, F_CU, "EPD_MOSI")

    # R DC: x=113.30 clear of RST via@112.65
    add_track(board, 113.650, 98.800, 113.650, 99.200, F_CU, "EPD_DC")
    add_track(board, 113.650, 99.200, 113.300, 99.200, F_CU, "EPD_DC")
    add_track(board, 113.300, 99.200, 113.300, 100.750, F_CU, "EPD_DC")
    add_track(board, 113.300, 100.750, 116.850, 100.750, F_CU, "EPD_DC")

    # MAIN SCK via north of MOSI@84.90
    if add_via(board, 99.250, 85.250, 0.45, "EPD_SCK"):
        add_track(board, 99.250, 85.250, 99.250, 83.150, F_CU, "EPD_SCK")
        add_track(board, 99.250, 85.250, 105.500, 85.250, B_CU, "EPD_SCK")

    # MAIN CS at y=85.50
    add_track(board, 100.800, 86.350, 100.800, 85.500, F_CU, "EPD_CS_MAIN")
    add_track(board, 100.800, 85.500, 99.750, 85.500, F_CU, "EPD_CS_MAIN")
    add_track(board, 99.750, 85.500, 99.750, 83.150, F_CU, "EPD_CS_MAIN")

    # MAIN BUSY at y=88.10 clear of DC pad@87.25
    add_track(board, 103.750, 90.150, 103.750, 88.100, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 103.750, 88.100, 101.550, 88.100, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 88.100, 101.550, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 84.000, 101.250, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.250, 84.000, 101.250, 83.150, F_CU, "EPD_BUSY_MAIN")

    # BTN2: east then B vertical at x=97.80 (clear via cluster ~96.x)
    add_track(board, 96.250, 94.950, 97.800, 94.950, F_CU, "BTN2")
    add_track(board, 97.800, 94.950, 97.800, 96.000, F_CU, "BTN2")
    if add_via(board, 97.800, 96.000, 0.45, "BTN2"):
        add_track(board, 97.800, 96.000, 97.800, 112.200, B_CU, "BTN2")
        add_track(board, 97.800, 112.200, 112.800, 112.200, B_CU, "BTN2")
        add_track(board, 112.800, 112.200, 112.800, 111.500, B_CU, "BTN2")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"D3 rebuild ok 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
