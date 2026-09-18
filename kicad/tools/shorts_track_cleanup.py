#!/usr/bin/env python3
"""DRC short cleanup: clear track crossings / wrong-layer bridges (surgical).

Applied fixes (no power-corridor edits — those reintroduce GND↔VBUS / 3V3_DISP↔GND):
  1) BTN2/BTN3 B.Cu mash at y=110.8 → keep staggered 111.5 / 109.5 paths
  2) EPD F.Cu bus mash at y=85.2 → staggered channels
  3) Remove 3V3_DISP via @111.5,105.2 (was shorting VSYS neighborhood)
  4) Dedup stacked 3V3 vias @106,87.5

Preserve: 4L, charge path, SW_DBG SWD-only, pogo, IP67 seal (no new vias in land).
Run as two processes if needed (pcbnew SWIG invalidates Tracks after Remove).
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
BACKUP = ROOT / "backups" / f"e-ink-watch.kicad_pcb.pre-track-cleanup-{datetime.now():%H%M%S}"
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W_SIG = 0.18


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def tomm(v) -> float:
    return pcbnew.ToMM(v)


def near(a, b, eps=0.08):
    return abs(a - b) < eps


def netcode(board, name: str) -> int:
    return board.GetNetInfo().GetNetItem(name).GetNetCode()


def is_zero(t, eps=1e-4):
    return abs(tomm(t.GetStart().x) - tomm(t.GetEnd().x)) < eps and abs(
        tomm(t.GetStart().y) - tomm(t.GetEnd().y)
    ) < eps


def seg_match(t, x1, y1, x2, y2, eps=0.08):
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    return (
        (near(sx, x1, eps) and near(sy, y1, eps) and near(ex, x2, eps) and near(ey, y2, eps))
        or (near(sx, x2, eps) and near(sy, y2, eps) and near(ex, x1, eps) and near(ey, y1, eps))
    )


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
        print(f"  SKIP via in seal ({x:.3f},{y:.3f})")
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetWidth(mm(d))
    t.SetLayer(F_CU)
    t.SetNetCode(netcode(board, net))
    board.Add(t)


EPD = {
    "EPD_SCK", "EPD_MOSI", "EPD_DC", "EPD_RST",
    "EPD_CS_MAIN", "EPD_BUSY_MAIN", "EPD_CS_R", "EPD_BUSY_R",
    "EPD_CS_L", "EPD_BUSY_L",
}


def should_delete(t) -> bool:
    net = t.GetNetname()
    layer = t.GetLayer()
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    zero = is_zero(t)
    if net == "BTN2":
        if layer == B_CU and near(sy, 110.8) and near(ey, 110.8) and abs(sx - ex) > 1.0:
            return True
        if zero and near(sx, 112.8) and near(sy, 110.8):
            return True
        if layer == F_CU and seg_match(t, 112.8, 110.8, 112.8, 111.0, eps=0.1):
            return True
        if layer == B_CU and near(sx, 95.45) and near(ex, 95.45):
            if near(max(sy, ey), 110.8) and min(sy, ey) < 100 and max(sy, ey) < 111.2:
                return True
    if net == "BTN3":
        if layer == B_CU and near(sy, 110.8) and near(ey, 110.8) and abs(sx - ex) > 1.0:
            return True
        if layer == B_CU and near(sx, 99.6, 0.12) and near(ex, 99.6, 0.12):
            if near(max(sy, ey), 110.8) and min(sy, ey) < 100:
                return True
        if zero and near(sx, 114.8) and near(sy, 110.8):
            return True
        if layer == F_CU and near(sx, 114.8) and near(ex, 114.8):
            if near(max(sy, ey), 110.8) and min(sy, ey) <= 108.1:
                return True
    if net in EPD and layer == F_CU:
        if near(sy, 85.2, 0.35) and near(ey, 85.2, 0.35) and abs(sx - ex) > 0.8:
            if 95 <= min(sx, ex) <= 107 or 95 <= max(sx, ex) <= 107:
                return True
        if zero and near(sy, 85.2, 0.35) and 96.5 <= sx <= 102.5:
            return True
    if net == "3V3_DISP":
        if zero and near(sx, 111.5, 0.15) and near(sy, 105.2, 0.15):
            return True
        if layer == F_CU and not zero and seg_match(t, 111.8, 106.0, 111.5, 106.0, eps=0.15):
            return True
        if layer == F_CU and not zero and near(sx, 111.5, 0.2) and near(ex, 111.5, 0.2) and max(sy, ey) <= 106.1:
            return True
    return False


def pass_a():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    tracks = list(board.GetTracks())
    doomed = [t for t in tracks if should_delete(t)]
    threes = [
        t
        for t in tracks
        if t.GetNetname() == "3V3"
        and is_zero(t)
        and near(tomm(t.GetStart().x), 106.0, 0.1)
        and near(tomm(t.GetStart().y), 87.5, 0.1)
    ]
    for t in threes[1:]:
        if t not in doomed:
            doomed.append(t)
    for t in doomed:
        board.Remove(t)
    print(f"deleted {len(doomed)}")
    pcbnew.SaveBoard(str(PCB), board)


def pass_b():
    board = pcbnew.LoadBoard(str(PCB))
    add_track(board, 112.8, 111.0, 112.8, 111.5, W_SIG, F_CU, "BTN2")
    add_track(board, 114.8, 108.0, 114.8, 109.5, W_SIG, F_CU, "BTN3")
    add_track(board, 111.800, 106.000, 113.000, 106.000, 0.30, F_CU, "3V3_DISP")
    channels = [
        ("EPD_SCK", 84.40, 97.00, 99.25),
        ("EPD_MOSI", 84.90, 98.00, 98.75),
        ("EPD_DC", 85.40, 99.00, 100.25),
        ("EPD_RST", 85.90, 100.00, 100.75),
        ("EPD_CS_MAIN", 86.40, 101.00, 99.75),
        ("EPD_BUSY_MAIN", 86.90, 102.00, 101.25),
    ]
    for net, ych, xvia, xdrop in channels:
        add_via(board, xvia, ych, 0.45, net)
        add_track(board, xvia, ych, xdrop, ych, W_SIG, F_CU, net)
        add_track(board, xdrop, ych, xdrop, 83.150, W_SIG, F_CU, net)
    add_track(board, 105.500, 84.400, 97.000, 84.400, W_SIG, F_CU, "EPD_SCK")
    add_track(board, 101.600, 86.350, 101.600, 84.900, W_SIG, F_CU, "EPD_MOSI")
    add_track(board, 101.600, 84.900, 98.000, 84.900, W_SIG, F_CU, "EPD_MOSI")
    add_track(board, 102.000, 85.400, 99.000, 85.400, W_SIG, F_CU, "EPD_DC")
    add_track(board, 104.000, 86.350, 104.000, 85.900, W_SIG, F_CU, "EPD_RST")
    add_track(board, 104.000, 85.900, 100.000, 85.900, W_SIG, F_CU, "EPD_RST")
    add_track(board, 100.800, 86.350, 100.800, 86.400, W_SIG, F_CU, "EPD_CS_MAIN")
    add_track(board, 100.800, 86.400, 101.000, 86.400, W_SIG, F_CU, "EPD_CS_MAIN")
    add_track(board, 105.800, 90.150, 105.800, 86.900, W_SIG, F_CU, "EPD_BUSY_MAIN")
    add_track(board, 105.800, 86.900, 102.000, 86.900, W_SIG, F_CU, "EPD_BUSY_MAIN")
    pcbnew.SaveBoard(str(PCB), board)
    print("pass B saved")


def main():
    shutil.copy2(PCB, BACKUP)
    print(f"backup → {BACKUP.name}")
    pass_a()
    # Fresh interpreter recommended for pass_b if SWIG breaks LoadBoard;
    # same-process usually works after Save+implicit release.
    pass_b()
    print("DONE — re-run DRC; expect shorting ~158 if starting from 179")


if __name__ == "__main__":
    main()
