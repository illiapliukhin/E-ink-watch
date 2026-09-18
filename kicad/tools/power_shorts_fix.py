#!/usr/bin/env python3
"""Fix critical power shorts: GND↔VBUS, GND↔VBAT, GND↔VBUS_POGO, 3V3*↔GND, TS↔VBAT.

Strategy: delete only offending copper; reroute around 0402 GND pads / TVS body.
Preserve: TP1→FB1/TVS→U2.IN→BAT→J_BAT; SW_DBG SWD-only; 4L; pogo; no vias in seal.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
BACKUP = ROOT / "backups" / f"e-ink-watch.kicad_pcb.pre-power-shorts-{datetime.now():%H%M%S}"

POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)  # seal: no NEW vias
W_PWR, W_NECK, W_SIG = 0.35, 0.25, 0.18
F_CU = pcbnew.F_Cu


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def tomm(v) -> float:
    return pcbnew.ToMM(v)


def netcode(board, name: str) -> int:
    return board.GetNetInfo().GetNetItem(name).GetNetCode()


def near(a, b, eps=0.05):
    return abs(a - b) < eps


def seg_match(t, x1, y1, x2, y2, eps=0.05):
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    return (
        (near(sx, x1, eps) and near(sy, y1, eps) and near(ex, x2, eps) and near(ey, y2, eps))
        or (near(sx, x2, eps) and near(sy, y2, eps) and near(ex, x1, eps) and near(ey, y1, eps))
    )


def is_zero(t, eps=1e-4):
    return abs(tomm(t.GetStart().x) - tomm(t.GetEnd().x)) < eps and abs(
        tomm(t.GetStart().y) - tomm(t.GetEnd().y)
    ) < eps


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


def add_via_as_track(board, x, y, d, net):
    """Board historically uses zero-length tracks as vias; keep convention.
    Refuse inside pogo seal keepout."""
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


def delete_tracks(board, pred, label):
    doomed = [t for t in board.GetTracks() if pred(t)]
    for t in doomed:
        board.Remove(t)
    print(f"  deleted {len(doomed)} [{label}]")
    return len(doomed)


def main():
    shutil.copy2(PCB, BACKUP)
    print(f"backup → {BACKUP.name}")
    board = pcbnew.LoadBoard(str(PCB))

    # ------------------------------------------------------------------
    # 1) GND ↔ VBUS  (C_IN cluster)
    # ------------------------------------------------------------------
    print("\n=== Class 1: GND ↔ VBUS ===")

    def del_vbus_cross_cin(t):
        if t.GetNetname() != "VBUS" or is_zero(t):
            return False
        # horizontal through C_IN pads at y=104.5
        if seg_match(t, 108.120, 104.500, 110.600, 104.500, eps=0.08):
            return True
        # stub south from C_IN pad1 into C_BAT lane (VBUS must not go there)
        if seg_match(t, 108.120, 104.500, 108.120, 105.200, eps=0.08):
            return True
        return False

    delete_tracks(board, del_vbus_cross_cin, "VBUS cross C_IN")

    def del_gnd_near_cin_vbus(t):
        if t.GetNetname() != "GND":
            return False
        x1, y1 = tomm(t.GetStart().x), tomm(t.GetStart().y)
        # fake-via directly under / south of C_IN (shorts VBUS pad)
        if is_zero(t) and near(x1, 108.500, 0.08) and near(y1, 104.000, 0.08):
            return True
        # duplicate fake-vias stacked on C_IN pad2 east stub — keep ONE at 109.55 later
        if is_zero(t) and near(y1, 104.500, 0.08) and 109.15 <= x1 <= 109.35:
            return True
        # short 0.12 mm stubs pad2→109.20 (replaced by cleaner fanout)
        if (not is_zero(t)) and seg_match(t, 109.080, 104.500, 109.200, 104.500, eps=0.08):
            return True
        # vertical GND column at x=109.2 from U2 down to C_IN — too close after VBUS east approach
        if (not is_zero(t)) and seg_match(t, 109.200, 105.200, 109.200, 104.500, eps=0.08):
            return True
        return False

    delete_tracks(board, del_gnd_near_cin_vbus, "GND near C_IN VBUS")

    # Keep C_IN on VBUS via west corridor (107,104.5)-(108.12,104.5) already present.
    # Ensure U2.A2 feed from north (R_TS path already exists). Add clear north detour
    # from corridor to U2 as redundancy without crossing C_IN GND pad:
    # (107.0,104.5) → (107.0,103.6) → (110.6,103.6) → (110.6,105.2)
    add_track(board, 107.0, 104.5, 107.0, 103.6, W_PWR, F_CU, "VBUS")
    add_track(board, 107.0, 103.6, 110.6, 103.6, W_PWR, F_CU, "VBUS")
    add_track(board, 110.6, 103.6, 110.6, 105.2, W_PWR, F_CU, "VBUS")

    # Clean GND fanout from C_IN pad2: east then via further out (clear of VBUS north path)
    add_track(board, 109.080, 104.500, 109.700, 104.500, W_NECK, F_CU, "GND")
    add_track(board, 109.700, 104.500, 109.700, 104.000, W_NECK, F_CU, "GND")
    add_via_as_track(board, 109.700, 104.000, 0.50, "GND")
    # link to U2.A1 GND without hugging VBUS
    add_track(board, 110.200, 105.200, 109.700, 105.200, W_NECK, F_CU, "GND")
    add_track(board, 109.700, 105.200, 109.700, 104.500, W_NECK, F_CU, "GND")

    # ------------------------------------------------------------------
    # 2) GND ↔ VBAT  (C_BAT + NTC)
    # ------------------------------------------------------------------
    print("\n=== Class 2: GND ↔ VBAT ===")

    def del_vbat_cross(t):
        if t.GetNetname() != "VBAT":
            return False
        if is_zero(t):
            # keep J_BAT stitch zeros; remove ones that sit on conflict coords
            x, y = tomm(t.GetStart().x), tomm(t.GetStart().y)
            if near(x, 100.000, 0.05) and near(y, 107.900, 0.05):
                return True
            return False
        # diagonals / horizontals through C_BAT body
        if seg_match(t, 108.120, 105.800, 110.200, 105.600, eps=0.10):
            return True
        if seg_match(t, 110.200, 105.600, 108.120, 105.600, eps=0.10):
            return True
        # long run at y=107.9 through NTC GND pad
        if seg_match(t, 110.200, 107.900, 100.000, 107.900, eps=0.10):
            return True
        # long run at y=105.6 through C_BAT — replace with north detour
        if seg_match(t, 110.200, 105.600, 100.000, 105.600, eps=0.10):
            return True
        return False

    delete_tracks(board, del_vbat_cross, "VBAT cross C_BAT/NTC")

    def del_gnd_near_cbat(t):
        if t.GetNetname() != "GND":
            return False
        x1, y1 = tomm(t.GetStart().x), tomm(t.GetStart().y)
        # via between NTC pads (on TS side) — wrong place
        if is_zero(t) and near(x1, 107.910, 0.08) and near(y1, 107.800, 0.08):
            return True
        # via on C_BAT pad2 line
        if is_zero(t) and near(x1, 109.550, 0.08) and near(y1, 105.800, 0.08):
            return True
        # short stubs pad2→109.20
        if (not is_zero(t)) and seg_match(t, 109.080, 105.800, 109.200, 105.800, eps=0.08):
            return True
        if (not is_zero(t)) and seg_match(t, 109.080, 105.800, 109.550, 105.800, eps=0.08):
            return True
        # via between C_IN/C_BAT at 108.5,106.5 — may be ok but check later
        return False

    delete_tracks(board, del_gnd_near_cbat, "GND near C_BAT/NTC")

    # VBAT north-of-caps corridor: U2.B1 → north → west past caps → down → to J_BAT column
    # U2.B1 = (110.2, 105.6); C_BAT pad1 = (108.12, 105.8); J_BAT pad1 = (100, 115.8)
    # Existing vertical (100,105.6)-(100,115.8) kept.
    add_track(board, 110.200, 105.600, 110.200, 106.700, W_PWR, F_CU, "VBAT")
    add_track(board, 110.200, 106.700, 107.000, 106.700, W_PWR, F_CU, "VBAT")
    add_track(board, 107.000, 106.700, 107.000, 105.600, W_PWR, F_CU, "VBAT")
    add_track(board, 107.000, 105.600, 100.000, 105.600, W_PWR, F_CU, "VBAT")
    # C_BAT pad1 join into corridor (north)
    add_track(board, 108.120, 105.800, 108.120, 106.700, W_NECK, F_CU, "VBAT")
    add_track(board, 108.120, 106.700, 107.000, 106.700, W_NECK, F_CU, "VBAT")
    # keep pad1 neck if vertical to 105.6 still useful — already may exist; ensure:
    # (optional) leave (108.12,105.6)-(108.12,105.8) if present

    # C_BAT GND fanout: east then south (away from VBAT north corridor)
    add_track(board, 109.080, 105.800, 109.800, 105.800, W_NECK, F_CU, "GND")
    add_track(board, 109.800, 105.800, 109.800, 105.200, W_NECK, F_CU, "GND")
    add_via_as_track(board, 109.800, 105.200, 0.50, "GND")

    # NTC GND: east stub + via (clear of any residual VBAT)
    add_track(board, 108.710, 107.800, 109.500, 107.800, W_NECK, F_CU, "GND")
    add_track(board, 109.500, 107.800, 109.500, 108.400, W_NECK, F_CU, "GND")
    add_via_as_track(board, 109.500, 108.400, 0.50, "GND")

    # ------------------------------------------------------------------
    # 3) GND ↔ VBUS_POGO  (D_TVS body)
    # ------------------------------------------------------------------
    print("\n=== Class 3: GND ↔ VBUS_POGO ===")

    def del_vbus_pogo_through_tvs(t):
        if t.GetNetname() != "VBUS_POGO" or is_zero(t):
            return False
        if seg_match(t, 88.150, 112.500, 93.000, 112.500, eps=0.10):
            return True
        return False

    delete_tracks(board, del_vbus_pogo_through_tvs, "VBUS_POGO through TVS")

    # Reroute around TVS body (south of pads — away from pogo row at y=114)
    # pad1 (88.15,112.5) → south → east → join (93,112.5)
    add_track(board, 88.150, 112.500, 88.150, 111.600, W_PWR, F_CU, "VBUS_POGO")
    add_track(board, 88.150, 111.600, 93.000, 111.600, W_PWR, F_CU, "VBUS_POGO")
    add_track(board, 93.000, 111.600, 93.000, 112.500, W_PWR, F_CU, "VBUS_POGO")
    # GND pad2 already has stub north — keep

    # ------------------------------------------------------------------
    # 4) 3V3 / 3V3_DISP ↔ GND
    # ------------------------------------------------------------------
    print("\n=== Class 4: 3V3/3V3_DISP ↔ GND ===")

    def del_3v3_gnd(t):
        net = t.GetNetname()
        if net not in ("3V3", "3V3_DISP", "GND"):
            return False
        x1, y1 = tomm(t.GetStart().x), tomm(t.GetStart().y)
        x2, y2 = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        # 3V3 track near GND via @ 103.48,109.6
        if net == "3V3" and (not is_zero(t)):
            if seg_match(t, 101.438, 109.200, 103.500, 109.200, eps=0.15) or (
                near(y1, 109.200, 0.1) and min(x1, x2) < 103.6 and max(x1, x2) > 101.0
                and abs(tomm(t.GetWidth()) - 0.0) >= 0  # any
            ):
                # only the specific shorting segment ~2.06mm at y=109.2
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if near(y1, 109.2, 0.15) and near(y2, 109.2, 0.15) and 1.5 < length < 2.5:
                    return True
        if net == "3V3" and is_zero(t) and near(x1, 103.500, 0.08) and near(y1, 109.200, 0.08):
            return True
        if net == "GND" and is_zero(t) and near(x1, 103.480, 0.08) and 109.35 <= y1 <= 109.65:
            return True
        # 3V3_DISP vs GND via @ 115.2,106.5 — B.Cu track; skip layer edits carefully
        if net == "3V3_DISP" and (not is_zero(t)):
            # track near J_DISP_MAIN pad2: (97.75,82.4) length 4.5
            if near(x1, 97.750, 0.15) or near(x2, 97.750, 0.15):
                if min(y1, y2) < 83.5 and max(y1, y2) > 80.0:
                    # narrow: only if it's the shorting F.Cu run at ~82.4
                    if near(y1, 82.400, 0.2) or near(y2, 82.400, 0.2):
                        return True
            # J_STRAP_L: (84.45,102.75) len 1.3
            if (near(x1, 84.450, 0.1) or near(x2, 84.450, 0.1)) and (
                near(y1, 102.750, 0.2) or near(y2, 102.750, 0.2)
            ):
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if 1.0 < length < 1.6:
                    return True
            # J_STRAP_R area via 114.5,106
            if is_zero(t) and near(x1, 114.500, 0.1) and near(y1, 106.000, 0.1):
                return True
            # (115.55,98.25) vs GND via 115.75,98.75
            if (near(x1, 115.550, 0.1) or near(x2, 115.550, 0.1)) and (
                near(y1, 98.250, 0.2) or near(y2, 98.250, 0.2)
            ):
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if 1.0 < length < 1.6:
                    return True
        if net == "GND" and is_zero(t):
            if near(x1, 115.200, 0.1) and near(y1, 106.500, 0.1):
                return True
            if near(x1, 115.750, 0.1) and near(y1, 98.750, 0.1):
                return True
        return False

    delete_tracks(board, del_3v3_gnd, "3V3/3V3_DISP↔GND offenders")

    # ------------------------------------------------------------------
    # 5) TS ↔ VBAT
    # ------------------------------------------------------------------
    print("\n=== Class 5: TS ↔ VBAT ===")

    def del_ts_vbat(t):
        if t.GetNetname() != "TS" or is_zero(t):
            return False
        x1, y1 = tomm(t.GetStart().x), tomm(t.GetStart().y)
        x2, y2 = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
        # horizontal TS at y=106 across VBAT zone — keep but will clear after VBAT move;
        # diagonal from NTC pad1 to U2.C3 crosses VBAT corridor at 106.7
        if seg_match(t, 107.690, 107.800, 111.000, 106.000, eps=0.15):
            return True
        # vertical TS on pad1 column that crossed old VBAT: (107.69,106)-(107.69,107.8)
        # keep — VBAT no longer at 107.9
        return False

    delete_tracks(board, del_ts_vbat, "TS diagonal across VBAT")

    # Clean TS Manhattan: NTC pad1 (107.69,107.8) → west slightly → north of VBAT corridor
    # VBAT corridor at y=106.7; route TS at y=107.3 then to U2.C3 (111,106)
    add_track(board, 107.690, 107.800, 107.690, 107.300, W_SIG, F_CU, "TS")
    add_track(board, 107.690, 107.300, 111.000, 107.300, W_SIG, F_CU, "TS")
    add_track(board, 111.000, 107.300, 111.000, 106.000, W_SIG, F_CU, "TS")
    # R_TS pad2 (108.71,107) already has paths; leave existing Manhattan if present

    # Also remove leftover VBUS stub that went to R_TS at y=107 if it crosses new VBAT?
    # VBUS (107.69,107)-(110.6,107) is BETWEEN TS 107.3 and VBAT 106.7 — OK clearance ~0.3

    pcbnew.Refresh()
    board.Save(str(PCB))
    print(f"\nSaved {PCB}")
    print("Done. Re-run DRC next.")


if __name__ == "__main__":
    main()
