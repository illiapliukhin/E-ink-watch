#!/usr/bin/env python3
"""Repair unconnected nets after short/cross cleanup — prefer B.Cu, avoid F crossings."""
from __future__ import annotations

import math
from pathlib import Path

import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
W_SIG, W_PWR, W_FAT, W_NECK = 0.18, 0.45, 0.50, 0.20
VIA_D, VIA_DRILL = 0.60, 0.30
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)


def mm(v):
    return pcbnew.FromMM(v)


def netcode(board, name):
    return board.GetNetInfo().GetNetItem(name).GetNetCode()


def find_fp(board, ref):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    raise KeyError(ref)


def pad_xy(board, ref, num):
    for p in find_fp(board, ref).Pads():
        if p.GetNumber() == str(num):
            return pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
    raise KeyError(f"{ref}.{num}")


def pad_by_net(board, ref, net):
    for p in find_fp(board, ref).Pads():
        if p.GetNetname() == net:
            return pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), p.GetNumber()
    raise KeyError(f"{ref}:{net}")


def add_track(board, x1, y1, x2, y2, w, layer, net):
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w))
    t.SetLayer(layer)
    t.SetNetCode(netcode(board, net))
    board.Add(t)


def poly(board, pts, w, layer, net):
    for a, b in zip(pts, pts[1:]):
        add_track(board, a[0], a[1], b[0], b[1], w, layer, net)


def in_seal(x, y):
    return POGO["xmin"] <= x <= POGO["xmax"] and POGO["ymin"] <= y <= POGO["ymax"]


def add_via(board, x, y, net):
    if in_seal(x, y):
        print(f"  skip via seal ({x},{y}) {net}")
        return None
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    try:
        v.SetWidth(pcbnew.F_Cu, mm(VIA_D))
    except Exception:
        pass
    v.SetDrill(mm(VIA_DRILL))
    v.SetNetCode(netcode(board, net))
    board.Add(v)
    return v


def main():
    board = pcbnew.LoadBoard(str(PCB))
    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    # ----- PMID: C_PMID pad1 to A3 -----
    a3 = pad_xy(board, "U2", "A3")
    cpmid1 = pad_xy(board, "C_PMID", "1")
    poly(board, [cpmid1, (a3[0], cpmid1[1]), a3], 0.30, F, "PMID")

    # ----- VBUS continuous TP1→corridor→A2 + C_IN -----
    a2 = pad_xy(board, "U2", "A2")
    cin1 = pad_xy(board, "C_IN", "1")
    # Ensure single clear path
    poly(
        board,
        [(93.0, 114.0), (93.0, 112.2), (110.6, 112.2), (110.6, 105.2), a2],
        W_FAT,
        F,
        "VBUS",
    )
    poly(board, [cin1, (cin1[0], a2[1]), a2], 0.35, F, "VBUS")

    # ----- VBAT continuous -----
    b1 = pad_xy(board, "U2", "B1")
    cbat1 = pad_xy(board, "C_BAT", "1")
    poly(board, [b1, (b1[0], 107.9)], W_FAT, F, "VBAT")
    poly(board, [(b1[0], 107.9), (100.0, 107.9), (100.0, 115.8)], W_FAT, F, "VBAT")
    poly(board, [cbat1, b1], 0.35, F, "VBAT")
    # J_BAT pad1
    try:
        jbat = pad_xy(board, "J_BAT", "1")
        poly(board, [(100.0, 115.8), jbat], W_FAT, F, "VBAT")
    except Exception:
        pass

    # ----- VSYS already short; ensure C_SYS/C_VINLS -----
    b5 = pad_xy(board, "U2", "B5")
    c4 = pad_xy(board, "U2", "C4")
    for ref in ("C_SYS", "C_VINLS"):
        fp = find_fp(board, ref)
        for p in fp.Pads():
            if p.GetNetname() == "VSYS":
                xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                tgt = b5 if ref == "C_SYS" else c4
                poly(board, [xy, tgt], 0.30, F, "VSYS")

    # ----- 3V3: reconnect escapes without pad-row short -----
    p28 = pad_xy(board, "U1", "28")
    p30 = pad_xy(board, "U1", "30")
    poly(board, [p30, p28], W_NECK + 0.05, F, "3V3")
    # west escape via at (97, 87.5)
    poly(board, [p30, (97.0, p30[1]), (97.0, 87.5)], 0.30, F, "3V3")
    add_via(board, 97.0, 87.5, "3V3")
    # B spine west-south to (94.9, 101.95) area and R_VSYS
    poly(
        board,
        [(97.0, 87.5), (93.5, 87.5), (93.5, 98.5), (94.9, 98.5), (94.9, 101.95)],
        W_PWR,
        B,
        "3V3",
    )
    add_via(board, 94.9, 101.95, "3V3")
    # east via at (106, 87.5) — drop vertically from p28 then east on y=87.5 NOT 86.35
    poly(board, [p28, (p28[0], 87.5), (106.0, 87.5)], 0.30, F, "3V3")
    add_via(board, 106.0, 87.5, "3V3")
    poly(board, [(106.0, 87.5), (106.0, 96.01)], W_PWR, B, "3V3")
    add_via(board, 106.0, 96.01, "3V3")
    # to R2 / R_VSYS 3V3 side
    rvsys3 = pad_xy(board, "R_VSYS", "2")
    poly(board, [(106.0, 96.01), (106.0, 103.35), (rvsys3[0], 103.35), rvsys3], W_PWR, F, "3V3")
    # pull-ups
    for ref in ("R_SDA", "R_SCL"):
        p = pad_xy(board, ref, "2")
        poly(board, [p, (p[0], 103.35), (107.5, 103.35)], 0.25, F, "3V3")
    # link R_SDA.2 and R_SCL.2
    poly(
        board,
        [pad_xy(board, "R_SDA", "2"), pad_xy(board, "R_SCL", "2")],
        0.25,
        F,
        "3V3",
    )
    # J_SWD 3V3 via B
    try:
        # find 3V3 pad on J_SWD
        for p in find_fp(board, "J_SWD").Pads():
            if p.GetNetname() == "3V3":
                jx, jy = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
                add_via(board, 94.9, 108.0, "3V3")
                poly(board, [(94.9, 101.95), (94.9, 108.0)], W_PWR, B, "3V3")
                poly(board, [(94.9, 108.0), (jx, 108.0), (jx, jy)], W_PWR, F, "3V3")
                break
    except Exception as e:
        print("J_SWD 3V3", e)

    # ----- 3V3_DISP: C5 → via → B spine → FPC vias -----
    c5 = pad_xy(board, "U2", "C5")
    cldo = None
    for p in find_fp(board, "C_LDO").Pads():
        if p.GetNetname() == "3V3_DISP":
            cldo = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
    poly(board, [c5, (113.0, c5[1])], W_PWR, F, "3V3_DISP")
    if cldo:
        poly(board, [cldo, (113.0, cldo[1]), (113.0, c5[1])], 0.30, F, "3V3_DISP")
    add_via(board, 113.0, c5[1], "3V3_DISP")
    # B.Cu backbone
    poly(
        board,
        [
            (113.0, c5[1]),
            (104.0, 105.2),
            (96.0, 105.2),
            (92.0, 105.2),
            (92.0, 87.0),
            (94.0, 87.0),
        ],
        W_PWR,
        B,
        "3V3_DISP",
    )
    add_via(board, 94.0, 87.0, "3V3_DISP")
    add_via(board, 92.0, 105.2, "3V3_DISP")
    add_via(board, 104.0, 105.2, "3V3_DISP")
    # Left FPC 3V3_DISP
    poly(board, [(92.0, 105.2), (84.45, 105.5), (84.45, 108.5)], W_PWR, B, "3V3_DISP")
    add_via(board, 84.45, 108.5, "3V3_DISP")
    # to J_STRAP_L pad 10
    try:
        jl = pad_xy(board, "J_STRAP_L", "10")
        poly(board, [(84.45, 108.5), (jl[0], 108.5), jl], W_PWR, F, "3V3_DISP")
        # also pad at 102.75 / 98.25 area
        for p in find_fp(board, "J_STRAP_L").Pads():
            if p.GetNetname() == "3V3_DISP":
                xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                poly(board, [(84.45, xy[1]), xy], W_PWR, F, "3V3_DISP")
    except Exception as e:
        print("strap L", e)
    # Right FPC
    poly(board, [(113.0, c5[1]), (115.55, c5[1]), (115.55, 102.75)], W_PWR, B, "3V3_DISP")
    add_via(board, 115.55, 102.75, "3V3_DISP")
    for p in find_fp(board, "J_STRAP_R").Pads():
        if p.GetNetname() == "3V3_DISP":
            xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            poly(board, [(115.55, 102.75), (115.55, xy[1]), xy], W_PWR, F, "3V3_DISP")
    # Main display
    poly(board, [(94.0, 87.0), (94.0, 82.4), (97.75, 82.4)], W_PWR, F, "3V3_DISP")
    for p in find_fp(board, "J_DISP_MAIN").Pads():
        if p.GetNetname() == "3V3_DISP":
            xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            poly(board, [(97.75, 82.4), (xy[0], 82.4), xy], W_PWR, F, "3V3_DISP")

    # ----- GND: stitch U2 + SW3 + caps to vias/zones -----
    a1 = pad_xy(board, "U2", "A1")
    a5 = pad_xy(board, "U2", "A5")
    d5 = pad_xy(board, "U2", "D5")
    poly(board, [a1, a5, d5], W_NECK, F, "GND")
    add_via(board, 109.2, 104.5, "GND")
    poly(board, [a1, (109.2, a1[1]), (109.2, 104.5)], 0.35, F, "GND")
    # C_IN/C_BAT GND pads
    for ref in ("C_IN", "C_BAT", "C_PMID"):
        p = pad_xy(board, ref, "2")
        poly(board, [p, (109.2, p[1]), (109.2, 104.5)], 0.30, F, "GND")
    # C_SYS/C_VINLS/C_LDO GND
    for ref in ("C_SYS", "C_VINLS", "C_LDO"):
        for p in find_fp(board, ref).Pads():
            if p.GetNetname() == "GND":
                xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                poly(board, [xy, a5], 0.30, F, "GND")
    # SW3 GND to via east
    sw3g = pad_xy(board, "SW3", "2")
    add_via(board, 117.2, 108.0, "GND")
    poly(board, [sw3g, (117.2, sw3g[1]), (117.2, 108.0)], 0.35, F, "GND")
    # C4 GND
    c4g = pad_xy(board, "C4", "2")
    add_via(board, c4g[0], c4g[1] + 0.8, "GND")
    poly(board, [c4g, (c4g[0], c4g[1] + 0.8)], 0.35, F, "GND")

    # ----- SWD U1 → SW_DBG -----
    # pads
    swdio_u = pad_by_net(board, "U1", "SWDIO")
    swdclk_u = pad_by_net(board, "U1", "SWDCLK")
    nreset_u = pad_by_net(board, "U1", "nRESET")
    swdio_d = pad_xy(board, "SW_DBG", "1")
    swdclk_d = pad_xy(board, "SW_DBG", "2")
    nreset_d = pad_xy(board, "SW_DBG", "3")
    # route west on F then south — stay clear of module
    def route_swd(net, src, dst, x_corridor):
        poly(
            board,
            [
                (src[0], src[1]),
                (x_corridor, src[1]),
                (x_corridor, dst[1]),
                dst,
            ],
            W_SIG,
            F,
            net,
        )

    route_swd("SWDIO", swdio_u, swdio_d, 88.0)
    route_swd("SWDCLK", swdclk_u, swdclk_d, 88.5)
    route_swd("nRESET", nreset_u, nreset_d, 89.0)

    # POGO side of SW_DBG → TP (F.Cu only, no new vias in seal)
    # SW_DBG pads 6/5/4 = SWDIO_POGO / SWDCLK_POGO / nRESET_POGO
    pogo_map = [
        ("SWDIO_POGO", "6", (99.0, 114.0)),
        ("SWDCLK_POGO", "5", (93.0, 111.0)),
        ("nRESET_POGO", "4", (96.0, 111.0)),
    ]
    for net, padn, tp in pogo_map:
        src = pad_xy(board, "SW_DBG", padn)
        # route east then south outside seal, enter seal only as track to pad
        mid_y = 108.0  # just above seal
        poly(
            board,
            [src, (src[0] + 2.0, src[1]), (tp[0], mid_y), tp],
            W_SIG,
            F,
            net,
        )

    # ----- I2C: U1 → B.Cu east → U2 + pullups already -----
    sda_u = pad_xy(board, "U1", "27")
    scl_u = pad_xy(board, "U1", "29")
    sda_p = pad_xy(board, "U2", "E4")
    scl_p = pad_xy(board, "U2", "E5")
    int_p = pad_xy(board, "U2", "D2")
    # find INT pad on U1
    try:
        int_u = pad_by_net(board, "U1", "PMIC_INT")
    except KeyError:
        int_u = None

    add_via(board, sda_u[0] + 0.6, sda_u[1] + 0.8, "SDA")
    poly(board, [sda_u, (sda_u[0] + 0.6, sda_u[1]), (sda_u[0] + 0.6, sda_u[1] + 0.8)], W_SIG, F, "SDA")
    poly(
        board,
        [
            (sda_u[0] + 0.6, sda_u[1] + 0.8),
            (109.2, sda_u[1] + 0.8),
            (109.2, 107.0),
            (sda_p[0], 107.0),
        ],
        W_SIG,
        B,
        "SDA",
    )
    add_via(board, sda_p[0], 107.0, "SDA")
    poly(board, [(sda_p[0], 107.0), sda_p], W_SIG, F, "SDA")
    # pullup already connected

    add_via(board, scl_u[0] + 0.6, scl_u[1] + 0.8, "SCL")
    poly(board, [scl_u, (scl_u[0] + 0.6, scl_u[1]), (scl_u[0] + 0.6, scl_u[1] + 0.8)], W_SIG, F, "SCL")
    poly(
        board,
        [
            (scl_u[0] + 0.6, scl_u[1] + 0.8),
            (109.8, scl_u[1] + 0.8),
            (109.8, 107.2),
            (scl_p[0], 107.2),
        ],
        W_SIG,
        B,
        "SCL",
    )
    add_via(board, scl_p[0], 107.2, "SCL")
    poly(board, [(scl_p[0], 107.2), scl_p], W_SIG, F, "SCL")

    if int_u:
        add_via(board, int_u[0] - 0.5, int_u[1] + 0.8, "PMIC_INT")
        poly(
            board,
            [ (int_u[0], int_u[1]), (int_u[0] - 0.5, int_u[1]), (int_u[0] - 0.5, int_u[1] + 0.8) ],
            W_SIG,
            F,
            "PMIC_INT",
        )
        poly(
            board,
            [
                (int_u[0] - 0.5, int_u[1] + 0.8),
                (94.2, int_u[1] + 0.8),
                (94.2, 106.4),
                (int_p[0], 106.4),
            ],
            W_SIG,
            B,
            "PMIC_INT",
        )
        add_via(board, int_p[0], 106.4, "PMIC_INT")
        poly(board, [(int_p[0], 106.4), int_p], W_SIG, F, "PMIC_INT")

    # ----- SPI shared: ensure U1 pad → local via → B star → FPC vias -----
    spi = [
        ("EPD_SCK", "9", 105.5, 91.75),
        ("EPD_MOSI", "20", 106.5, 91.0),
        ("EPD_DC", "19", 102.0, 87.25),
        ("EPD_RST", "16", 104.0, 86.35),
    ]
    # Via farm positions (existing-ish)
    farm = {
        "EPD_SCK": [(105.5, 91.75), (97.0, 85.2), (115.0, 96.5), (85.0, 96.5)],
        "EPD_MOSI": [(106.5, 91.0), (98.0, 85.2), (114.5, 97.5), (86.0, 97.5)],
        "EPD_DC": [(102.0, 88.5), (99.0, 85.2), (113.5, 98.5), (86.5, 98.5)],
        "EPD_RST": [(104.0, 87.5), (100.0, 85.2), (112.5, 99.5), (87.5, 99.5)],
    }
    for net, pnum, *_ in spi:
        try:
            src = pad_xy(board, "U1", pnum)
        except KeyError:
            src = pad_by_net(board, "U1", net)[:2]
        vias = farm[net]
        # F escape to first via
        poly(board, [src, vias[0]], W_SIG, F, net)
        add_via(board, vias[0][0], vias[0][1], net)
        # B star
        for v in vias[1:]:
            add_via(board, v[0], v[1], net)
            poly(board, [vias[0], v], W_SIG, B, net)

    # CS/BUSY singles
    singles = [
        ("EPD_CS_MAIN", None, (101.0, 85.2)),
        ("EPD_BUSY_MAIN", "13", (105.8, 90.15)),
        ("EPD_CS_L", "23", (91.2, 88.5)),
        ("EPD_CS_R", "24", (108.8, 88.0)),
        ("EPD_BUSY_L", None, (90.2, 97.25)),
        ("EPD_BUSY_R", "14", (109.8, 99.25)),
    ]
    for net, pnum, via_pt in singles:
        try:
            if pnum:
                src = pad_xy(board, "U1", pnum)
            else:
                src = pad_by_net(board, "U1", net)[:2]
        except Exception as e:
            print("single", net, e)
            continue
        add_via(board, via_pt[0], via_pt[1], net)
        poly(board, [src, via_pt], W_SIG, F, net)
        # try connect toward matching connector pad on B then F
        # search connector pad
        for jref in ("J_DISP_MAIN", "J_STRAP_L", "J_STRAP_R"):
            for p in find_fp(board, jref).Pads():
                if p.GetNetname() == net:
                    xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                    # B run then via near connector
                    mid = ((via_pt[0] + xy[0]) / 2, (via_pt[1] + xy[1]) / 2)
                    # keep mid outside dense areas
                    poly(board, [via_pt, (xy[0], via_pt[1]), (xy[0], xy[1] + (0.8 if xy[1] < via_pt[1] else -0.8))], W_SIG, B, net)
                    vx, vy = xy[0], xy[1] + (0.8 if xy[1] < 100 else -0.8)
                    if not in_seal(vx, vy):
                        add_via(board, vx, vy, net)
                        poly(board, [(vx, vy), xy], W_SIG, F, net)

    # ----- BTN already routed in previous pass; verify/fix -----
    for net, sw in (("BTN1", "SW1"), ("BTN2", "SW2"), ("BTN3", "SW3")):
        try:
            src = pad_by_net(board, "U1", net)
            dst = pad_xy(board, sw, "1")
        except Exception as e:
            print("btn", net, e)
            continue
        # B corridor south
        vx, vy = src[0] + (0.8 if net != "BTN2" else -0.8), src[1] + 1.0
        add_via(board, vx, vy, net)
        poly(board, [(src[0], src[1]), (vx, src[1]), (vx, vy)], W_SIG, F, net)
        poly(board, [(vx, vy), (vx, 110.8), (dst[0], 110.8)], W_SIG, B, net)
        add_via(board, dst[0], 110.8, net)
        poly(board, [(dst[0], 110.8), dst], W_SIG, F, net)

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(PCB), board)
    print("repair saved")


if __name__ == "__main__":
    main()
