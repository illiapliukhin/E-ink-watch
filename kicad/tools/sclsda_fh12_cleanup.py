#!/usr/bin/env python3
"""DRC short cleanup: remaining SCL/SDA via cluster + FH12 fanouts."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
BACKUP = ROOT / "backups" / f"e-ink-watch.kicad_pcb.pre-sclsda-fh12run-{datetime.now():%H%M%S}"
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W_SIG, W_PWR = 0.18, 0.25


def mm(v: float) -> int:
    return int(round(v * 1e6))


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


def add_via_track(board, x, y, d, net):
    if POGO["xmin"] <= x <= POGO["xmax"] and POGO["ymin"] <= y <= POGO["ymax"]:
        print(f"  SKIP via in seal ({x:.3f},{y:.3f})")
        return False
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetWidth(mm(d))
    t.SetLayer(F_CU)
    t.SetNetCode(netcode(board, net))
    board.Add(t)
    return True


def find_fp(board, ref):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    raise KeyError(ref)


def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            return tomm(p.GetX()), tomm(p.GetY())
    raise KeyError(num)


def fp_xy(fp):
    return tomm(fp.GetX()), tomm(fp.GetY())


def shift_track_ends(board, old_pts, dx, dy, eps=0.12):
    n = 0
    for t in board.GetTracks():
        if is_zero(t):
            continue
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        ns, ne = sx, sy
        changed = False
        for ox, oy in old_pts:
            if near(sx, ox, eps) and near(sy, oy, eps):
                ns, ne = sx + dx, sy + dy
                changed = True
        if changed:
            t.SetStart(pcbnew.VECTOR2I(mm(ns), mm(ne)))
            n += 1
        ns, ne = ex, ey
        changed = False
        for ox, oy in old_pts:
            if near(ex, ox, eps) and near(ey, oy, eps):
                ns, ne = ex + dx, ey + dy
                changed = True
        if changed:
            t.SetEnd(pcbnew.VECTOR2I(mm(ns), mm(ne)))
            n += 1
    return n


def should_delete(t) -> bool:
    net = t.GetNetname()
    layer = t.GetLayer()
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    zero = is_zero(t)

    if net == "SDA":
        if layer == F_CU and not zero and near(sy, 87.25) and near(ey, 87.25):
            if near(min(sx, ex), 98.8, 0.1) and near(max(sx, ex), 99.4, 0.1):
                return True
        if layer == F_CU and not zero and near(sx, 99.4, 0.1) and near(ex, 99.4, 0.1):
            if min(sy, ey) >= 87.2 and max(sy, ey) <= 88.1:
                return True
        if zero and near(sx, 99.4, 0.1) and near(sy, 88.05, 0.1):
            return True
        if zero and near(sx, 111.25, 0.12) and near(sy, 107.45, 0.12):
            return True
        if layer == F_CU and not zero:
            if (near(sx, 111.4, 0.15) and near(ex, 111.25, 0.15)) or (
                near(ex, 111.4, 0.15) and near(sx, 111.25, 0.15)
            ):
                if max(sy, ey) <= 107.55 and min(sy, ey) >= 106.7:
                    return True
        if layer == B_CU and max(sy, ey) <= 107.6 and min(sy, ey) >= 106.9:
            if min(sx, ex) >= 109.0:
                return True

    if net == "SCL":
        if layer == F_CU and not zero and near(sy, 87.25) and near(ey, 87.25):
            if near(min(sx, ex), 98.0, 0.1) and near(max(sx, ex), 98.6, 0.1):
                return True
        if layer == F_CU and not zero and near(sx, 98.6, 0.1) and near(ex, 98.6, 0.1):
            if min(sy, ey) >= 87.2 and max(sy, ey) <= 88.1:
                return True
        if zero and near(sx, 98.6, 0.1) and near(sy, 88.05, 0.1):
            return True
        if zero and near(sx, 112.55, 0.12) and near(sy, 107.85, 0.12):
            return True
        if layer == F_CU and not zero:
            if (near(sx, 111.8, 0.15) or near(ex, 111.8, 0.15)) and (
                near(sx, 112.55, 0.15) or near(ex, 112.55, 0.15)
            ):
                return True
        if layer == B_CU and near(sx, 112.55, 0.15) and near(ex, 112.55, 0.15):
            return True

    if net == "3V3" and layer == F_CU and not zero:
        if near(sy, 107.6, 0.08) and near(ey, 107.6, 0.08):
            if near(min(sx, ex), 110.01, 0.12) and near(max(sx, ex), 112.01, 0.12):
                return True

    if net == "GND" and zero and near(sx, 98.25, 0.12) and near(sy, 84.25, 0.12):
        return True

    if net == "EPD_SCK" and layer == F_CU:
        if near(sy, 84.4, 0.08) and near(ey, 84.4, 0.08) and abs(sx - ex) > 2.0:
            return True
        if zero and near(sx, 97.0, 0.1) and near(sy, 84.4, 0.1):
            return True
        if not zero and near(min(sx, ex), 97.0, 0.1) and near(max(sx, ex), 99.25, 0.1):
            if near(sy, 84.4, 0.1) and near(ey, 84.4, 0.1):
                return True

    if net == "EPD_RST" and layer == F_CU:
        if near(sx, 104.0, 0.12) and near(ex, 104.0, 0.12):
            if min(sy, ey) <= 86.4 and max(sy, ey) >= 85.0:
                return True
        if near(sy, 85.9, 0.1) and near(ey, 85.9, 0.1) and max(sx, ex) >= 103.5:
            return True
        if zero and near(sx, 104.0, 0.15) and near(sy, 87.5, 0.15):
            return True
        if zero and near(sx, 100.0, 0.1) and near(sy, 85.9, 0.1):
            return True

    if net == "EPD_BUSY_MAIN" and layer == F_CU:
        if near(sx, 105.8, 0.12) and near(ex, 105.8, 0.12):
            return True
        if near(sy, 86.9, 0.1) and near(ey, 86.9, 0.1) and max(sx, ex) >= 101.5:
            return True
        if zero and near(sx, 102.0, 0.1) and near(sy, 86.9, 0.1):
            return True
        if (
            near(min(sx, ex), 101.25, 0.15)
            and near(max(sx, ex), 102.0, 0.15)
            and near(sy, 86.9, 0.15)
            and near(ey, 86.9, 0.15)
        ):
            return True

    return False


def pass_delete(board):
    doomed = []
    for t in list(board.GetTracks()):
        if should_delete(t):
            doomed.append(t)
            continue
        # PCB_VIA form of U1 wrong-pad vias
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        if abs(sx - ex) > 1e-4 or abs(sy - ey) > 1e-4:
            continue
        net = t.GetNetname()
        if net == "SDA" and near(sx, 99.4, 0.1) and near(sy, 88.05, 0.1):
            doomed.append(t)
        if net == "SCL" and near(sx, 98.6, 0.1) and near(sy, 88.05, 0.1):
            doomed.append(t)
    for t in doomed:
        board.Remove(t)
    print(f"deleted {len(doomed)}")
    return len(doomed)


def pass_nudge(board):
    fp = find_fp(board, "R_SDA")
    old = fp_xy(fp)
    old_pads = [pad_xy(fp, "1"), pad_xy(fp, "2")]
    dx, dy = 0.20, -0.55
    fp.SetPosition(pcbnew.VECTOR2I(mm(old[0] + dx), mm(old[1] + dy)))
    n = shift_track_ends(board, old_pads, dx, dy)
    print(f"R_SDA {old} -> ({old[0]+dx:.2f},{old[1]+dy:.2f}); ends {n}")

    jd = find_fp(board, "J_DISP_MAIN")
    for p in jd.Pads():
        if p.GetNumber() != "MP":
            continue
        px, py = tomm(p.GetX()), tomm(p.GetY())
        if px < 100:
            continue
        p.SetSize(pcbnew.VECTOR2I(mm(1.0), mm(1.4)))
        p.SetPosition(pcbnew.VECTOR2I(mm(105.10), mm(86.80)))
        print(f"J_DISP_MAIN east MP ({px:.2f},{py:.2f})->(105.10,86.80) 1.0x1.4")


def pass_rebuild(board):
    rs = find_fp(board, "R_SDA")
    rc = find_fp(board, "R_SCL")
    sda1, sda2 = pad_xy(rs, "1"), pad_xy(rs, "2")
    scl1, scl2 = pad_xy(rc, "1"), pad_xy(rc, "2")

    y_jog = max(sda2[1], scl2[1]) + 0.70
    add_track(board, sda2[0], sda2[1], sda2[0], y_jog, W_PWR, F_CU, "3V3")
    add_track(board, sda2[0], y_jog, scl2[0], y_jog, W_PWR, F_CU, "3V3")
    add_track(board, scl2[0], y_jog, scl2[0], scl2[1], W_PWR, F_CU, "3V3")
    print(f"3V3 jog y={y_jog:.2f}")

    add_track(board, sda1[0], sda1[1], 111.400, 106.800, W_SIG, F_CU, "SDA")
    add_track(board, 111.800, 106.800, scl1[0], scl1[1], W_SIG, F_CU, "SCL")

    if add_via_track(board, sda1[0], 106.90, 0.45, "SDA"):
        add_track(board, 98.800, 88.800, 96.400, 88.800, W_SIG, B_CU, "SDA")
        add_track(board, 96.400, 88.800, 96.400, 106.900, W_SIG, B_CU, "SDA")
        add_track(board, 96.400, 106.900, sda1[0], 106.900, W_SIG, B_CU, "SDA")
        add_track(board, sda1[0], 106.900, sda1[0], sda1[1], W_SIG, F_CU, "SDA")
        print(f"SDA B.Cu -> via @({sda1[0]:.2f},106.90)")

    vx, vy = scl1[0], scl1[1] + 0.55
    if add_via_track(board, vx, vy, 0.45, "SCL"):
        add_track(board, 98.000, 89.200, 95.600, 89.200, W_SIG, B_CU, "SCL")
        add_track(board, 95.600, 89.200, 95.600, vy, W_SIG, B_CU, "SCL")
        add_track(board, 95.600, vy, vx, vy, W_SIG, B_CU, "SCL")
        add_track(board, vx, vy, scl1[0], scl1[1], W_SIG, F_CU, "SCL")
        print(f"SCL B.Cu -> via @({vx:.2f},{vy:.2f})")

    add_via_track(board, 97.000, 84.050, 0.45, "EPD_SCK")
    add_track(board, 105.500, 84.050, 97.000, 84.050, W_SIG, F_CU, "EPD_SCK")
    add_track(board, 97.000, 84.050, 99.250, 84.050, W_SIG, F_CU, "EPD_SCK")
    add_track(board, 99.250, 84.050, 99.250, 83.150, W_SIG, F_CU, "EPD_SCK")
    print("EPD_SCK @ y=84.05")

    add_track(board, 104.000, 86.350, 102.600, 86.350, W_SIG, F_CU, "EPD_RST")
    add_track(board, 102.600, 86.350, 102.600, 85.550, W_SIG, F_CU, "EPD_RST")
    add_track(board, 102.600, 85.550, 100.750, 85.550, W_SIG, F_CU, "EPD_RST")
    add_track(board, 100.750, 85.550, 100.750, 83.150, W_SIG, F_CU, "EPD_RST")
    print("EPD_RST west-jog")

    add_track(board, 105.400, 90.150, 105.400, 86.550, W_SIG, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 105.400, 86.550, 101.250, 86.550, W_SIG, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 101.250, 86.550, 101.250, 83.150, W_SIG, F_CU, "EPD_BUSY_MAIN")
    print("EPD_BUSY_MAIN @ y=86.55 x=105.4")


def main():
    shutil.copy2(PCB, BACKUP)
    print(f"backup -> {BACKUP.name}")
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    pass_delete(board)
    pass_nudge(board)
    pcbnew.SaveBoard(str(PCB), board)
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    pass_rebuild(board)
    pcbnew.SaveBoard(str(PCB), board)
    print("DONE")


if __name__ == "__main__":
    main()
