#!/usr/bin/env python3
"""DRC short cleanup: FH12 strap pad-column mash + signal crossings.

Delete vertical bus tracks/vias ON J_STRAP_L/R pad columns (x=83.15 / 116.85)
that short adjacent FH12 nets; rebuild per-pad stubs off-column.
Also clear BTN1↔BTN3, PMIC_INT↔nRESET crossings, and EPD_BUSY_MAIN vs U1.15 GND
by jogging — NEVER delete GND copper.
Preserve: 4L, charge corridor, SW_DBG, pogo, seal (no new vias in land).
"""
from __future__ import annotations

from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W_SIG = 0.18
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)
# PMIC power neighborhood — do not add copper here
POWER = dict(xmin=105.0, xmax=118.5, ymin=101.5, ymax=109.0)


def mm(v: float) -> int:
    return int(round(float(v) * 1e6))


def tomm(v) -> float:
    return float(v) / 1e6


def near(a, b, eps=0.08):
    return abs(a - b) < eps


def is_zero(t, eps=1e-4):
    return abs(tomm(t.GetStart().x) - tomm(t.GetEnd().x)) < eps and abs(
        tomm(t.GetStart().y) - tomm(t.GetEnd().y)
    ) < eps


def netcode(board, name: str) -> int:
    return board.GetNetInfo().GetNetItem(name).GetNetCode()


def add_track(board, x1, y1, x2, y2, w, layer, net):
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


def pts(t):
    return tomm(t.GetStart().x), tomm(t.GetStart().y), tomm(t.GetEnd().x), tomm(t.GetEnd().y)


def seg(t, x1, y1, x2, y2, eps=0.12):
    sx, sy, ex, ey = pts(t)
    return (
        near(sx, x1, eps) and near(sy, y1, eps) and near(ex, x2, eps) and near(ey, y2, eps)
    ) or (
        near(sx, x2, eps) and near(sy, y2, eps) and near(ex, x1, eps) and near(ey, y1, eps)
    )


def via_at(t, x, y, eps=0.12):
    if not is_zero(t):
        return False
    sx, sy, _, _ = pts(t)
    return near(sx, x, eps) and near(sy, y, eps)


# ---- delete predicates (NEVER match GND) ----
def should_delete(t) -> bool:
    net = t.GetNetname()
    if net == "GND":
        return False  # hard rule
    layer = t.GetLayer()
    sx, sy, ex, ey = pts(t)
    zero = is_zero(t)
    xmin, xmax = min(sx, ex), max(sx, ex)
    ymin, ymax = min(sy, ey), max(sy, ey)

    # --- J_STRAP_L pad column x≈83.15 vertical mash ---
    if near(sx, 83.15, 0.12) and near(ex, 83.15, 0.12):
        if net in {"EPD_SCK", "EPD_MOSI", "EPD_DC", "EPD_RST", "EPD_CS_L", "EPD_BUSY_L"}:
            if zero:
                # vias ON pad column
                if near(sy, 99.95, 0.15) or near(sy, 100.05, 0.15):
                    return True
            else:
                # any vertical run longer than a pad pitch stub
                if (ymax - ymin) > 0.35:
                    return True
                # tiny RST stub 99.80↔99.75 keep? remove with rebuild
                if net == "EPD_RST" and near(ymin, 99.75, 0.1) and near(ymax, 99.80, 0.1):
                    return True

    # wrong-Y stubs into column (will rebuild at pad Y)
    if layer == F_CU and not zero:
        if net == "EPD_SCK" and near(sy, 96.80, 0.1) and near(ey, 96.80, 0.1):
            if xmin <= 83.2 and xmax <= 85.0:
                return True
        if net == "EPD_MOSI" and near(sy, 97.80, 0.1) and near(ey, 97.80, 0.1):
            if xmin <= 83.2 and xmax <= 86.0:
                return True
        if net == "EPD_DC" and near(sy, 98.80, 0.1) and near(ey, 98.80, 0.1):
            if xmin <= 83.2 and xmax <= 87.0:
                return True
        if net == "EPD_RST" and near(sy, 99.80, 0.1) and near(ey, 99.80, 0.1):
            if xmin <= 83.2 and xmax <= 88.0:
                return True

    # B.Cu under L pad column
    if layer == B_CU and near(sx, 83.15, 0.12) and near(ex, 83.15, 0.12):
        if net in {"EPD_CS_L", "EPD_BUSY_L"}:
            return True
    if layer == B_CU and net == "EPD_BUSY_L" and near(sy, 97.25, 0.1) and near(ey, 97.25, 0.1):
        if xmin <= 83.2 and xmax >= 90.0:
            return True  # B horizontal into column
    if layer == B_CU and net == "EPD_CS_L" and near(sy, 88.50, 0.1) and near(ey, 88.50, 0.1):
        if xmin <= 83.2 and xmax >= 90.0:
            return True

    # --- J_STRAP_R pad column x≈116.85 ---
    if near(sx, 116.85, 0.12) and near(ex, 116.85, 0.12):
        if net in {"EPD_SCK", "EPD_MOSI", "EPD_DC", "EPD_RST", "EPD_CS_R", "EPD_BUSY_R"}:
            if zero:
                if near(sy, 99.45, 0.15) or near(sy, 100.95, 0.15):
                    return True
            elif (ymax - ymin) > 0.35:
                return True

    if layer == F_CU and not zero:
        if net == "EPD_SCK" and near(sy, 96.80, 0.1) and near(ey, 96.80, 0.1):
            if xmax >= 116.7 and xmin >= 114.5:
                return True
        if net == "EPD_MOSI" and near(sy, 97.80, 0.1) and near(ey, 97.80, 0.1):
            if xmax >= 116.7 and xmin >= 113.5:
                return True
        if net == "EPD_DC" and near(sy, 98.80, 0.1) and near(ey, 98.80, 0.1):
            if xmax >= 116.7 and xmin >= 112.5:
                return True
        if net == "EPD_RST" and near(sy, 99.80, 0.1) and near(ey, 99.80, 0.1):
            if xmax >= 116.7 and xmin >= 111.5:
                return True

    if layer == B_CU and near(sx, 116.85, 0.12) and near(ex, 116.85, 0.12):
        if net in {"EPD_CS_R", "EPD_BUSY_R"}:
            return True
    if layer == B_CU and net == "EPD_CS_R" and near(sy, 88.00, 0.1) and near(ey, 88.00, 0.1):
        if xmax >= 116.7:
            return True
    if layer == B_CU and net == "EPD_BUSY_R" and near(sy, 99.25, 0.1) and near(ey, 99.25, 0.1):
        if xmax >= 116.7:
            return True

    # --- BTN1 / BTN3 pad mash ---
    if net == "BTN1":
        # horizontal onto BTN3 pad
        if layer == F_CU and not zero and near(sy, 92.95, 0.08) and near(ey, 92.95, 0.08):
            if xmin <= 98.05 and xmax >= 98.7:
                return True
        # contaminated via/path at x=98.8 (BTN3 column)
        if zero and near(sx, 98.80, 0.12) and near(sy, 93.95, 0.15):
            return True
        if layer == B_CU and near(sx, 98.80, 0.12) and near(ex, 98.80, 0.12):
            return True
        if layer == B_CU and near(sy, 110.80, 0.1) and near(ey, 110.80, 0.1):
            if xmin <= 99.0 and xmax >= 107.0:
                return True
        if zero and near(sx, 107.50, 0.12) and near(sy, 110.80, 0.12):
            return True
        if layer == F_CU and near(sx, 107.50, 0.12) and near(ex, 107.50, 0.12):
            if near(ymin, 110.80, 0.15) or near(ymax, 110.80, 0.15):
                if ymax >= 111.5:
                    return True  # duplicate spine; keep 110.50 path

    if net == "BTN3":
        # excursions east onto U1 no-net pads
        if layer == F_CU and not zero and near(sy, 92.95, 0.08) and near(ey, 92.95, 0.08):
            if xmax >= 99.4:
                return True
        if zero and (
            (near(sx, 99.60, 0.12) and near(sy, 93.95, 0.15))
            or (near(sx, 99.70, 0.12) and near(sy, 93.85, 0.15))
        ):
            return True
        if layer == F_CU and not zero:
            if near(sx, 99.60, 0.12) and near(ex, 99.60, 0.12):
                return True
            if near(sx, 99.70, 0.12) and near(ex, 99.70, 0.12):
                return True
        if layer == B_CU and near(sx, 99.70, 0.12) and near(ex, 99.70, 0.12):
            return True
        if layer == B_CU and near(sy, 109.50, 0.1) and near(ey, 109.50, 0.1):
            if xmin <= 100.0:
                return True  # will rebuild from 98.8

    # --- PMIC_INT / nRESET crossing ~x=94.8 ---
    if net == "nRESET" and layer == F_CU and not zero:
        if near(sx, 94.80, 0.1) and near(ex, 94.80, 0.1):
            if ymin <= 91.0 and ymax >= 94.0:
                return True  # rebuild jogged west
    if net == "PMIC_INT":
        # vertical stub into nRESET corridor
        if layer == F_CU and not zero and near(sx, 94.85, 0.1) and near(ex, 94.85, 0.1):
            if ymin <= 89.8 and ymax >= 90.4:
                return True
        if zero and near(sx, 94.85, 0.12) and near(sy, 90.55, 0.12):
            return True
        if layer == B_CU and near(sy, 90.55, 0.1) and near(ey, 90.55, 0.1):
            if near(xmin, 94.2, 0.2) or near(xmax, 94.85, 0.2):
                return True

    # --- EPD_BUSY_MAIN leftovers / too close to U1.15 GND ---
    if net == "EPD_BUSY_MAIN":
        if layer == F_CU and not zero:
            if near(sy, 86.55, 0.08) and near(ey, 86.55, 0.08):
                return True  # rebuild at y=87.05
            if near(sx, 105.40, 0.1) and near(ex, 105.40, 0.1):
                if ymin <= 86.6 and ymax >= 90.0:
                    return True  # rebuild
            if near(sy, 85.20, 0.1) and near(ey, 85.20, 0.1):
                return True
            # duplicate stubs on pad column x=101.25
            if near(sx, 101.25, 0.1) and near(ex, 101.25, 0.1):
                if ymin <= 84.0 and ymax >= 86.4:
                    return True
                if near(ymin, 83.15, 0.1) and near(ymax, 83.95, 0.15):
                    return True  # keep one stub after rebuild
        if zero and near(sx, 101.25, 0.1) and near(sy, 83.95, 0.1):
            return True  # too close to SCK y=83.85; rebuild via south of pad? keep pad stub only

    # --- EPD_CS_MAIN duplicate mash near BUSY ---
    if net == "EPD_CS_MAIN" and layer == F_CU and not zero:
        # diagonal mash
        if seg(t, 100.80, 86.35, 101.00, 85.20, 0.15):
            return True
        # duplicate long drops
        if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and (ymax - ymin) > 2.0:
            return True
        if near(sx, 100.80, 0.1) and near(ex, 100.80, 0.1) and ymax >= 86.3 and ymin <= 85.3:
            return True

    # leftover EPD_SCK stubs on MAIN FPC (keep single channel y=83.85)
    if net == "EPD_SCK" and layer == F_CU and not zero:
        if near(sx, 99.25, 0.1) and near(ex, 99.25, 0.1):
            if near(ymin, 83.15, 0.1) and near(ymax, 85.20, 0.15):
                return True  # old tall stub
            if near(ymin, 83.15, 0.1) and near(ymax, 84.40, 0.15):
                return True

    # leftover EPD_MOSI dual channels
    if net == "EPD_MOSI" and layer == F_CU and not zero:
        if near(sy, 85.20, 0.08) and near(ey, 85.20, 0.08):
            return True
        if near(sx, 101.60, 0.1) and near(ex, 101.60, 0.1) and near(ymin, 85.20, 0.15):
            if ymax >= 86.3:
                return True  # keep 86.35→84.90 path only

    # leftover EPD_DC dual
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 100.25, 0.1) and near(ex, 100.25, 0.1):
            if near(ymax, 85.20, 0.1) and near(ymin, 83.15, 0.1):
                return True

    # leftover EPD_RST old y=85.90
    if net == "EPD_RST" and layer == F_CU and not zero:
        if near(sy, 85.90, 0.08) and near(ey, 85.90, 0.08):
            return True

    # 3V3 extending west into U1 pad 31 (no-net) — signal-adjacent cleanup
    if net == "3V3" and layer == F_CU and not zero:
        if near(sy, 86.35, 0.08) and near(ey, 86.35, 0.08):
            if xmin < 97.40:  # west of pad30 center
                return True

    return False


def pass_delete(board):
    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    # also PCB_VIA class if any
    for t in doomed:
        board.Remove(t)
    print(f"deleted {len(doomed)}")
    return len(doomed)


def pass_rebuild(board):
    # --- L strap: pad Y stubs from existing vias ---
    # EPD_SCK L: via@84.35,96.80 → pad@83.15,101.25
    add_track(board, 84.350, 96.800, 84.350, 101.250, W_SIG, F_CU, "EPD_SCK")
    add_track(board, 84.350, 101.250, 83.150, 101.250, W_SIG, F_CU, "EPD_SCK")
    # EPD_MOSI L: via@85.35,97.80 → pad@83.15,101.75
    add_track(board, 85.350, 97.800, 85.350, 101.750, W_SIG, F_CU, "EPD_MOSI")
    add_track(board, 85.350, 101.750, 83.150, 101.750, W_SIG, F_CU, "EPD_MOSI")
    # EPD_DC L: via@86.35,98.80 → pad@83.15,100.25
    add_track(board, 86.350, 98.800, 86.350, 100.250, W_SIG, F_CU, "EPD_DC")
    add_track(board, 86.350, 100.250, 83.150, 100.250, W_SIG, F_CU, "EPD_DC")
    # EPD_RST L: via@87.35,99.80 → pad@83.15,99.75
    add_track(board, 87.350, 99.800, 83.150, 99.750, W_SIG, F_CU, "EPD_RST")
    # EPD_CS_L: via@91.20,96.75 → horizontal at pad Y (keep existing 91.20→83.15 @100.75)
    add_track(board, 91.200, 96.750, 91.200, 100.750, W_SIG, F_CU, "EPD_CS_L")
    # EPD_BUSY_L: via@90.20,97.25 already has F vertical to 99.25; B ends at via only
    # (F pad link 90.20→83.15 @99.25 kept)

    # --- R strap ---
    add_track(board, 115.650, 96.800, 115.650, 99.750, W_SIG, F_CU, "EPD_SCK")
    add_track(board, 115.650, 99.750, 116.850, 99.750, W_SIG, F_CU, "EPD_SCK")
    add_track(board, 114.650, 97.800, 114.650, 99.250, W_SIG, F_CU, "EPD_MOSI")
    add_track(board, 114.650, 99.250, 116.850, 99.250, W_SIG, F_CU, "EPD_MOSI")
    add_track(board, 113.650, 98.800, 113.650, 100.750, W_SIG, F_CU, "EPD_DC")
    add_track(board, 113.650, 100.750, 116.850, 100.750, W_SIG, F_CU, "EPD_DC")
    add_track(board, 112.650, 99.800, 112.650, 101.250, W_SIG, F_CU, "EPD_RST")
    add_track(board, 112.650, 101.250, 116.850, 101.250, W_SIG, F_CU, "EPD_RST")
    # CS_R: B.Cu vertical at x=108.8 instead of pad column
    add_track(board, 108.800, 88.000, 108.800, 99.750, W_SIG, B_CU, "EPD_CS_R")
    # BUSY_R: F from via@109.8,99.25 up to pad Y
    add_track(board, 109.800, 99.250, 109.800, 101.750, W_SIG, F_CU, "EPD_BUSY_R")

    # --- BTN1 clean escape (pad 61 @98.0,92.95) — keep existing via@98.0,93.85 + B ---
    # add F link pad→via if missing after deletes
    add_track(board, 98.000, 92.950, 98.000, 93.850, W_SIG, F_CU, "BTN1")
    # south B already (98.0,93.85)-(98.0,110.5); ensure F to switch area
    add_track(board, 107.500, 110.500, 107.500, 112.000, W_SIG, F_CU, "BTN1")

    # --- BTN3 clean escape (pad 60 @98.8,92.95) ---
    add_track(board, 98.800, 92.950, 98.800, 93.950, W_SIG, F_CU, "BTN3")
    if add_via(board, 98.800, 93.950, 0.45, "BTN3"):
        add_track(board, 98.800, 93.950, 98.800, 109.500, W_SIG, B_CU, "BTN3")
        add_track(board, 98.800, 109.500, 114.800, 109.500, W_SIG, B_CU, "BTN3")

    # --- nRESET jog west of PMIC_INT ---
    # R1.2 @94.8,94.99 → west → down → to existing 91.62,90.15 bus
    add_track(board, 94.800, 94.990, 94.200, 94.990, W_SIG, F_CU, "nRESET")
    add_track(board, 94.200, 94.990, 94.200, 90.150, W_SIG, F_CU, "nRESET")
    add_track(board, 94.200, 90.150, 91.620, 90.150, W_SIG, F_CU, "nRESET")

    # --- PMIC_INT: keep pad→94.2 via; drop the 94.85 vertical ---
    # existing (95.35,89.75)-(94.2,89.75) + via@94.2,89.75 + B — OK

    # --- EPD_BUSY_MAIN channel y=87.05 (clear U1.15 GND @86.35±0.2) ---
    add_track(board, 103.750, 90.150, 105.400, 90.150, W_SIG, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 105.400, 90.150, 105.400, 87.050, W_SIG, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 105.400, 87.050, 101.250, 87.050, W_SIG, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.250, 87.050, 101.250, 83.150, W_SIG, F_CU, "EPD_BUSY_MAIN")

    # --- EPD_SCK MAIN: single stub pad ← channel ---
    add_track(board, 99.250, 83.850, 99.250, 83.150, W_SIG, F_CU, "EPD_SCK")

    # --- EPD_DC MAIN stub ---
    add_track(board, 100.250, 85.400, 100.250, 83.150, W_SIG, F_CU, "EPD_DC")

    # --- EPD_CS_MAIN: keep pad@100.8,86.35 → via@101.0,86.4 → B → pad column ---
    add_track(board, 100.800, 86.350, 101.000, 86.400, W_SIG, F_CU, "EPD_CS_MAIN")
    add_track(board, 101.000, 86.400, 99.750, 86.400, W_SIG, F_CU, "EPD_CS_MAIN")
    add_track(board, 99.750, 86.400, 99.750, 83.150, W_SIG, F_CU, "EPD_CS_MAIN")

    # --- 3V3: only bridge pad30↔pad28, no west overrun ---
    add_track(board, 97.600, 86.350, 98.400, 86.350, W_SIG, F_CU, "3V3")

    print("rebuild done")


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4, "must stay 4L"
    n = pass_delete(board)
    pcbnew.SaveBoard(str(PCB), board)
    # reload — SWIG Tracks invalidated after Remove
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    pass_rebuild(board)
    pcbnew.SaveBoard(str(PCB), board)
    print(f"DONE deleted={n} 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
