#!/usr/bin/env python3
"""Pass E: surgical non-power short cleanup (CS/DC/RST, SWDCLK_POGO, BTN3, SWD stubs).
Never delete GND copper. Avoid power-zone bulk edits near GND via@111.31,102.9.
"""
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)
# Skip new vias in dense PMIC power pocket
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
        return False  # NEVER delete GND
    layer = t.GetLayer()
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    zero = is_zero(t)
    xmin, xmax = min(sx, ex), max(sx, ex)
    ymin, ymax = min(sy, ey), max(sy, ey)

    # --- L EPD_RST F @y=98.40 through 3V3_DISP + DC via ---
    if net == "EPD_RST" and layer == F_CU and not zero:
        if near(sy, 98.40, 0.1) and near(ey, 98.40, 0.1) and xmin <= 83.6 and xmax >= 87.0:
            return True
        if near(sx, 87.35, 0.1) and near(ex, 87.35, 0.1) and near(ymin, 98.40, 0.1) and near(ymax, 99.80, 0.15):
            return True
        if near(sx, 83.50, 0.1) and near(ex, 83.50, 0.1) and near(ymin, 98.40, 0.1) and near(ymax, 99.75, 0.15):
            return True
        if near(sy, 99.75, 0.08) and near(ey, 99.75, 0.08) and near(xmin, 83.15, 0.1) and near(xmax, 83.50, 0.15):
            return True

    # --- L EPD_DC B path skimming GND via@86,100 ---
    if net == "EPD_DC" and layer == B_CU and not zero:
        if near(sy, 100.25, 0.1) and near(ey, 100.25, 0.1) and xmin <= 84.0 and xmax >= 88.0:
            return True
        if near(sx, 88.50, 0.1) and near(ex, 88.50, 0.1) and ymin <= 99.0 and ymax >= 100.0:
            return True
        if near(sy, 98.80, 0.1) and near(ey, 98.80, 0.1) and near(xmin, 86.35, 0.15) and near(xmax, 88.50, 0.15):
            return True

    # --- R EPD_DC near RST via@112.65 ---
    if net == "EPD_DC" and layer == F_CU and not zero:
        if near(sx, 112.90, 0.1) and near(ex, 112.90, 0.1) and ymin <= 99.2 and ymax >= 100.5:
            return True
        if near(sy, 99.10, 0.1) and near(ey, 99.10, 0.1) and xmin <= 112.95 and xmax >= 113.6:
            return True
        if near(sy, 100.75, 0.1) and near(ey, 100.75, 0.1) and near(xmax, 116.85, 0.1) and near(xmin, 112.90, 0.2):
            return True
        if near(sx, 113.65, 0.1) and near(ex, 113.65, 0.1) and near(ymin, 98.80, 0.1) and near(ymax, 99.10, 0.15):
            return True

    # --- MAIN MOSI channel @y=84.90 (shares SCK via) ---
    if net == "EPD_MOSI" and layer == F_CU and not zero:
        if near(sy, 84.90, 0.08) and near(ey, 84.90, 0.08) and xmin <= 101.7 and xmax >= 98.0:
            return True
        if near(sx, 101.60, 0.1) and near(ex, 101.60, 0.1) and near(ymin, 84.90, 0.1) and near(ymax, 86.35, 0.15):
            return True
        if near(sx, 98.00, 0.1) and near(ex, 98.75, 0.15) and near(sy, 84.90, 0.1) and near(ey, 84.90, 0.1):
            return True
        if near(sx, 98.75, 0.1) and near(ex, 98.75, 0.1) and ymax <= 85.3 and ymin >= 83.0:
            return True

    # --- MAIN CS @y=85.00 near MOSI ---
    if net == "EPD_CS_MAIN" and layer == F_CU and not zero:
        if near(sy, 85.00, 0.08) and near(ey, 85.00, 0.08):
            return True
        if near(sx, 100.80, 0.1) and near(ex, 100.80, 0.1) and near(ymin, 85.00, 0.1) and near(ymax, 86.35, 0.15):
            return True
        if near(sx, 99.75, 0.1) and near(ex, 99.75, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 85.00, 0.15):
            return True

    # --- MAIN SCK via sitting on MOSI y ---
    if net == "EPD_SCK" and layer == F_CU:
        if zero and near(sx, 99.25, 0.12) and near(sy, 84.90, 0.12):
            return True
        if not zero and near(sx, 99.25, 0.1) and near(ex, 99.25, 0.1) and near(ymin, 83.15, 0.1) and near(ymax, 84.90, 0.15):
            return True
    if net == "EPD_SCK" and layer == B_CU and not zero:
        if near(sy, 84.90, 0.1) and near(ey, 84.90, 0.1) and xmin <= 99.5 and xmax >= 105.0:
            return True

    # --- R MOSI via too close to J_STRAP_R pad1 3V3_DISP ---
    if net == "EPD_MOSI" and layer == F_CU:
        if zero and near(sx, 116.20, 0.12) and near(sy, 98.60, 0.12):
            return True
        if not zero and near(sx, 116.20, 0.1) and near(ex, 116.20, 0.1) and ymin <= 98.7 and ymax >= 99.2:
            return True
        if not zero and near(sy, 99.25, 0.1) and near(ey, 99.25, 0.1) and near(xmax, 116.85, 0.1) and near(xmin, 116.20, 0.15):
            return True

    # --- SWDCLK_POGO mash with 3V3 / VBAT / 3V3_DISP ---
    if net == "SWDCLK_POGO" and layer == F_CU and not zero:
        if near(sy, 105.50, 0.1) and near(ey, 105.50, 0.1) and xmax >= 95.0:
            return True
        if near(sx, 96.50, 0.1) and near(ex, 96.50, 0.1) and ymin <= 106.0 and ymax >= 110.5:
            return True
        if near(sy, 111.00, 0.1) and near(ey, 111.00, 0.1) and near(xmin, 93.0, 0.1) and near(xmax, 96.50, 0.15):
            return True

    # --- BTN3 B.Cu @y=109.50 through 3V3/GND vias ---
    if net == "BTN3" and layer == B_CU and not zero:
        if near(sy, 109.50, 0.1) and near(ey, 109.50, 0.1) and xmin <= 99.0 and xmax >= 114.0:
            return True
        if near(sx, 98.80, 0.1) and near(ex, 98.80, 0.1) and ymax >= 109.0 and ymin <= 95.0:
            # keep vertical but trim end — delete whole and rebuild
            return True

    # --- SWDIO stub into J_STRAP_L MP ---
    if net == "SWDIO" and layer == F_CU and not zero:
        if near(sy, 104.50, 0.1) and near(ey, 104.50, 0.1) and xmin <= 86.6 and xmax >= 87.5:
            return True

    # --- SWDCLK vertical @x=89.08 through nRESET stub ---
    if net == "SWDCLK" and layer == F_CU and not zero:
        if near(sx, 89.08, 0.1) and near(ex, 89.08, 0.1) and ymin <= 101.0 and ymax >= 107.5:
            return True
        if near(sy, 105.50, 0.1) and near(ey, 105.50, 0.1) and near(xmin, 87.55, 0.1) and near(xmax, 89.08, 0.15):
            return True
        if near(sy, 100.40, 0.1) and near(ey, 100.40, 0.1) and near(xmin, 89.08, 0.1) and near(xmax, 91.20, 0.15):
            return True
        if near(sx, 89.08, 0.1) and near(ex, 89.08, 0.1) and near(ymin, 100.40, 0.1) and near(ymax, 100.75, 0.15):
            return True

    # --- nRESET stub to x=89.0 (shorts SWDCLK) ---
    if net == "nRESET" and layer == F_CU and not zero:
        if near(sy, 106.50, 0.1) and near(ey, 106.50, 0.1) and near(xmin, 87.55, 0.1) and near(xmax, 89.00, 0.15):
            return True

    return False


def shrink_strap_l_north_mp(board):
    """Shrink/move J_STRAP_L north MP away from SW_DBG pads (do not delete)."""
    for fp in board.GetFootprints():
        if fp.GetReference() != "J_STRAP_L":
            continue
        for p in fp.Pads():
            if p.GetNumber() != "MP":
                continue
            if p.GetNetname() != "GND":
                continue
            px, py = tomm(p.GetPosition().x), tomm(p.GetPosition().y)
            if near(py, 104.65, 0.3):  # north MP
                # was 1.8x2.2 @86.40,104.65 — shrink + west
                p.SetSize(pcbnew.VECTOR2I(mm(1.0), mm(1.4)))
                p.SetPosition(pcbnew.VECTOR2I(mm(85.70), mm(104.65)))
                print(f"  J_STRAP_L north MP → 1.0x1.4 @({85.70},{104.65}) was ({px:.2f},{py:.2f})")
                return True
    return False


def nudge_r_lsctrl(board):
    """Nudge R_LSCTRL west clear of SW3 pad1."""
    for fp in board.GetFootprints():
        if fp.GetReference() != "R_LSCTRL":
            continue
        x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
        # move west 0.55 mm
        fp.SetPosition(pcbnew.VECTOR2I(mm(x - 0.55), mm(y)))
        print(f"  R_LSCTRL ({x:.3f},{y:.3f}) → ({x-0.55:.3f},{y:.3f})")
        return True
    return False


def nudge_r1(board):
    """Nudge R1 west clear of U1 SWD pads."""
    for fp in board.GetFootprints():
        if fp.GetReference() != "R1":
            continue
        x, y = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x - 0.50), mm(y)))
        print(f"  R1 ({x:.3f},{y:.3f}) → ({x-0.50:.3f},{y:.3f})")
        return True
    return False


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4

    doomed = [t for t in list(board.GetTracks()) if should_delete(t)]
    for t in doomed:
        board.Remove(t)
    print(f"E deleted {len(doomed)} non-GND tracks/vias")

    shrink_strap_l_north_mp(board)
    nudge_r_lsctrl(board)
    nudge_r1(board)

    pcbnew.SaveBoard(str(PCB), board)

    board = pcbnew.LoadBoard(str(PCB))

    # L RST: south corridor y=97.55 clear of 3V3_DISP@98.25 and DC vias@98.5
    # keep via@87.35,99.80 — drop south then west then to pad
    add_track(board, 87.350, 99.800, 87.350, 97.550, F_CU, "EPD_RST")
    add_track(board, 87.350, 97.550, 83.500, 97.550, F_CU, "EPD_RST")
    add_track(board, 83.500, 97.550, 83.500, 99.750, F_CU, "EPD_RST")
    add_track(board, 83.500, 99.750, 83.150, 99.750, F_CU, "EPD_RST")

    # L DC B: approach at y=101.10 clear of GND via@86,100
    add_track(board, 86.350, 98.800, 88.500, 98.800, B_CU, "EPD_DC")
    add_track(board, 88.500, 98.800, 88.500, 101.100, B_CU, "EPD_DC")
    add_track(board, 88.500, 101.100, 83.700, 101.100, B_CU, "EPD_DC")
    # existing via@83.70,100.25 — connect down on B then use via
    add_track(board, 83.700, 101.100, 83.700, 100.250, B_CU, "EPD_DC")
    # F stub already: via@83.70,100.25 → pad

    # R DC: x=113.45 clear of RST via@112.65
    add_track(board, 113.650, 98.800, 113.650, 99.250, F_CU, "EPD_DC")
    add_track(board, 113.650, 99.250, 113.450, 99.250, F_CU, "EPD_DC")
    add_track(board, 113.450, 99.250, 113.450, 100.750, F_CU, "EPD_DC")
    add_track(board, 113.450, 100.750, 116.850, 100.750, F_CU, "EPD_DC")

    # MAIN MOSI @y=84.55 (between GND via@84.25 and old SCK@84.90)
    add_track(board, 101.600, 86.350, 101.600, 84.550, F_CU, "EPD_MOSI")
    add_track(board, 101.600, 84.550, 98.000, 84.550, F_CU, "EPD_MOSI")
    # via@98.00,84.90 still exists — connect
    add_track(board, 98.000, 84.550, 98.000, 84.900, F_CU, "EPD_MOSI")
    add_track(board, 98.000, 84.900, 98.750, 84.900, F_CU, "EPD_MOSI")
    add_track(board, 98.750, 84.900, 98.750, 83.150, F_CU, "EPD_MOSI")

    # MAIN SCK via north of MOSI channel — at 85.15 (clear CS below)
    if add_via(board, 99.250, 85.150, 0.45, "EPD_SCK"):
        add_track(board, 99.250, 85.150, 99.250, 83.150, F_CU, "EPD_SCK")
        add_track(board, 99.250, 85.150, 105.500, 85.150, B_CU, "EPD_SCK")

    # MAIN CS @y=85.55 clear of SCK via@85.15 and MOSI@84.55
    add_track(board, 100.800, 86.350, 100.800, 85.550, F_CU, "EPD_CS_MAIN")
    add_track(board, 100.800, 85.550, 99.750, 85.550, F_CU, "EPD_CS_MAIN")
    add_track(board, 99.750, 85.550, 99.750, 83.150, F_CU, "EPD_CS_MAIN")

    # R MOSI: via further west/south clear of pad1 @116.85,98.25
    if add_via(board, 115.900, 99.000, 0.45, "EPD_MOSI"):
        add_track(board, 115.900, 99.000, 115.900, 99.250, F_CU, "EPD_MOSI")
        add_track(board, 115.900, 99.250, 116.850, 99.250, F_CU, "EPD_MOSI")

    # SWDCLK_POGO: north then west vertical @x=95.00 (clear 3V3@96.5, VBAT@96.2, 3V3_DISP@96.0)
    # keep (93.00,108)-(93.00,111) and connect
    add_track(board, 93.450, 105.500, 93.450, 104.700, F_CU, "SWDCLK_POGO")
    add_track(board, 93.450, 104.700, 95.000, 104.700, F_CU, "SWDCLK_POGO")
    add_track(board, 95.000, 104.700, 95.000, 111.000, F_CU, "SWDCLK_POGO")
    add_track(board, 95.000, 111.000, 93.000, 111.000, F_CU, "SWDCLK_POGO")

    # BTN3 B: vertical to y=110.30 then east (clear vias @109.4/109.8)
    add_track(board, 98.800, 93.950, 98.800, 110.300, B_CU, "BTN3")
    add_track(board, 98.800, 110.300, 114.800, 110.300, B_CU, "BTN3")
    add_track(board, 114.800, 110.300, 114.800, 108.000, B_CU, "BTN3")

    # SWDCLK: vertical @x=89.70 (east of nRESET stub end), connect from pad
    add_track(board, 87.550, 105.500, 89.700, 105.500, F_CU, "SWDCLK")
    add_track(board, 89.700, 105.500, 89.700, 100.400, F_CU, "SWDCLK")
    add_track(board, 89.700, 100.400, 91.200, 100.400, F_CU, "SWDCLK")
    # south escape to U1 still via (88.000,96.150)-(89.080,96.150) — bridge
    add_track(board, 89.700, 100.400, 89.700, 96.150, F_CU, "SWDCLK")
    add_track(board, 89.700, 96.150, 88.000, 96.150, F_CU, "SWDCLK")
    # keep north to 108 for any remaining ties
    add_track(board, 89.700, 105.500, 89.700, 108.000, F_CU, "SWDCLK")

    # nRESET: short stub from SW_DBG pad3 — stop at x=88.40 clear of SWDCLK@89.70
    add_track(board, 87.550, 106.500, 88.400, 106.500, F_CU, "nRESET")
    # connect toward existing nRESET vertical @91.62 via jog north of SWDCLK
    add_track(board, 88.400, 106.500, 88.400, 107.200, F_CU, "nRESET")
    add_track(board, 88.400, 107.200, 91.620, 107.200, F_CU, "nRESET")
    add_track(board, 91.620, 107.200, 91.620, 108.000, F_CU, "nRESET")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"E rebuild ok 4L={board.GetCopperLayerCount()}")


if __name__ == "__main__":
    main()
