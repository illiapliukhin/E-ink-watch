#!/usr/bin/env python3
"""Clear remaining pad↔pad power shorts via FP nudge + FH12 pad-axis fix.

Two-pass (pcbnew SWIG invalidates FP iterators after board.Remove):
  Pass A — pad-size fix + footprint moves + endpoint shifts (no deletes)
  Pass B — delete stale tracks + rebuild fanouts
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
BACKUP = ROOT / "backups" / f"e-ink-watch.kicad_pcb.pre-padpad-nudge-{datetime.now():%H%M%S}"

F_CU = pcbnew.F_Cu
W_PWR, W_NECK, W_SIG = 0.35, 0.25, 0.18


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def tomm(v) -> float:
    return pcbnew.ToMM(v)


def near(a, b, eps=0.08):
    return abs(a - b) < eps


def footprints(board):
    return list(board.GetFootprints())


def find_fp(board, ref: str):
    for fp in footprints(board):
        if fp.GetReference() == ref:
            return fp
    raise KeyError(ref)


def pad_xy(fp, num: str):
    for p in list(fp.Pads()):
        if p.GetNumber() == str(num):
            return tomm(p.GetPosition().x), tomm(p.GetPosition().y)
    raise KeyError(num)


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
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetWidth(mm(d))
    t.SetLayer(F_CU)
    t.SetNetCode(netcode(board, net))
    board.Add(t)


def move_fp(fp, nx, ny):
    fp.SetPosition(pcbnew.VECTOR2I(mm(nx), mm(ny)))


def shift_track_ends(board, old_pts, dx, dy, eps=0.15):
    n = 0
    for t in list(board.GetTracks()):
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        nsx, nsy, nex, ney = sx, sy, ex, ey
        for ox, oy in old_pts:
            if near(sx, ox, eps) and near(sy, oy, eps):
                nsx, nsy = sx + dx, sy + dy
            if near(ex, ox, eps) and near(ey, oy, eps):
                nex, ney = ex + dx, ey + dy
        if (nsx, nsy, nex, ney) != (sx, sy, ex, ey):
            t.SetStart(pcbnew.VECTOR2I(mm(nsx), mm(nsy)))
            t.SetEnd(pcbnew.VECTOR2I(mm(nex), mm(ney)))
            n += 1
    return n


def delete_tracks(board, pred, label):
    doomed = [t for t in list(board.GetTracks()) if pred(t)]
    for t in doomed:
        board.Remove(t)
    print(f"  deleted {len(doomed)} [{label}]")
    return len(doomed)


def pass_a_moves(board):
    print("\n=== PASS A: FH12 pad axes + FP nudges ===")

    # FH12: swap pad size so 0.3 mm is along pitch
    for ref in ("J_STRAP_L", "J_STRAP_R"):
        fp = find_fp(board, ref)
        n = 0
        for p in list(fp.Pads()):
            num = p.GetNumber()
            if num in ("MP", "") or not str(num).isdigit():
                continue
            sx, sy = tomm(p.GetSize().x), tomm(p.GetSize().y)
            if sx < sy:
                p.SetSize(pcbnew.VECTOR2I(mm(sy), mm(sx)))
                n += 1
        print(f"  {ref}: swapped {n} pads → 1.3×0.3")

    # R_LSCTRL east+north
    fp = find_fp(board, "R_LSCTRL")
    old = (tomm(fp.GetPosition().x), tomm(fp.GetPosition().y))
    old_pads = [pad_xy(fp, "1"), pad_xy(fp, "2")]
    dx, dy = 0.80, 0.35
    move_fp(fp, old[0] + dx, old[1] + dy)
    print(f"  R_LSCTRL {old} → ({old[0]+dx:.2f},{old[1]+dy:.2f}); ends {shift_track_ends(board, old_pads, dx, dy)}")

    # R2 east
    fp = find_fp(board, "R2")
    old = (tomm(fp.GetPosition().x), tomm(fp.GetPosition().y))
    old_pads = [pad_xy(fp, "1"), pad_xy(fp, "2")]
    dx, dy = 0.45, 0.0
    move_fp(fp, old[0] + dx, old[1] + dy)
    print(f"  R2 {old} → ({old[0]+dx:.2f},{old[1]+dy:.2f}); ends {shift_track_ends(board, old_pads, dx, dy)}")

    # L_SYS east
    fp = find_fp(board, "L_SYS")
    old = (tomm(fp.GetPosition().x), tomm(fp.GetPosition().y))
    old_pads = [pad_xy(fp, "1"), pad_xy(fp, "2")]
    dx, dy = 1.00, 0.0
    move_fp(fp, old[0] + dx, old[1] + dy)
    print(f"  L_SYS {old} → ({old[0]+dx:.2f},{old[1]+dy:.2f}); ends {shift_track_ends(board, old_pads, dx, dy)}")

    # C_SYS / C_VINLS west
    for ref, dx, dy in (("C_SYS", -0.70, 0.0), ("C_VINLS", -0.70, 0.0)):
        fp = find_fp(board, ref)
        old = (tomm(fp.GetPosition().x), tomm(fp.GetPosition().y))
        old_pads = [pad_xy(fp, "1"), pad_xy(fp, "2")]
        move_fp(fp, old[0] + dx, old[1] + dy)
        print(f"  {ref} {old} → ({old[0]+dx:.2f},{old[1]+dy:.2f}); ends {shift_track_ends(board, old_pads, dx, dy)}")


def pass_b_tracks(board):
    print("\n=== PASS B: track cleanup + rebuild ===")

    def stale(t):
        net = t.GetNetname()
        sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        # LSCTRL diving through old C_LDO column
        if net == "LSCTRL":
            if near(sx, 113.8, 0.15) and near(ex, 113.8, 0.15):
                return True
            if near(sy, 106.8, 0.12) and near(ey, 106.8, 0.12) and max(sx, ex) > 112.5:
                return True
            # also any LSCTRL still ending at old R_LSCTRL pad coords
            if (near(sx, 113.8, 0.15) or near(ex, 113.8, 0.15)) and max(sy, ey) > 107.0:
                return True
        # VSYS through inductor body (both pads)
        if net == "VSYS" and near(sy, 104.5, 0.15) and near(ey, 104.5, 0.15):
            lo, hi = min(sx, ex), max(sx, ex)
            if lo < 114.5 and hi > 115.5:
                return True
        # Old SW aimed at previous L_SYS.1 ~113.74 (before +1.0 → now 114.74; kill 113.7 leftovers)
        if net == "SW":
            if near(sx, 113.7375, 0.2) or near(ex, 113.7375, 0.2):
                return True
            if max(sx, ex) > 112.5 and min(sx, ex) < 112.0 and (
                min(sy, ey) < 105.4 and max(sy, ey) > 104.2
            ):
                return True
        # Old VSYS joins at pre-nudge C_SYS pad1 (113.5,105.28)
        if net == "VSYS":
            if (near(sx, 113.5, 0.15) or near(ex, 113.5, 0.15)) and (
                near(sy, 105.28, 0.25) or near(ey, 105.28, 0.25)
            ):
                return True
        return False

    delete_tracks(board, stale, "stale LSCTRL/SW/VSYS")

    # Reload FP refs after deletes via fresh list
    r_ls = find_fp(board, "R_LSCTRL")
    r2 = find_fp(board, "R2")
    lsys = find_fp(board, "L_SYS")
    c_sys = find_fp(board, "C_SYS")
    c_vinls = find_fp(board, "C_VINLS")

    ls_p1, ls_p2 = pad_xy(r_ls, "1"), pad_xy(r_ls, "2")
    r2_p1 = pad_xy(r2, "1")
    sw_pad, vsys_pad = pad_xy(lsys, "1"), pad_xy(lsys, "2")
    csys_p1, csys_p2 = pad_xy(c_sys, "1"), pad_xy(c_sys, "2")
    cvin_p1, cvin_p2 = pad_xy(c_vinls, "1"), pad_xy(c_vinls, "2")
    rx = tomm(r_ls.GetPosition().x)

    # LSCTRL: U2.E3 (111,106.8) → east under new R_LSCTRL → up to pad1
    add_track(board, 111.0, 106.8, rx, 106.8, W_SIG, F_CU, "LSCTRL")
    add_track(board, rx, 106.8, ls_p1[0], ls_p1[1], W_SIG, F_CU, "LSCTRL")
    # 3V3 stub to R_LSCTRL.2
    add_track(board, ls_p2[0], ls_p2[1], ls_p2[0] + 0.6, ls_p2[1], W_NECK, F_CU, "3V3")
    # 3V3 to R2.1
    add_track(board, 106.0, r2_p1[1], r2_p1[0], r2_p1[1], W_PWR, F_CU, "3V3")

    # SW: U2.A4 → y=104.5 → L_SYS.1
    add_track(board, 111.4, 105.2, 111.4, 104.5, W_PWR, F_CU, "SW")
    add_track(board, 111.4, 104.5, sw_pad[0], 104.5, W_PWR, F_CU, "SW")
    if not near(sw_pad[1], 104.5):
        add_track(board, sw_pad[0], 104.5, sw_pad[0], sw_pad[1], W_PWR, F_CU, "SW")

    # VSYS south-of-inductor corridor (avoid SW pad)
    add_track(board, vsys_pad[0], vsys_pad[1], vsys_pad[0], 103.7, W_PWR, F_CU, "VSYS")
    add_track(board, vsys_pad[0], 103.7, 111.8, 103.7, W_PWR, F_CU, "VSYS")
    add_track(board, 111.8, 103.7, 111.8, 105.6, W_PWR, F_CU, "VSYS")
    add_track(board, csys_p1[0], csys_p1[1], csys_p1[0], 103.7, W_NECK, F_CU, "VSYS")
    add_track(board, csys_p1[0], 103.7, 111.8, 103.7, W_NECK, F_CU, "VSYS")

    # GND vias west of caps
    add_track(board, csys_p2[0], csys_p2[1], csys_p2[0] - 0.5, csys_p2[1], W_NECK, F_CU, "GND")
    add_track(board, cvin_p2[0], cvin_p2[1], cvin_p2[0] - 0.5, cvin_p2[1], W_NECK, F_CU, "GND")
    add_via_track(board, csys_p2[0] - 0.5, csys_p2[1], 0.50, "GND")
    add_via_track(board, cvin_p2[0] - 0.5, cvin_p2[1], 0.50, "GND")

    # PMID from C_VINLS.1
    add_track(board, cvin_p1[0], cvin_p1[1], cvin_p1[0], 105.6, W_NECK, F_CU, "PMID")
    add_track(board, cvin_p1[0], 105.6, 111.4, 105.6, W_NECK, F_CU, "PMID")

    print(f"  R_LSCTRL pads {ls_p1} / {ls_p2}")
    print(f"  L_SYS SW={sw_pad} VSYS={vsys_pad}")
    print(f"  C_SYS VSYS={csys_p1} GND={csys_p2}")
    print(f"  C_VINLS PMID={cvin_p1} GND={cvin_p2}")


def verify_gaps(board):
    import math

    def get_pad(ref, num):
        for p in list(find_fp(board, ref).Pads()):
            if p.GetNumber() == str(num):
                return p
        raise KeyError

    def clearance(a, an, b, bn):
        pa, pb = get_pad(a, an), get_pad(b, bn)
        ba = pa.GetEffectiveShape(pcbnew.F_Cu).BBox()
        bb = pb.GetEffectiveShape(pcbnew.F_Cu).BBox()
        if ba.GetRight() < bb.GetLeft():
            h = tomm(bb.GetLeft() - ba.GetRight())
        elif bb.GetRight() < ba.GetLeft():
            h = tomm(ba.GetLeft() - bb.GetRight())
        else:
            h = -tomm(min(ba.GetRight(), bb.GetRight()) - max(ba.GetLeft(), bb.GetLeft()))
        if ba.GetBottom() < bb.GetTop():
            v = tomm(bb.GetTop() - ba.GetBottom())
        elif bb.GetBottom() < ba.GetTop():
            v = tomm(ba.GetTop() - bb.GetBottom())
        else:
            v = -tomm(min(ba.GetBottom(), bb.GetBottom()) - max(ba.GetTop(), bb.GetTop()))
        overlap = h < 0 and v < 0
        if overlap:
            clear = min(h, v)
        elif h < 0:
            clear = v
        elif v < 0:
            clear = h
        else:
            clear = math.hypot(max(h, 0), max(v, 0))
        return clear, overlap

    pairs = [
        ("J_STRAP_L", "1", "J_STRAP_L", "2"),
        ("J_STRAP_L", "9", "J_STRAP_L", "10"),
        ("J_STRAP_R", "1", "J_STRAP_R", "2"),
        ("C_LDO", "1", "R_LSCTRL", "2"),
        ("U1", "2", "R2", "1"),
        ("C_SYS", "2", "L_SYS", "1"),
        ("C_VINLS", "2", "L_SYS", "1"),
    ]
    print("\n=== Post-nudge gaps ===")
    ok = True
    for a, an, b, bn in pairs:
        clear, ov = clearance(a, an, b, bn)
        status = "OK" if (not ov and clear >= 0.15) else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  {status} {a}.{an}↔{b}.{bn}: clear≈{clear:.3f} overlap={ov}")
    return ok


def preserve_check(board):
    print("\n=== Preserve ===")
    assert board.GetCopperLayerCount() == 4
    print("  4L OK")
    nets = sorted({p.GetNetname() for p in list(find_fp(board, "SW_DBG").Pads()) if p.GetNetname()})
    print(f"  SW_DBG nets: {nets}")
    for ref in ("TP1", "FB1", "U2", "J_BAT"):
        find_fp(board, ref)
    print("  charge refs OK")


def main():
    shutil.copy2(PCB, BACKUP)
    print(f"backup → {BACKUP.name}")

    board = pcbnew.LoadBoard(str(PCB))
    pass_a_moves(board)
    board.Save(str(PCB))
    print("  saved after pass A")

    board = pcbnew.LoadBoard(str(PCB))
    pass_b_tracks(board)
    ok = verify_gaps(board)
    preserve_check(board)
    board.Save(str(PCB))
    print(f"\nSaved {PCB} gaps_ok={ok}")


if __name__ == "__main__":
    main()
