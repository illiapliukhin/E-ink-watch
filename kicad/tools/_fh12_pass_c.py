#!/usr/bin/env python3
"""Pass C: fix FH12 rebuild regressions. Never delete GND."""
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18


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


def add_track(board, x1, y1, x2, y2, layer, net):
    if near(x1, x2, 1e-9) and near(y1, y2, 1e-9):
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(W))
    t.SetLayer(layer)
    t.SetNetCode(netcode(board, net))
    board.Add(t)


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

    # bad L SCK vertical that crosses 3V3_DISP
    if net == "EPD_SCK" and layer == F_CU and not zero:
        if near(sx, 84.35, 0.1) and near(ex, 84.35, 0.1) and ymin <= 97.0 and ymax >= 100.0:
            return True
        if near(sy, 101.25, 0.1) and near(ey, 101.25, 0.1) and near(xmin, 83.15, 0.1) and near(xmax, 84.35, 0.1):
            return True
        # MAIN channel y=83.85 too close to 3V3_DISP pad
        if near(sy, 83.85, 0.08) and near(ey, 83.85, 0.08) and xmax - xmin > 1.0:
            return True
        if near(sx, 99.25, 0.1) and near(ex, 99.25, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 83.85, 0.1):
            return True
        if zero and near(sx, 97.00, 0.1) and near(sy, 83.85, 0.1):
            return True  # move via with channel (not GND)

    # bad L DC vertical near GND via
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 86.35, 0.1) and near(ex, 86.35, 0.1) and ymin <= 99.0 and ymax >= 100.0:
            return True
        if near(sy, 100.25, 0.1) and near(ey, 100.25, 0.1) and near(xmin, 83.15, 0.1) and xmax <= 86.5:
            return True

    # bad L RST long horizontal into GND via / BUSY
    if net == "EPD_RST" and layer == F_CU and not zero:
        if near(sy, 99.80, 0.12) and near(ey, 99.75, 0.12) and xmin <= 83.2 and xmax >= 87.0:
            return True
        if near(sy, 99.75, 0.08) and near(ey, 99.75, 0.08) and xmin <= 83.2 and xmax >= 87.0:
            return True

    # BUSY_MAIN paths using x=105.4 (hits MP) or x=101.25 through CS via
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

    # CS_MAIN mash near BUSY
    if net == "EPD_CS_MAIN" and layer == F_CU and not zero:
        if near(sx, 100.80, 0.1) and near(sy, 86.35, 0.1) and near(ex, 101.00, 0.1) and near(ey, 86.40, 0.1):
            return True
        if near(sy, 86.40, 0.08) and near(ey, 86.40, 0.08) and xmin <= 99.8 and xmax >= 100.9:
            return True
        if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and ymax >= 86.3 and ymin <= 83.2:
            return True
        if zero and near(sx, 101.00, 0.1) and near(sy, 86.40, 0.1):
            return True

    # nRESET through PMIC_INT via x=94.2
    if net == "nRESET" and layer == F_CU and not zero:
        if near(sx, 94.20, 0.1) and near(ex, 94.20, 0.1):
            return True
        if near(sy, 94.99, 0.1) and near(ey, 94.99, 0.1) and near(xmin, 94.20, 0.1) and near(xmax, 94.80, 0.1):
            return True
        if near(sy, 90.15, 0.1) and near(ey, 90.15, 0.1) and near(xmin, 91.62, 0.15) and near(xmax, 94.20, 0.15):
            return True

    # R MOSI stub that sits on GND via — only our vertical if present; also old horiz at 97.8 into column already gone
    if net == "EPD_MOSI" and layer == F_CU and not zero:
        if near(sx, 114.65, 0.1) and near(ex, 114.65, 0.1) and ymin <= 98.0 and ymax >= 99.0:
            return True
        if near(sy, 99.25, 0.1) and near(ey, 99.25, 0.1) and near(xmax, 116.85, 0.1) and xmin >= 114.5:
            return True

    # R DC vertical may skim CS via — rebuild farther west
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 113.65, 0.1) and near(ex, 113.65, 0.1) and ymin <= 99.0 and ymax >= 100.5:
            return True
        if near(sy, 100.75, 0.1) and near(ey, 100.75, 0.1) and near(xmax, 116.85, 0.1) and xmin >= 113.5:
            return True

    return False


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    for t in doomed:
        board.Remove(t)
    pcbnew.SaveBoard(str(PCB), board)
    print(f"pass C deleted {len(doomed)}")

    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4

    # EPD_SCK L: east of 3V3_DISP spine x=85
    add_track(board, 84.350, 96.800, 85.700, 96.800, F_CU, "EPD_SCK")
    add_track(board, 85.700, 96.800, 85.700, 101.250, F_CU, "EPD_SCK")
    add_track(board, 85.700, 101.250, 83.150, 101.250, F_CU, "EPD_SCK")

    # EPD_DC L: east of GND via@86,100
    add_track(board, 86.350, 98.800, 87.100, 98.800, F_CU, "EPD_DC")
    add_track(board, 87.100, 98.800, 87.100, 100.250, F_CU, "EPD_DC")
    add_track(board, 87.100, 100.250, 83.150, 100.250, F_CU, "EPD_DC")

    # EPD_RST L: south of GND via / clear BUSY_L @99.25
    add_track(board, 87.350, 99.800, 87.350, 99.550, F_CU, "EPD_RST")
    add_track(board, 87.350, 99.550, 83.500, 99.550, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.550, 83.500, 99.750, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.750, 83.150, 99.750, F_CU, "EPD_RST")

    # EPD_SCK MAIN channel y=84.20
    add_track(board, 105.500, 84.200, 97.000, 84.200, F_CU, "EPD_SCK")
    add_track(board, 97.000, 84.200, 99.250, 84.200, F_CU, "EPD_SCK")
    add_track(board, 99.250, 84.200, 99.250, 83.150, F_CU, "EPD_SCK")
    # via for continuity with B if needed — keep F only; old via moved
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(97.000), mm(84.200)))
    t.SetEnd(pcbnew.VECTOR2I(mm(97.000), mm(84.200)))
    t.SetWidth(mm(0.45))
    t.SetLayer(F_CU)
    t.SetNetCode(netcode(board, "EPD_SCK"))
    board.Add(t)

    # EPD_BUSY_MAIN: from U1.13 south then west; CS stays west
    add_track(board, 103.750, 90.150, 103.750, 87.600, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 103.750, 87.600, 101.550, 87.600, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 87.600, 101.550, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.550, 84.000, 101.250, 84.000, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.250, 84.000, 101.250, 83.150, F_CU, "EPD_BUSY_MAIN")

    # EPD_CS_MAIN clean
    add_track(board, 100.800, 86.350, 100.800, 85.000, F_CU, "EPD_CS_MAIN")
    add_track(board, 100.800, 85.000, 99.750, 85.000, F_CU, "EPD_CS_MAIN")
    add_track(board, 99.750, 85.000, 99.750, 83.150, F_CU, "EPD_CS_MAIN")

    # nRESET west of PMIC_INT via@94.2
    add_track(board, 94.800, 94.990, 93.700, 94.990, F_CU, "nRESET")
    add_track(board, 93.700, 94.990, 93.700, 90.150, F_CU, "nRESET")
    add_track(board, 93.700, 90.150, 91.620, 90.150, F_CU, "nRESET")

    # EPD_MOSI R: jog north of GND via@114.5,97.5
    add_track(board, 114.650, 97.800, 114.650, 98.200, F_CU, "EPD_MOSI")
    add_track(board, 114.650, 98.200, 115.200, 98.200, F_CU, "EPD_MOSI")
    add_track(board, 115.200, 98.200, 115.200, 99.250, F_CU, "EPD_MOSI")
    add_track(board, 115.200, 99.250, 116.850, 99.250, F_CU, "EPD_MOSI")

    # EPD_DC R: further west then to pad
    add_track(board, 113.650, 98.800, 113.650, 99.100, F_CU, "EPD_DC")
    add_track(board, 113.650, 99.100, 115.000, 99.100, F_CU, "EPD_DC")
    add_track(board, 115.000, 99.100, 115.000, 100.750, F_CU, "EPD_DC")
    add_track(board, 115.000, 100.750, 116.850, 100.750, F_CU, "EPD_DC")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"pass C rebuild ok; 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
