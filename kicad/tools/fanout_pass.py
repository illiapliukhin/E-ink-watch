#!/usr/bin/env python3
"""Professional fanout pass after MDBT50Q + BQ25120A footprint upgrade.

Goals: connect critical nets (power, SWD via SW_DBG, SPI→FPCs, I2C→PMIC,
buttons, pogo path). Respect Ø40, pogo 2×3@3mm, PowerFat/Signal widths.
Does NOT claim fab-ready.
"""
from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
BACKUP = ROOT / "backups" / f"e-ink-watch.kicad_pcb.pre-fanout-script-{datetime.now():%H%M%S}"

# Physics / net-class widths (mm) — see CALC_POWER_TRACES.md + .kicad_pro
W_SIG = 0.18
W_PWR = 0.45
W_FAT = 0.50
W_ESCAPE = 0.25  # local module escape before neck-down
VIA_D = 0.60
VIA_DRILL = 0.30
CX, CY, R = 100.0, 100.0, 20.0


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def uid() -> str:
    return str(uuid.uuid4())


def netcode(board: pcbnew.BOARD, name: str) -> int:
    ni = board.GetNetInfo().GetNetItem(name)
    if ni is None:
        raise KeyError(name)
    return ni.GetNetCode()


def ensure_net(board: pcbnew.BOARD, name: str) -> int:
    ni = board.GetNetInfo().GetNetItem(name)
    if ni is not None:
        return ni.GetNetCode()
    # Find max net code and add
    info = board.GetNetInfo()
    # KiCad 9: FindNet / AddNet
    new = pcbnew.NETINFO_ITEM(board, name)
    board.Add(new)
    return new.GetNetCode()


def find_fp(board: pcbnew.BOARD, ref: str):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    raise KeyError(ref)


def pad_xy(board: pcbnew.BOARD, ref: str, num: str) -> tuple[float, float]:
    fp = find_fp(board, ref)
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            pos = p.GetPosition()
            return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
    raise KeyError(f"{ref}.{num}")


def set_pad_net(board: pcbnew.BOARD, ref: str, num: str, netname: str) -> None:
    fp = find_fp(board, ref)
    code = ensure_net(board, netname)
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            p.SetNetCode(code)
            return
    raise KeyError(f"{ref}.{num}")


def add_track(board, x1, y1, x2, y2, width, layer, netname):
    if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNetCode(netcode(board, netname))
    board.Add(t)
    return t


def add_via(board, x, y, netname):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    # KiCad 9: layer-aware via width
    try:
        v.SetWidth(pcbnew.F_Cu, mm(VIA_D))
    except TypeError:
        v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNetCode(netcode(board, netname))
    board.Add(v)
    return v


def poly_track(board, pts, width, layer, netname):
    """pts: list of (x,y); consecutive segments."""
    for a, b in zip(pts, pts[1:]):
        add_track(board, a[0], a[1], b[0], b[1], width, layer, netname)


def delete_tracks_matching(board, pred):
    """Delete tracks/vias where pred(track)->True."""
    doomed = [t for t in list(board.GetTracks()) if pred(t)]
    for t in doomed:
        board.Delete(t)
    return len(doomed)


def near(x, y, x0, y0, tol=0.05):
    return abs(x - x0) <= tol and abs(y - y0) <= tol


def seg_endpoints(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        return [(x, y)]
    a, b = t.GetStart(), t.GetEnd()
    return [
        (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)),
        (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)),
    ]


def main() -> None:
    shutil.copy2(PCB, BACKUP)
    board = pcbnew.LoadBoard(str(PCB))
    F = pcbnew.F_Cu
    B = pcbnew.B_Cu

    # ------------------------------------------------------------------
    # 0) Create I2C / INT nets and assign pads (Raytac DS + BQ25120A)
    #    U1.27=P0.11 SDA, U1.29=P0.12 SCL, U1.39=P0.15 PMIC_INT
    #    U2.E4=SDA, U2.E5=SCL, U2.D2=INT
    # ------------------------------------------------------------------
    for n in ("SDA", "SCL", "PMIC_INT"):
        ensure_net(board, n)
    set_pad_net(board, "U1", "27", "SDA")
    set_pad_net(board, "U1", "29", "SCL")
    set_pad_net(board, "U1", "39", "PMIC_INT")
    set_pad_net(board, "U2", "E4", "SDA")
    set_pad_net(board, "U2", "E5", "SCL")
    set_pad_net(board, "U2", "D2", "PMIC_INT")

    # ------------------------------------------------------------------
    # 1) Remove known-bad / shorting stubs from fp-upgrade minimal fanout
    # ------------------------------------------------------------------
    def is_bad(t) -> bool:
        n = t.GetNetname()
        pts = seg_endpoints(t)
        # Horizontal 3V3 across U1 north pad row (SHORTS MOSI/CS/RST/GND)
        if n == "3V3" and t.GetClass() != "PCB_VIA":
            (x1, y1), (x2, y2) = pts[0], pts[1]
            if abs(y1 - 86.35) < 0.08 and abs(y2 - 86.35) < 0.08:
                if min(x1, x2) < 100 and max(x1, x2) > 102:
                    return True
        # VSYS vertical spine into module east column (clearance / short risk)
        if n == "VSYS" and t.GetClass() != "PCB_VIA":
            (x1, y1), (x2, y2) = pts[0], pts[1]
            if abs(x1 - 105.0) < 0.08 and abs(x2 - 105.0) < 0.08:
                if min(y1, y2) < 90 and max(y1, y2) > 100:
                    return True
        # Old thin VBAT/VBUS duplicates that fight PowerFat corridors (keep fat ones)
        if n in ("VBAT", "VBUS") and t.GetClass() != "PCB_VIA":
            w = pcbnew.ToMM(t.GetWidth())
            if w < 0.40:
                # keep only if not the duplicate thin paths added at upgrade
                (x1, y1), (x2, y2) = pts[0], pts[1]
                if n == "VBUS" and (near(x1, y1, 93, 110, 0.2) or near(x2, y2, 108, 110, 0.2) or near(x1, y1, 108, 105.2, 0.2)):
                    return True
                if n == "VBAT" and (near(x1, y1, 110.2, 112, 0.2) or near(x2, y2, 100, 112, 0.2)):
                    return True
        return False

    n_del = delete_tracks_matching(board, is_bad)
    print(f"deleted bad tracks: {n_del}")

    # After deleting thin VBUS, ensure fat path reaches U2.A2
    # Existing fat: TP1(93,114)-(93,112.2)-(99.2,112.2)+via — extend to A2
    a2 = pad_xy(board, "U2", "A2")
    # Route PowerFat around bottom of PMIC
    poly_track(
        board,
        [(99.2, 112.2), (110.6, 112.2), (a2[0], 112.2), (a2[0], a2[1])],
        W_FAT,
        F,
        "VBUS",
    )

    # ------------------------------------------------------------------
    # 2) U2 local ball ties (0.4 mm pitch — use 0.20 mm necks between balls)
    # ------------------------------------------------------------------
    W_BGA = 0.20
    # VBAT B1-B2
    b1, b2 = pad_xy(board, "U2", "B1"), pad_xy(board, "U2", "B2")
    add_track(board, b1[0], b1[1], b2[0], b2[1], W_BGA, F, "VBAT")
    # Connect B1 to existing VBAT corridor at (96.2, 106.25) via south then west
    # Fat path from J_BAT already to (96.2,106.25); bridge to B1
    poly_track(
        board,
        [(b1[0], b1[1]), (b1[0], 107.2), (96.2, 107.2), (96.2, 106.25)],
        W_FAT,
        F,
        "VBAT",
    )

    # VSYS B5-B4-C4
    b5, b4, c4 = pad_xy(board, "U2", "B5"), pad_xy(board, "U2", "B4"), pad_xy(board, "U2", "C4")
    add_track(board, b5[0], b5[1], b4[0], b4[1], W_BGA, F, "VSYS")
    add_track(board, b4[0], b4[1], c4[0], c4[1], W_BGA, F, "VSYS")
    # Escape VSYS west then to 0Ω landing
    poly_track(
        board,
        [(b5[0], b5[1]), (b5[0], 104.4), (107.5, 104.4)],
        W_PWR,
        F,
        "VSYS",
    )

    # GND A1-A5-D5 local + stub to exterior
    a1, a5, d5 = pad_xy(board, "U2", "A1"), pad_xy(board, "U2", "A5"), pad_xy(board, "U2", "D5")
    add_track(board, a1[0], a1[1], a5[0], a5[1], W_BGA, F, "GND")
    add_track(board, a5[0], a5[1], d5[0], d5[1], W_BGA, F, "GND")
    # Escape GND from A1 west + via to B.Cu pour
    poly_track(board, [(a1[0], a1[1]), (108.5, a1[1]), (108.5, 104.0)], W_PWR, F, "GND")
    add_via(board, 108.5, 104.0, "GND")

    # 3V3_DISP C5 → join right-strap 3V3_DISP spine at x≈115.55
    c5 = pad_xy(board, "U2", "C5")
    poly_track(
        board,
        [(c5[0], c5[1]), (114.5, c5[1]), (114.5, 102.75), (115.55, 102.75)],
        W_PWR,
        F,
        "3V3_DISP",
    )
    # Stitch B.Cu 3V3_DISP fragments: via@104,105.2 ↔ via@96,105.2 ↔ lane
    poly_track(board, [(104.0, 105.2), (96.0, 105.2)], W_PWR, B, "3V3_DISP")
    # Connect via@104 to C5 neighborhood on F already partially; add via near escape
    add_via(board, 114.5, 106.0, "3V3_DISP")
    # Link left B.Cu spine (92,105.5)-(92,87) to via@92,87 already; connect 92↔94 at y=87
    poly_track(board, [(92.0, 87.0), (94.0, 87.0)], W_PWR, B, "3V3_DISP")
    # Tie via@96,105.2 to B.Cu vertical at 92 via horizontal
    poly_track(board, [(96.0, 105.2), (92.0, 105.2), (92.0, 105.5)], W_PWR, B, "3V3_DISP")
    # F.Cu: connect dangling left 3V3_DISP track end near (84.45,108.5) already has via —
    # connect main FPC 3V3_DISP at y=82.4 to via@94,87
    poly_track(board, [(97.75, 82.4), (94.0, 82.4), (94.0, 87.0)], W_PWR, F, "3V3_DISP")

    # ------------------------------------------------------------------
    # 3) U1 power: tie VDD pads + escape to 3V3 island (C1/C2/zone)
    # ------------------------------------------------------------------
    p28, p30 = pad_xy(board, "U1", "28"), pad_xy(board, "U1", "30")
    add_track(board, p28[0], p28[1], p30[0], p30[1], W_ESCAPE, F, "3V3")
    # Escape south-west around module to C1 @ (94.92,102.2) — left side corridor
    # From p30 (97.6,86.35) left to x=94.5 then south — avoid pad column
    poly_track(
        board,
        [
            (p30[0], p30[1]),
            (p30[0], 85.6),
            (93.5, 85.6),
            (93.5, 98.5),
            (94.9, 98.5),
            (94.9, 101.95),
        ],
        W_PWR,
        F,
        "3V3",
    )
    # Also stitch R2 3V3 (105.2,96.01) from east escape of p28
    poly_track(
        board,
        [(p28[0], p28[1]), (p28[0], 85.6), (106.0, 85.6), (106.0, 96.01), (105.2, 96.01)],
        W_PWR,
        F,
        "3V3",
    )
    # Tie C2 3V3 to B.Cu already (101.05,103.35)-(104.95,103.35); connect C2 pad to via
    poly_track(board, [(104.12, 102.2), (104.12, 103.35), (101.05, 103.35)], W_PWR, F, "3V3")
    add_via(board, 104.95, 103.35, "3V3")  # if not exists — ok duplicate nearby

    # U1 GND pad ties: 1-2, and vias out
    g1, g2 = pad_xy(board, "U1", "1"), pad_xy(board, "U1", "2")
    add_track(board, g1[0], g1[1], g2[0], g2[1], W_ESCAPE, F, "GND")
    g55 = pad_xy(board, "U1", "55")
    g33 = pad_xy(board, "U1", "33")
    g15 = pad_xy(board, "U1", "15")
    # Escape GND pad1 east then south to C2 GND
    poly_track(
        board,
        [(g1[0], g1[1]), (106.2, g1[1]), (106.2, 102.2), (105.08, 102.2)],
        W_PWR,
        F,
        "GND",
    )
    add_via(board, 106.2, 100.0, "GND")
    # Escape GND pad55 west to C1 GND
    poly_track(
        board,
        [(g55[0], g55[1]), (93.8, g55[1]), (93.8, 102.2), (95.88, 102.2)],
        W_PWR,
        F,
        "GND",
    )
    add_via(board, 93.8, 98.0, "GND")
    # Tie g15 and g33 with short stubs + via (antenna-side GND)
    poly_track(board, [(g15[0], g15[1]), (g15[0], 85.5)], W_PWR, F, "GND")
    add_via(board, g15[0], 85.5, "GND")
    poly_track(board, [(g33[0], g33[1]), (g33[0], 85.5)], W_PWR, F, "GND")
    add_via(board, g33[0], 85.5, "GND")

    # ------------------------------------------------------------------
    # 4) 0 Ω bridge VSYS ↔ 3V3 (explicit jumper — not silent net merge)
    #    Place R_VSYS 0603 between (107.5,104.4) VSYS and (107.5,103.2) 3V3
    # ------------------------------------------------------------------
    # Load 0603 footprint from system lib
    io = pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    # Prefer FootprintLoad
    try:
        rfp = pcbnew.FootprintLoad(
            str(Path("/usr/share/kicad/footprints/Resistor_SMD.pretty")),
            "R_0603_1608Metric",
        )
    except Exception:
        rfp = None
    if rfp is not None:
        rfp.SetReference("R_VSYS")
        rfp.SetValue("0R")
        rfp.SetPosition(pcbnew.VECTOR2I(mm(107.5), mm(103.8)))
        # pads along Y: orient 90°
        rfp.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
        board.Add(rfp)
        # Assign nets to pads after place — pad1 toward VSYS (south), pad2 3V3
        pads = list(rfp.Pads())
        # After 90° rot, determine which pad is higher Y
        pads_sorted = sorted(pads, key=lambda p: p.GetPosition().y)
        pads_sorted[0].SetNetCode(netcode(board, "3V3"))  # lower Y ~103.2
        pads_sorted[1].SetNetCode(netcode(board, "VSYS"))  # higher Y ~104.4
        # Ensure tracks hit pads
        p3 = pads_sorted[0].GetPosition()
        pv = pads_sorted[1].GetPosition()
        add_track(
            board,
            107.5,
            104.4,
            pcbnew.ToMM(pv.x),
            pcbnew.ToMM(pv.y),
            W_PWR,
            F,
            "VSYS",
        )
        add_track(
            board,
            pcbnew.ToMM(p3.x),
            pcbnew.ToMM(p3.y),
            106.0,
            103.35,
            W_PWR,
            F,
            "3V3",
        )
        print("placed R_VSYS 0Ω")
    else:
        # Fallback: direct short track (document as intentional proto bridge)
        poly_track(board, [(107.5, 104.4), (107.5, 103.35), (106.0, 103.35)], W_PWR, F, "VSYS")
        print("WARN: no 0603 lib — temporary VSYS track only; add 0R manually")

    # ------------------------------------------------------------------
    # 5) SWD: finish stubs from U1 → SW_DBG / J_SWD bus (gating preserved)
    # ------------------------------------------------------------------
    # Existing stubs end at x=88; bus at x=86.54 / 89.08 / 91.62
    poly_track(
        board,
        [(88.0, 95.35), (86.54, 95.35), (86.54, 100.25)],
        W_SIG,
        F,
        "SWDIO",
    )
    poly_track(
        board,
        [(88.0, 96.15), (89.08, 96.15), (89.08, 100.75)],
        W_SIG,
        F,
        "SWDCLK",
    )
    # nRESET stub at y=90.15 → go west then south to bus x=91.62
    poly_track(
        board,
        [(88.0, 90.15), (91.62, 90.15), (91.62, 101.25)],
        W_SIG,
        F,
        "nRESET",
    )
    # R1 pull-up already on nRESET at (94.8,94.99) — stitch from stub
    poly_track(board, [(94.8, 94.99), (94.8, 90.15), (91.62, 90.15)], W_SIG, F, "nRESET")

    # ------------------------------------------------------------------
    # 6) Buttons U1 → existing stubs → SW*
    # ------------------------------------------------------------------
    b1p = pad_xy(board, "U1", "61")  # BTN1
    b2p = pad_xy(board, "U1", "50")
    b3p = pad_xy(board, "U1", "60")
    # Escape south between module and SW_DBG/pogo — corridor y=100..103.6 x=98..102
    poly_track(
        board,
        [(b1p[0], b1p[1]), (b1p[0], 100.5), (101.75, 100.5), (101.75, 103.6)],
        W_SIG,
        F,
        "BTN1",
    )
    poly_track(
        board,
        [(b2p[0], b2p[1]), (b2p[0], 99.5), (102.25, 99.5), (102.25, 103.6)],
        W_SIG,
        F,
        "BTN2",
    )
    poly_track(
        board,
        [(b3p[0], b3p[1]), (b3p[0], 101.0), (102.75, 101.0), (102.75, 103.6)],
        W_SIG,
        F,
        "BTN3",
    )
    # Finish BTN3 to SW3.1
    poly_track(board, [(108.4, 105.5), (111.8, 105.5)], W_SIG, F, "BTN3")

    # ------------------------------------------------------------------
    # 7) SPI fanout U1 → J_DISP_MAIN stubs (north edge) + B.Cu star to L/R
    # ------------------------------------------------------------------
    # Helper pad positions
    sck = pad_xy(board, "U1", "9")
    mosi = pad_xy(board, "U1", "20")
    dc = pad_xy(board, "U1", "19")
    rst = pad_xy(board, "U1", "16")
    csm = pad_xy(board, "U1", "22")
    csl = pad_xy(board, "U1", "23")
    csr = pad_xy(board, "U1", "24")
    bsym = pad_xy(board, "U1", "13")
    bsyl = pad_xy(board, "U1", "10")
    bsyr = pad_xy(board, "U1", "14")

    # --- Main FPC short escapes to y=85.2 bus ---
    # MOSI pad → (101.6,85.2) → existing (98.0,85.2)
    poly_track(board, [(mosi[0], mosi[1]), (mosi[0], 85.2), (98.0, 85.2)], W_SIG, F, "EPD_MOSI")
    # CS_MAIN
    poly_track(board, [(csm[0], csm[1]), (csm[0], 85.2), (101.0, 85.2)], W_SIG, F, "EPD_CS_MAIN")
    # CS_R (also needed on right strap — branch later)
    poly_track(board, [(csr[0], csr[1]), (csr[0], 85.0), (csr[0], 85.0)], W_SIG, F, "EPD_CS_R")
    # DC from pad@87.25
    poly_track(board, [(dc[0], dc[1]), (dc[0], 85.2), (100.25, 85.2)], W_SIG, F, "EPD_DC")
    # RST
    poly_track(board, [(rst[0], rst[1]), (rst[0], 85.2), (100.75, 85.2)], W_SIG, F, "EPD_RST")
    # SCK: pad on east side — escape east then north to via@97,85.2 area
    poly_track(
        board,
        [(sck[0], sck[1]), (105.5, sck[1]), (105.5, 85.2), (99.25, 85.2)],
        W_SIG,
        F,
        "EPD_SCK",
    )
    # BUSY_MAIN
    poly_track(
        board,
        [(bsym[0], bsym[1]), (105.8, bsym[1]), (105.8, 85.2), (102.0, 85.2)],
        W_SIG,
        F,
        "EPD_BUSY_MAIN",
    )

    # --- B.Cu bridges between Main ↔ L ↔ R vias for shared SPI ---
    # EPD_SCK vias: (97,85.2), (84.35,96.8), (115.65,96.8)
    poly_track(
        board,
        [(97.0, 85.2), (97.0, 96.8), (84.35, 96.8)],
        W_SIG,
        B,
        "EPD_SCK",
    )
    poly_track(
        board,
        [(97.0, 96.8), (115.65, 96.8)],
        W_SIG,
        B,
        "EPD_SCK",
    )
    # EPD_MOSI: (98,85.2), (85.35,97.8), (114.65,97.8)
    poly_track(board, [(98.0, 85.2), (98.0, 97.8), (85.35, 97.8)], W_SIG, B, "EPD_MOSI")
    poly_track(board, [(98.0, 97.8), (114.65, 97.8)], W_SIG, B, "EPD_MOSI")
    # EPD_DC
    poly_track(board, [(99.0, 85.2), (99.0, 98.8), (86.35, 98.8)], W_SIG, B, "EPD_DC")
    poly_track(board, [(99.0, 98.8), (113.65, 98.8)], W_SIG, B, "EPD_DC")
    # EPD_RST
    poly_track(board, [(100.0, 85.2), (100.0, 99.8), (87.35, 99.8)], W_SIG, B, "EPD_RST")
    poly_track(board, [(100.0, 99.8), (112.65, 99.8)], W_SIG, B, "EPD_RST")

    # --- CS_L / BUSY_L from U1 east/north to left stubs ---
    # CS_L pad (100.4,87.25) → west on B.Cu to (91.2,96.75)
    add_via(board, 100.4, 88.5, "EPD_CS_L")
    poly_track(board, [(csl[0], csl[1]), (csl[0], 88.5)], W_SIG, F, "EPD_CS_L")
    poly_track(board, [(100.4, 88.5), (91.2, 88.5), (91.2, 96.75)], W_SIG, B, "EPD_CS_L")
    add_via(board, 91.2, 96.75, "EPD_CS_L")

    # CS_R pad (100,86.35) → east to (108.8,99.75)
    add_via(board, 100.0, 88.0, "EPD_CS_R")
    poly_track(board, [(csr[0], csr[1]), (csr[0], 88.0)], W_SIG, F, "EPD_CS_R")
    poly_track(board, [(100.0, 88.0), (108.8, 88.0), (108.8, 99.75)], W_SIG, B, "EPD_CS_R")
    add_via(board, 108.8, 99.75, "EPD_CS_R")

    # BUSY_L (104.65,91.35) → left stub (90.2,97.25)
    add_via(board, 106.0, 91.35, "EPD_BUSY_L")
    poly_track(board, [(bsyl[0], bsyl[1]), (106.0, bsyl[1])], W_SIG, F, "EPD_BUSY_L")
    poly_track(board, [(106.0, 91.35), (106.0, 97.25), (90.2, 97.25)], W_SIG, B, "EPD_BUSY_L")
    add_via(board, 90.2, 97.25, "EPD_BUSY_L")

    # BUSY_R (104.65,89.75) → (109.8,99.25)
    add_via(board, 106.3, 89.75, "EPD_BUSY_R")
    poly_track(board, [(bsyr[0], bsyr[1]), (106.3, bsyr[1])], W_SIG, F, "EPD_BUSY_R")
    poly_track(board, [(106.3, 89.75), (106.3, 99.25), (109.8, 99.25)], W_SIG, B, "EPD_BUSY_R")
    add_via(board, 109.8, 99.25, "EPD_BUSY_R")

    # R2 is pull-up on EPD_CS_MAIN — connect pad2 if dangling
    poly_track(board, [(105.2, 94.99), (105.2, 90.0), (100.8, 90.0), (100.8, 86.35)], W_SIG, F, "EPD_CS_MAIN")

    # ------------------------------------------------------------------
    # 8) I2C U1 → U2 (east then south along module, Signal 0.18)
    # ------------------------------------------------------------------
    sda_u1, scl_u1, int_u1 = pad_xy(board, "U1", "27"), pad_xy(board, "U1", "29"), pad_xy(board, "U1", "39")
    sda_u2, scl_u2, int_u2 = pad_xy(board, "U2", "E4"), pad_xy(board, "U2", "E5"), pad_xy(board, "U2", "D2")

    # Escape SDA/SCL south from north-edge pads then east on B.Cu under module skirt
    add_via(board, 98.8, 88.8, "SDA")
    poly_track(board, [(sda_u1[0], sda_u1[1]), (sda_u1[0], 88.8)], W_SIG, F, "SDA")
    add_via(board, 98.0, 89.2, "SCL")
    poly_track(board, [(scl_u1[0], scl_u1[1]), (scl_u1[0], 89.2)], W_SIG, F, "SCL")

    # B.Cu east to x=109 then south to U2
    poly_track(
        board,
        [(98.8, 88.8), (109.2, 88.8), (109.2, 106.8), (sda_u2[0], 106.8), (sda_u2[0], sda_u2[1])],
        W_SIG,
        B,
        "SDA",
    )
    add_via(board, sda_u2[0], 106.8, "SDA")
    poly_track(
        board,
        [(98.0, 89.2), (109.8, 89.2), (109.8, 107.2), (scl_u2[0], 107.2), (scl_u2[0], scl_u2[1])],
        W_SIG,
        B,
        "SCL",
    )
    add_via(board, scl_u2[0], 107.2, "SCL")

    # PMIC_INT from left side pad 39 → B.Cu around south
    add_via(board, 94.2, 89.75, "PMIC_INT")
    poly_track(board, [(int_u1[0], int_u1[1]), (94.2, int_u1[1])], W_SIG, F, "PMIC_INT")
    poly_track(
        board,
        [(94.2, 89.75), (94.2, 107.5), (110.6, 107.5), (110.6, int_u2[1]), (int_u2[0], int_u2[1])],
        W_SIG,
        B,
        "PMIC_INT",
    )
    add_via(board, 110.6, int_u2[1], "PMIC_INT")

    # ------------------------------------------------------------------
    # 9) B.Cu GND zone (circular watch) — stitches dangling GND vias
    # ------------------------------------------------------------------
    # Remove old if any B.Cu GND — none currently
    zone = pcbnew.ZONE(board)
    zone.SetNetCode(netcode(board, "GND"))
    zone.SetLayer(B)
    zone.SetLocalClearance(mm(0.20))
    zone.SetMinThickness(mm(0.15))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    # Circular outline approx as 32-gon
    import math

    chain = zone.Outline().NewOutline()
    n = 48
    for i in range(n):
        ang = 2 * math.pi * i / n
        x = CX + (R - 0.6) * math.cos(ang)
        y = CY + (R - 0.6) * math.sin(ang)
        zone.Outline().Append(mm(x), mm(y))
    board.Add(zone)

    # RF keepout: rule-area if API allows; else documented in FANOUT_PASS.md
    try:
        ko = pcbnew.ZONE(board)
        ko.SetIsRuleArea(True)
        if hasattr(ko, "SetDoNotAllowCopperPour"):
            ko.SetDoNotAllowCopperPour(True)
        elif hasattr(ko, "SetDoNotAllowZones"):
            ko.SetDoNotAllowZones(True)
        ko.SetLayerSet(pcbnew.LSET(B))
        for x, y in [(94, 80), (106, 80), (106, 86), (94, 86)]:
            ko.Outline().Append(mm(x), mm(y))
        board.Add(ko)
        print("added RF keepout rule area")
    except Exception as e:
        print("RF keepout skipped:", e)

    # IP67 / seal land note on Dwgs.User (no geometric seal land present)
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText(
        "IP67: no seal-land copper ring on PCB — "
        "gasket keepout is mechanical (case); keep pogo 2x3@3mm clear of seal boss"
    )
    txt.SetPosition(pcbnew.VECTOR2I(mm(100), mm(121)))
    txt.SetLayer(pcbnew.Dwgs_User)
    txt.SetTextSize(pcbnew.VECTOR2I(mm(0.7), mm(0.7)))
    txt.SetTextThickness(mm(0.1))
    board.Add(txt)

    # Antenna RF keepout silk note
    txt2 = pcbnew.PCB_TEXT(board)
    txt2.SetText("RF KEEPOUT: MDBT50Q antenna (top) — no battery/metal under")
    txt2.SetPosition(pcbnew.VECTOR2I(mm(100), mm(79.5)))
    txt2.SetLayer(pcbnew.F_SilkS)
    txt2.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
    txt2.SetTextThickness(mm(0.08))
    board.Add(txt2)

    # ------------------------------------------------------------------
    # 10) Refill zones + save
    # ------------------------------------------------------------------
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(PCB), board)
    print(f"saved {PCB}")
    print(f"backup {BACKUP}")


if __name__ == "__main__":
    main()
