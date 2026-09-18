#!/usr/bin/env python3
"""Pass A: delete FH12 pad-column mash + signal crossing copper. Never delete GND."""
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu


def tomm(v):
    return float(v) / 1e6


def near(a, b, eps=0.08):
    return abs(a - b) < eps


def is_zero(t, eps=1e-4):
    return abs(tomm(t.GetStart().x) - tomm(t.GetEnd().x)) < eps and abs(
        tomm(t.GetStart().y) - tomm(t.GetEnd().y)
    ) < eps


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

    # J_STRAP_L column x=83.15
    if near(sx, 83.15, 0.12) and near(ex, 83.15, 0.12):
        if net in {"EPD_SCK", "EPD_MOSI", "EPD_DC", "EPD_RST", "EPD_CS_L", "EPD_BUSY_L"}:
            if zero and (near(sy, 99.95, 0.15) or near(sy, 100.05, 0.15)):
                return True
            if not zero and (ymax - ymin) > 0.30:
                return True
            if net == "EPD_RST" and not zero and near(ymin, 99.75, 0.1) and near(ymax, 99.80, 0.1):
                return True

    if layer == F_CU and not zero:
        if net == "EPD_SCK" and near(sy, 96.80, 0.1) and near(ey, 96.80, 0.1) and xmin <= 83.2 and xmax <= 85.0:
            return True
        if net == "EPD_MOSI" and near(sy, 97.80, 0.1) and near(ey, 97.80, 0.1) and xmin <= 83.2 and xmax <= 86.0:
            return True
        if net == "EPD_DC" and near(sy, 98.80, 0.1) and near(ey, 98.80, 0.1) and xmin <= 83.2 and xmax <= 87.0:
            return True
        if net == "EPD_RST" and near(sy, 99.80, 0.1) and near(ey, 99.80, 0.1) and xmin <= 83.2 and xmax <= 88.0:
            return True

    if layer == B_CU and near(sx, 83.15, 0.12) and near(ex, 83.15, 0.12) and net in {"EPD_CS_L", "EPD_BUSY_L"}:
        return True
    if layer == B_CU and net == "EPD_BUSY_L" and near(sy, 97.25, 0.1) and near(ey, 97.25, 0.1) and xmin <= 83.2:
        return True
    if layer == B_CU and net == "EPD_CS_L" and near(sy, 88.50, 0.1) and near(ey, 88.50, 0.1) and xmin <= 83.2:
        return True

    # J_STRAP_R column x=116.85
    if near(sx, 116.85, 0.12) and near(ex, 116.85, 0.12):
        if net in {"EPD_SCK", "EPD_MOSI", "EPD_DC", "EPD_RST", "EPD_CS_R", "EPD_BUSY_R"}:
            if zero and (near(sy, 99.45, 0.15) or near(sy, 100.95, 0.15)):
                return True
            if not zero and (ymax - ymin) > 0.30:
                return True

    if layer == F_CU and not zero:
        if net == "EPD_SCK" and near(sy, 96.80, 0.1) and near(ey, 96.80, 0.1) and xmax >= 116.7 and xmin >= 114.5:
            return True
        if net == "EPD_MOSI" and near(sy, 97.80, 0.1) and near(ey, 97.80, 0.1) and xmax >= 116.7 and xmin >= 113.5:
            return True
        if net == "EPD_DC" and near(sy, 98.80, 0.1) and near(ey, 98.80, 0.1) and xmax >= 116.7 and xmin >= 112.5:
            return True
        if net == "EPD_RST" and near(sy, 99.80, 0.1) and near(ey, 99.80, 0.1) and xmax >= 116.7 and xmin >= 111.5:
            return True

    if layer == B_CU and near(sx, 116.85, 0.12) and near(ex, 116.85, 0.12) and net in {"EPD_CS_R", "EPD_BUSY_R"}:
        return True
    if layer == B_CU and net == "EPD_CS_R" and near(sy, 88.00, 0.1) and near(ey, 88.00, 0.1) and xmax >= 116.7:
        return True
    if layer == B_CU and net == "EPD_BUSY_R" and near(sy, 99.25, 0.1) and near(ey, 99.25, 0.1) and xmax >= 116.7:
        return True

    # BTN1 / BTN3
    if net == "BTN1":
        if layer == F_CU and not zero and near(sy, 92.95, 0.08) and near(ey, 92.95, 0.08) and xmin <= 98.05 and xmax >= 98.7:
            return True
        if zero and near(sx, 98.80, 0.12) and near(sy, 93.95, 0.15):
            return True
        if layer == B_CU and near(sx, 98.80, 0.12) and near(ex, 98.80, 0.12):
            return True
        if layer == B_CU and near(sy, 110.80, 0.1) and near(ey, 110.80, 0.1) and xmin <= 99.0 and xmax >= 107.0:
            return True
        if zero and near(sx, 107.50, 0.12) and near(sy, 110.80, 0.12):
            return True
        if layer == F_CU and near(sx, 107.50, 0.12) and near(ex, 107.50, 0.12):
            if ymin <= 110.85 and ymax >= 111.5:
                return True

    if net == "BTN3":
        if layer == F_CU and not zero and near(sy, 92.95, 0.08) and near(ey, 92.95, 0.08) and xmax >= 99.4:
            return True
        if zero and (
            (near(sx, 99.60, 0.12) and near(sy, 93.95, 0.15))
            or (near(sx, 99.70, 0.12) and near(sy, 93.85, 0.15))
        ):
            return True
        if layer == F_CU and not zero and (
            (near(sx, 99.60, 0.12) and near(ex, 99.60, 0.12))
            or (near(sx, 99.70, 0.12) and near(ex, 99.70, 0.12))
        ):
            return True
        if layer == B_CU and near(sx, 99.70, 0.12) and near(ex, 99.70, 0.12):
            return True
        if layer == B_CU and near(sy, 109.50, 0.1) and near(ey, 109.50, 0.1) and xmin <= 100.0:
            return True

    # nRESET / PMIC_INT
    if net == "nRESET" and layer == F_CU and not zero:
        if near(sx, 94.80, 0.1) and near(ex, 94.80, 0.1) and ymin <= 91.0 and ymax >= 94.0:
            return True
    if net == "PMIC_INT":
        if layer == F_CU and not zero and near(sx, 94.85, 0.1) and near(ex, 94.85, 0.1) and ymin <= 89.8 and ymax >= 90.4:
            return True
        if zero and near(sx, 94.85, 0.12) and near(sy, 90.55, 0.12):
            return True
        if layer == B_CU and near(sy, 90.55, 0.1) and near(ey, 90.55, 0.1):
            if xmin <= 94.3 and xmax >= 94.7:
                return True

    # EPD_BUSY_MAIN (clear of U1.15 GND)
    if net == "EPD_BUSY_MAIN":
        if layer == F_CU and not zero:
            if near(sy, 86.55, 0.08) and near(ey, 86.55, 0.08):
                return True
            if near(sx, 105.40, 0.1) and near(ex, 105.40, 0.1) and ymin <= 86.6 and ymax >= 90.0:
                return True
            if near(sy, 85.20, 0.1) and near(ey, 85.20, 0.1):
                return True
            if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1) and ymin <= 84.0 and ymax >= 86.4:
                return True
            if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 83.95, 0.15):
                return True
        if zero and near(sx, 101.25, 0.1) and near(sy, 83.95, 0.1):
            return True

    # EPD_CS_MAIN duplicates
    if net == "EPD_CS_MAIN" and layer == F_CU and not zero:
        # pad to wrong via path
        if near(sx, 100.80, 0.12) and near(sy, 86.35, 0.12) and near(ex, 101.00, 0.12) and near(ey, 85.20, 0.15):
            return True
        if near(ex, 100.80, 0.12) and near(ey, 86.35, 0.12) and near(sx, 101.00, 0.12) and near(sy, 85.20, 0.15):
            return True
        if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and (ymax - ymin) > 2.0:
            return True
        if near(sx, 100.80, 0.1) and near(ex, 100.80, 0.1) and ymax >= 86.3 and ymin <= 85.3:
            return True
        if near(sx, 100.80, 0.1) and near(ex, 100.80, 0.1) and near(ymin, 86.35, 0.1) and near(ymax, 86.40, 0.1):
            return True
        if near(sy, 86.40, 0.08) and near(ey, 86.40, 0.08) and xmin <= 100.0 and xmax >= 100.9:
            return True
        if near(sx, 100.80, 0.1) and near(sy, 86.35, 0.1) and near(ex, 100.80, 0.1) and near(ey, 86.40, 0.1):
            return True
        if near(sx, 101.00, 0.1) and near(sy, 86.40, 0.1) and near(ex, 99.75, 0.1) and near(ey, 86.40, 0.1):
            return True
        if near(ex, 101.00, 0.1) and near(ey, 86.40, 0.1) and near(sx, 99.75, 0.1) and near(sy, 86.40, 0.1):
            return True
        if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and near(ymin, 83.15, 0.1) and ymax <= 85.3:
            return True

    # leftover MAIN fanout stubs
    if net == "EPD_SCK" and layer == F_CU and not zero and near(sx, 99.25, 0.1) and near(ex, 99.25, 0.1):
        if near(ymin, 83.15, 0.1) and ymax >= 84.3:
            return True
    if net == "EPD_MOSI" and layer == F_CU and not zero:
        if near(sy, 85.20, 0.08) and near(ey, 85.20, 0.08):
            return True
        if near(sx, 101.60, 0.1) and near(ex, 101.60, 0.1) and near(ymin, 85.20, 0.15) and ymax >= 86.3:
            return True
    if net == "EPD_DC" and layer == F_CU and not zero and near(sx, 100.25, 0.1) and near(ex, 100.25, 0.1):
        if near(ymin, 83.15, 0.1) and near(ymax, 85.20, 0.1):
            return True
    if net == "EPD_RST" and layer == F_CU and not zero and near(sy, 85.90, 0.08) and near(ey, 85.90, 0.08):
        return True

    # 3V3 overrun into U1 pad 31
    if net == "3V3" and layer == F_CU and not zero and near(sy, 86.35, 0.08) and near(ey, 86.35, 0.08):
        if xmin < 97.40:
            return True

    return False


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    for t in doomed:
        board.Remove(t)
    pcbnew.SaveBoard(str(PCB), board)
    print(f"pass A deleted {len(doomed)}; 4L ok")


if __name__ == "__main__":
    main()
