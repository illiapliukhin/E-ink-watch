#!/usr/bin/env python3
"""Pass B: rebuild FH12 stubs + signal jogs. No GND deletes. No power-corridor vias."""
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
POGO = (90.5, 101.5, 108.5, 117.0)
POWER = (105.0, 118.5, 101.5, 109.0)


def mm(v):
    return int(round(float(v) * 1e6))


def near(a, b, eps=1e-9):
    return abs(a - b) < eps


def netcode(board, name):
    return board.GetNetInfo().GetNetItem(name).GetNetCode()


def add_track(board, x1, y1, x2, y2, layer, net):
    if near(x1, x2) and near(y1, y2):
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(W))
    t.SetLayer(layer)
    t.SetNetCode(netcode(board, net))
    board.Add(t)


def add_via(board, x, y, d, net):
    if POGO[0] <= x <= POGO[1] and POGO[2] <= y <= POGO[3]:
        print(f"SKIP seal via {x},{y}")
        return False
    if POWER[0] <= x <= POWER[1] and POWER[2] <= y <= POWER[3]:
        print(f"SKIP power via {x},{y}")
        return False
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetWidth(mm(d))
    t.SetLayer(F_CU)
    t.SetNetCode(netcode(board, net))
    board.Add(t)
    return True


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4

    # L strap stubs (off-column jog to pad Y)
    add_track(board, 84.350, 96.800, 84.350, 101.250, F_CU, "EPD_SCK")
    add_track(board, 84.350, 101.250, 83.150, 101.250, F_CU, "EPD_SCK")
    add_track(board, 85.350, 97.800, 85.350, 101.750, F_CU, "EPD_MOSI")
    add_track(board, 85.350, 101.750, 83.150, 101.750, F_CU, "EPD_MOSI")
    add_track(board, 86.350, 98.800, 86.350, 100.250, F_CU, "EPD_DC")
    add_track(board, 86.350, 100.250, 83.150, 100.250, F_CU, "EPD_DC")
    add_track(board, 87.350, 99.800, 83.150, 99.750, F_CU, "EPD_RST")
    add_track(board, 91.200, 96.750, 91.200, 100.750, F_CU, "EPD_CS_L")
    # EPD_BUSY_L: existing F (90.2,97.25)-(90.2,99.25)-(83.15,99.25) kept

    # R strap stubs
    add_track(board, 115.650, 96.800, 115.650, 99.750, F_CU, "EPD_SCK")
    add_track(board, 115.650, 99.750, 116.850, 99.750, F_CU, "EPD_SCK")
    add_track(board, 114.650, 97.800, 114.650, 99.250, F_CU, "EPD_MOSI")
    add_track(board, 114.650, 99.250, 116.850, 99.250, F_CU, "EPD_MOSI")
    add_track(board, 113.650, 98.800, 113.650, 100.750, F_CU, "EPD_DC")
    add_track(board, 113.650, 100.750, 116.850, 100.750, F_CU, "EPD_DC")
    add_track(board, 112.650, 99.800, 112.650, 101.250, F_CU, "EPD_RST")
    add_track(board, 112.650, 101.250, 116.850, 101.250, F_CU, "EPD_RST")
    add_track(board, 108.800, 88.000, 108.800, 99.750, B_CU, "EPD_CS_R")
    add_track(board, 109.800, 99.250, 109.800, 101.750, F_CU, "EPD_BUSY_R")

    # BTN1 / BTN3 clean
    add_track(board, 98.000, 92.950, 98.000, 93.850, F_CU, "BTN1")
    add_track(board, 107.500, 110.500, 107.500, 112.000, F_CU, "BTN1")
    add_track(board, 98.800, 92.950, 98.800, 93.950, F_CU, "BTN3")
    if add_via(board, 98.800, 93.950, 0.45, "BTN3"):
        add_track(board, 98.800, 93.950, 98.800, 109.500, B_CU, "BTN3")
        add_track(board, 98.800, 109.500, 114.800, 109.500, B_CU, "BTN3")

    # nRESET jog west of PMIC_INT
    add_track(board, 94.800, 94.990, 94.200, 94.990, F_CU, "nRESET")
    add_track(board, 94.200, 94.990, 94.200, 90.150, F_CU, "nRESET")
    add_track(board, 94.200, 90.150, 91.620, 90.150, F_CU, "nRESET")

    # EPD_BUSY_MAIN @ y=87.05 clear of U1.15 GND
    add_track(board, 103.750, 90.150, 105.400, 90.150, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 105.400, 90.150, 105.400, 87.050, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 105.400, 87.050, 101.250, 87.050, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.250, 87.050, 101.250, 83.150, F_CU, "EPD_BUSY_MAIN")

    # MAIN stubs
    add_track(board, 99.250, 83.850, 99.250, 83.150, F_CU, "EPD_SCK")
    add_track(board, 100.250, 85.400, 100.250, 83.150, F_CU, "EPD_DC")
    add_track(board, 100.800, 86.350, 101.000, 86.400, F_CU, "EPD_CS_MAIN")
    add_track(board, 101.000, 86.400, 99.750, 86.400, F_CU, "EPD_CS_MAIN")
    add_track(board, 99.750, 86.400, 99.750, 83.150, F_CU, "EPD_CS_MAIN")

    # 3V3 pad30↔pad28 only
    add_track(board, 97.600, 86.350, 98.400, 86.350, F_CU, "3V3")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"pass B rebuild saved; 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
