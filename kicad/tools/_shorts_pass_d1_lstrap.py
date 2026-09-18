#!/usr/bin/env python3
"""Pass D1: L-strap FH12 stubs only. Never delete GND. No MAIN/power touches."""
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU = pcbnew.F_Cu
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


def should_delete(t) -> bool:
    net = t.GetNetname()
    if net == "GND":
        return False
    if t.GetLayer() != F_CU:
        return False
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    zero = is_zero(t)
    xmin, xmax = min(sx, ex), max(sx, ex)
    ymin, ymax = min(sy, ey), max(sy, ey)

    if net == "EPD_SCK" and not zero:
        if near(sx, 84.35, 0.1) and near(ex, 84.35, 0.1) and ymin <= 97.0 and ymax >= 100.0:
            return True
        if near(sy, 101.25, 0.1) and near(ey, 101.25, 0.1) and near(xmin, 83.15, 0.1) and near(xmax, 84.35, 0.1):
            return True

    if net == "EPD_DC" and not zero:
        if near(sx, 86.35, 0.1) and near(ex, 86.35, 0.1) and ymin <= 99.0 and ymax >= 100.0:
            return True
        if near(sy, 100.25, 0.1) and near(ey, 100.25, 0.1) and near(xmin, 83.15, 0.1) and xmax <= 86.5:
            return True

    if net == "EPD_RST" and not zero:
        if (near(sy, 99.80, 0.15) or near(sy, 99.75, 0.1)) and (
            near(ey, 99.75, 0.15) or near(ey, 99.80, 0.15)
        ):
            if xmin <= 83.2 and xmax >= 87.0:
                return True

    if net == "EPD_BUSY_L" and not zero:
        if near(sx, 90.20, 0.1) and near(ex, 90.20, 0.1) and ymin <= 97.5 and ymax >= 99.0:
            return True
        if near(sy, 99.25, 0.08) and near(ey, 99.25, 0.08) and near(xmin, 83.15, 0.1) and near(xmax, 90.20, 0.1):
            return True  # rebuild pad link from jogged path

    return False


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    for t in doomed:
        board.Remove(t)
    pcbnew.SaveBoard(str(PCB), board)
    print(f"D1 deleted {len(doomed)}")

    board = pcbnew.LoadBoard(str(PCB))
    add_track(board, 84.350, 96.800, 85.700, 96.800, F_CU, "EPD_SCK")
    add_track(board, 85.700, 96.800, 85.700, 101.250, F_CU, "EPD_SCK")
    add_track(board, 85.700, 101.250, 83.150, 101.250, F_CU, "EPD_SCK")

    add_track(board, 86.350, 98.800, 87.150, 98.800, F_CU, "EPD_DC")
    add_track(board, 87.150, 98.800, 87.150, 100.250, F_CU, "EPD_DC")
    add_track(board, 87.150, 100.250, 83.150, 100.250, F_CU, "EPD_DC")

    add_track(board, 87.350, 99.800, 87.350, 99.500, F_CU, "EPD_RST")
    add_track(board, 87.350, 99.500, 83.500, 99.500, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.500, 83.500, 99.750, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.750, 83.150, 99.750, F_CU, "EPD_RST")

    add_track(board, 90.200, 97.250, 89.500, 97.250, F_CU, "EPD_BUSY_L")
    add_track(board, 89.500, 97.250, 89.500, 99.250, F_CU, "EPD_BUSY_L")
    add_track(board, 89.500, 99.250, 83.150, 99.250, F_CU, "EPD_BUSY_L")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"D1 rebuild ok 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
