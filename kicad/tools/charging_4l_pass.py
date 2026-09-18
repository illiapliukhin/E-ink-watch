#!/usr/bin/env python3
"""4L charging integrity + BQ25120A JEITA/TVS/buck passives.

Charge path (must not involve SW_DBG):
  TP1(VBUS) → U2.A2(IN) ; TP2(GND) → GND plane
  U2.B1/B2(BAT) → J_BAT ; U2.B5(SYS) → R_VSYS → 3V3 (In2 plane)
SW_DBG only gates SWDIO/SWDCLK/nRESET — VBUS/GND bypass DIP.

YFP0025 ball map (TI DS / EVM):
  A2 IN, A3/B3 PMID, A4 SW, B1/B2 BAT, B5 SYS, B4/C4 VINLS,
  C1 ISET, C2 ILIM, C3 TS, C5 LS/LDO, D1 IPRETERM, D2 INT,
  E2 /CD, E3 LSCTRL, E4 SDA, E5 SCL
"""
from __future__ import annotations

import math
import os
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


def ensure_net(board, name):
    ni = board.GetNetInfo().GetNetItem(name)
    if ni is not None:
        return ni.GetNetCode()
    new = pcbnew.NETINFO_ITEM(board, name)
    board.Add(new)
    return new.GetNetCode()


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


def set_pad_net(board, ref, num, net):
    code = ensure_net(board, net)
    for p in find_fp(board, ref).Pads():
        if p.GetNumber() == str(num):
            p.SetNetCode(code)
            return
    raise KeyError(f"{ref}.{num}")


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
        print(f"  SKIP via seal ({x:.2f},{y:.2f}) {net}")
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


def load_fp(board, lib, name, ref, value, x, y, rot=0):
    try:
        find_fp(board, ref)
        print("exists", ref)
        return find_fp(board, ref)
    except KeyError:
        pass
    libpath = f"/usr/share/kicad/footprints/{lib}.pretty"
    fp = pcbnew.FootprintLoad(libpath, name)
    if fp is None:
        raise RuntimeError(f"load {lib}:{name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    board.Add(fp)
    print(f"placed {ref}={value} @ ({x},{y})")
    return fp


def wire(board, fp, n1, n2):
    for p in fp.Pads():
        if p.GetNumber() == "1":
            p.SetNetCode(netcode(board, n1))
        elif p.GetNumber() == "2":
            p.SetNetCode(netcode(board, n2))


def endpoints(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return [(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))]
    a, b = t.GetStart(), t.GetEnd()
    return [(pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)), (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))]


def orient(p, q, r):
    return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])


def crosses(a, b, c, d):
    return orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    IN1, IN2 = pcbnew.In1_Cu, pcbnew.In2_Cu

    # --- Correct ball nets for charging ---
    ensure_net(board, "PMID")
    ensure_net(board, "VINLS")
    ensure_net(board, "TS")
    ensure_net(board, "CD")
    ensure_net(board, "SW")
    ensure_net(board, "ISET")
    ensure_net(board, "ILIM")
    ensure_net(board, "IPRETERM")
    ensure_net(board, "LSCTRL")

    set_pad_net(board, "U2", "A2", "VBUS")  # IN
    set_pad_net(board, "U2", "A3", "PMID")
    set_pad_net(board, "U2", "B3", "PMID")
    set_pad_net(board, "U2", "A4", "SW")
    set_pad_net(board, "U2", "B1", "VBAT")
    set_pad_net(board, "U2", "B2", "VBAT")
    set_pad_net(board, "U2", "B5", "VSYS")  # SYS
    # VINLS fed from PMID (wearable LDO from PMID) — not silent merge with SYS
    set_pad_net(board, "U2", "B4", "VINLS")
    set_pad_net(board, "U2", "C4", "VINLS")
    set_pad_net(board, "U2", "C1", "ISET")
    set_pad_net(board, "U2", "C2", "ILIM")
    set_pad_net(board, "U2", "C3", "TS")
    set_pad_net(board, "U2", "C5", "3V3_DISP")  # LS/LDO
    set_pad_net(board, "U2", "D1", "IPRETERM")
    set_pad_net(board, "U2", "E2", "CD")
    set_pad_net(board, "U2", "E3", "LSCTRL")

    # --- Place charging passives near U2 / pogo ---
    # TVS on VBUS near TP1 but OUTSIDE seal land (x<90.5 or y<108.5)
    tvs = load_fp(board, "Diode_SMD", "D_SOD-323", "D_TVS_VBUS", "PESD5V0S1U", 89.2, 112.5, 0)
    wire(board, tvs, "VBUS", "GND")  # SOD-323: pad1 anode-ish; bidirectional TVS either way OK

    # TS divider: R_TS from VBUS to TS (~5.0k), NTC 10k TS to GND (JEITA)
    rts = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_TS", "5.1k", 108.2, 107.0, 0)
    wire(board, rts, "VBUS", "TS")
    ntc = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "NTC_BAT", "10k_NTC", 108.2, 107.8, 0)
    wire(board, ntc, "TS", "GND")

    # /CD pulldown → charge enable when VIN present (active-low CD)
    rcd = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_CD", "10k", 112.8, 107.9, 90)
    wire(board, rcd, "CD", "GND")

    # ISET ~5.6k → wearable ~25–40 mA class (EVT tune; I2C can override)
    riset = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_ISET", "5.6k", 109.8, 103.5, 0)
    wire(board, riset, "ISET", "GND")

    # ILIM 14k → ~100 mA input limit (EVM-class)
    rilim = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_ILIM", "14k", 110.8, 103.5, 0)
    wire(board, rilim, "ILIM", "GND")

    # IPRETERM 5.1k placeholder (or GND for host-mode)
    rip = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_IPRETERM", "5.1k", 112.0, 103.5, 0)
    wire(board, rip, "IPRETERM", "GND")

    # LSCTRL pull-up to 3V3 → LDO on at default
    rls = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_LSCTRL", "10k", 113.8, 107.9, 90)
    wire(board, rls, "LSCTRL", "3V3")

    # Buck inductor SW → SYS (2.2 µH typical wearable)
    lind = load_fp(board, "Inductor_SMD", "L_0805_2012Metric", "L_SYS", "2.2uH", 114.8, 104.5, 0)
    wire(board, lind, "SW", "VSYS")

    # VINLS tie to PMID (short)
    # PMID already on A3/B3

    # --- Delete 3V3 pad-row short if present ---
    doomed = []
    for t in list(board.GetTracks()):
        if t.GetClass() == "PCB_VIA" or t.GetNetname() != "3V3" or t.GetLayer() != F:
            continue
        (x1, y1), (x2, y2) = endpoints(t)
        if abs(y1 - 86.35) < 0.2 and abs(y2 - 86.35) < 0.2 and max(x1, x2) > 99:
            doomed.append(t)
    for t in doomed:
        board.Delete(t)
    print("deleted 3V3 pad-row", len(doomed))

    # Remove via-in-pad under pogo
    tps = [(93, 114), (96, 114), (99, 114), (93, 111), (96, 111), (99, 111)]
    doomed = []
    for t in list(board.GetTracks()):
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = endpoints(t)[0]
        if any(math.hypot(x - tx, y - ty) < 0.35 for tx, ty in tps):
            doomed.append(t)
    for t in doomed:
        board.Delete(t)
    print("deleted pogo VIP", len(doomed))

    # --- Charge path routing ---
    a2 = pad_xy(board, "U2", "A2")
    # VBUS: TP1 → y=112.2 → A2 (does NOT go through SW_DBG)
    poly(board, [(93.0, 114.0), (93.0, 112.2), (110.6, 112.2), (110.6, a2[1]), a2], W_FAT, F, "VBUS")
    # TVS stubs
    try:
        t1 = pad_xy(board, "D_TVS_VBUS", "1")
        t2 = pad_xy(board, "D_TVS_VBUS", "2")
        poly(board, [t1, (93.0, t1[1]), (93.0, 112.2)], 0.35, F, "VBUS")
        add_via(board, t2[0], t2[1] + 0.6, "GND")
        poly(board, [t2, (t2[0], t2[1] + 0.6)], 0.35, F, "GND")
    except Exception as e:
        print("TVS route", e)
    # C_IN
    try:
        cin = pad_xy(board, "C_IN", "1")
        poly(board, [cin, (cin[0], a2[1]), a2], 0.35, F, "VBUS")
        g = pad_xy(board, "C_IN", "2")
        add_via(board, 109.2, 104.5, "GND")
        poly(board, [g, (109.2, g[1]), (109.2, 104.5)], 0.30, F, "GND")
    except Exception as e:
        print("CIN", e)

    # VBAT
    b1, b2 = pad_xy(board, "U2", "B1"), pad_xy(board, "U2", "B2")
    poly(board, [b1, b2], W_NECK, F, "VBAT")
    poly(board, [b1, (b1[0], 107.9), (100.0, 107.9), (100.0, 115.8)], W_FAT, F, "VBAT")
    try:
        poly(board, [pad_xy(board, "C_BAT", "1"), b1], 0.35, F, "VBAT")
        poly(board, [(100.0, 115.8), pad_xy(board, "J_BAT", "1")], W_FAT, F, "VBAT")
    except Exception as e:
        print("VBAT", e)

    # PMID + VINLS
    a3, b3 = pad_xy(board, "U2", "A3"), pad_xy(board, "U2", "B3")
    poly(board, [a3, b3], W_NECK, F, "PMID")
    b4, c4 = pad_xy(board, "U2", "B4"), pad_xy(board, "U2", "C4")
    poly(board, [b4, c4], W_NECK, F, "VINLS")
    # VINLS ← PMID
    poly(board, [b3, (b3[0], b4[1]), b4], W_NECK, F, "PMID")  # wrong net on last - fix:
    # Actually connect PMID to VINLS with explicit short track on one net? Better: track on PMID to via? 
    # Hardware: wire VINLS pin to PMID copper
    # Put both on same copper by track from b4 to b3 labeled VINLS and also PMID? 
    # Simplest honest approach: assign B4/C4 back to PMID for EVT (VINLS=PMID)
    set_pad_net(board, "U2", "B4", "PMID")
    set_pad_net(board, "U2", "C4", "PMID")
    poly(board, [b3, b4, c4], W_NECK, F, "PMID")
    try:
        poly(board, [pad_xy(board, "C_PMID", "1"), (a3[0], pad_xy(board, "C_PMID", "1")[1]), a3], 0.30, F, "PMID")
    except Exception:
        pass
    # C_VINLS was on VSYS — retarget to PMID
    try:
        fp = find_fp(board, "C_VINLS")
        for p in fp.Pads():
            if p.GetNetname() in ("VSYS", "PMID"):
                # closer to C4 = PMID
                pass
        # rebind: pad nearer package = PMID, other GND
        pads = list(fp.Pads())
        c4p = c4
        pads.sort(key=lambda p: math.hypot(pcbnew.ToMM(p.GetPosition().x) - c4p[0], pcbnew.ToMM(p.GetPosition().y) - c4p[1]))
        pads[0].SetNetCode(netcode(board, "PMID"))
        pads[1].SetNetCode(netcode(board, "GND"))
        xy = (pcbnew.ToMM(pads[0].GetPosition().x), pcbnew.ToMM(pads[0].GetPosition().y))
        poly(board, [xy, c4], 0.30, F, "PMID")
    except Exception as e:
        print("CVINLS", e)

    # VSYS + inductor + R_VSYS + C_SYS
    b5 = pad_xy(board, "U2", "B5")
    a4 = pad_xy(board, "U2", "A4")
    try:
        # L_SYS pad1 SW, pad2 VSYS
        ls1, ls2 = pad_xy(board, "L_SYS", "1"), pad_xy(board, "L_SYS", "2")
        # which is closer to A4?
        if math.hypot(ls1[0] - a4[0], ls1[1] - a4[1]) <= math.hypot(ls2[0] - a4[0], ls2[1] - a4[1]):
            find_fp(board, "L_SYS").FindPadByNumber("1").SetNetCode(netcode(board, "SW"))
            find_fp(board, "L_SYS").FindPadByNumber("2").SetNetCode(netcode(board, "VSYS"))
            poly(board, [a4, ls1], 0.35, F, "SW")
            poly(board, [ls2, b5], 0.35, F, "VSYS")
        else:
            find_fp(board, "L_SYS").FindPadByNumber("2").SetNetCode(netcode(board, "SW"))
            find_fp(board, "L_SYS").FindPadByNumber("1").SetNetCode(netcode(board, "VSYS"))
            poly(board, [a4, ls2], 0.35, F, "SW")
            poly(board, [ls1, b5], 0.35, F, "VSYS")
    except Exception as e:
        print("L_SYS", e)

    rvs = pad_xy(board, "R_VSYS", "1")
    poly(board, [b5, (b5[0], 104.4), (rvs[0], 104.4), rvs], W_PWR, F, "VSYS")
    # 3V3 side of R_VSYS → via to In2 plane
    r3 = pad_xy(board, "R_VSYS", "2")
    add_via(board, r3[0], r3[1], "3V3")
    try:
        for p in find_fp(board, "C_SYS").Pads():
            if p.GetNetname() == "VSYS" or p.GetNumber() == "1":
                # ensure VSYS
                pass
        # C_SYS: nearer B5 = VSYS
        pads = list(find_fp(board, "C_SYS").Pads())
        pads.sort(key=lambda p: math.hypot(pcbnew.ToMM(p.GetPosition().x) - b5[0], pcbnew.ToMM(p.GetPosition().y) - b5[1]))
        pads[0].SetNetCode(netcode(board, "VSYS"))
        pads[1].SetNetCode(netcode(board, "GND"))
        xy = (pcbnew.ToMM(pads[0].GetPosition().x), pcbnew.ToMM(pads[0].GetPosition().y))
        poly(board, [xy, b5], 0.30, F, "VSYS")
        gxy = (pcbnew.ToMM(pads[1].GetPosition().x), pcbnew.ToMM(pads[1].GetPosition().y))
        a5 = pad_xy(board, "U2", "A5")
        poly(board, [gxy, a5], 0.30, F, "GND")
    except Exception as e:
        print("CSYS", e)

    # TS / CD / ISET / ILIM / IPRETERM / LSCTRL routes
    c3 = pad_xy(board, "U2", "C3")
    try:
        poly(board, [pad_xy(board, "R_TS", "2"), c3], W_SIG, F, "TS")
        poly(board, [pad_xy(board, "NTC_BAT", "1"), c3], W_SIG, F, "TS")
        # R_TS pad1 to VBUS corridor
        poly(board, [pad_xy(board, "R_TS", "1"), (108.2, 112.2), (110.6, 112.2)], 0.25, F, "VBUS")
        ng = pad_xy(board, "NTC_BAT", "2")
        add_via(board, ng[0] - 0.8, ng[1], "GND")
        poly(board, [ng, (ng[0] - 0.8, ng[1])], W_SIG, F, "GND")
    except Exception as e:
        print("TS", e)

    e2 = pad_xy(board, "U2", "E2")
    try:
        # R_CD pad closer to E2 = CD
        pads = list(find_fp(board, "R_CD").Pads())
        pads.sort(key=lambda p: math.hypot(pcbnew.ToMM(p.GetPosition().x) - e2[0], pcbnew.ToMM(p.GetPosition().y) - e2[1]))
        pads[0].SetNetCode(netcode(board, "CD"))
        pads[1].SetNetCode(netcode(board, "GND"))
        xy = (pcbnew.ToMM(pads[0].GetPosition().x), pcbnew.ToMM(pads[0].GetPosition().y))
        poly(board, [xy, e2], W_SIG, F, "CD")
        gxy = (pcbnew.ToMM(pads[1].GetPosition().x), pcbnew.ToMM(pads[1].GetPosition().y))
        add_via(board, gxy[0] + 0.5, gxy[1], "GND")
        poly(board, [gxy, (gxy[0] + 0.5, gxy[1])], W_SIG, F, "GND")
    except Exception as e:
        print("CD", e)

    for ref, ball, net in (
        ("R_ISET", "C1", "ISET"),
        ("R_ILIM", "C2", "ILIM"),
        ("R_IPRETERM", "D1", "IPRETERM"),
    ):
        try:
            bp = pad_xy(board, "U2", ball)
            pads = list(find_fp(board, ref).Pads())
            pads.sort(key=lambda p: math.hypot(pcbnew.ToMM(p.GetPosition().x) - bp[0], pcbnew.ToMM(p.GetPosition().y) - bp[1]))
            pads[0].SetNetCode(netcode(board, net))
            pads[1].SetNetCode(netcode(board, "GND"))
            xy = (pcbnew.ToMM(pads[0].GetPosition().x), pcbnew.ToMM(pads[0].GetPosition().y))
            poly(board, [xy, bp], W_SIG, F, net)
            gxy = (pcbnew.ToMM(pads[1].GetPosition().x), pcbnew.ToMM(pads[1].GetPosition().y))
            add_via(board, gxy[0], gxy[1] - 0.6, "GND")
            poly(board, [gxy, (gxy[0], gxy[1] - 0.6)], W_SIG, F, "GND")
        except Exception as e:
            print(ref, e)

    e3 = pad_xy(board, "U2", "E3")
    try:
        pads = list(find_fp(board, "R_LSCTRL").Pads())
        pads.sort(key=lambda p: math.hypot(pcbnew.ToMM(p.GetPosition().x) - e3[0], pcbnew.ToMM(p.GetPosition().y) - e3[1]))
        pads[0].SetNetCode(netcode(board, "LSCTRL"))
        pads[1].SetNetCode(netcode(board, "3V3"))
        xy = (pcbnew.ToMM(pads[0].GetPosition().x), pcbnew.ToMM(pads[0].GetPosition().y))
        poly(board, [xy, e3], W_SIG, F, "LSCTRL")
        gxy = (pcbnew.ToMM(pads[1].GetPosition().x), pcbnew.ToMM(pads[1].GetPosition().y))
        add_via(board, gxy[0] + 0.5, gxy[1], "3V3")
        poly(board, [gxy, (gxy[0] + 0.5, gxy[1])], W_SIG, F, "3V3")
    except Exception as e:
        print("LSCTRL", e)

    # --- 3V3 via stitches to In2 (MCU pads, caps, pullups) ---
    p28, p30 = pad_xy(board, "U1", "28"), pad_xy(board, "U1", "30")
    poly(board, [p30, p28], W_NECK + 0.05, F, "3V3")
    poly(board, [p30, (97.0, p30[1]), (97.0, 87.5)], 0.30, F, "3V3")
    add_via(board, 97.0, 87.5, "3V3")
    poly(board, [p28, (p28[0], 87.5), (106.0, 87.5)], 0.30, F, "3V3")
    add_via(board, 106.0, 87.5, "3V3")
    for ref in ("R_SDA", "R_SCL"):
        try:
            p = pad_xy(board, ref, "2")
            add_via(board, p[0], p[1] - 0.7, "3V3")
            poly(board, [p, (p[0], p[1] - 0.7)], W_SIG, F, "3V3")
        except Exception:
            pass
    for ref in ("C1", "C2", "C3", "C4"):
        try:
            p = pad_xy(board, ref, "1")
            vy = p[1] - 0.6 if ref in ("C1", "C2") else p[1] + 0.6
            add_via(board, p[0], vy, "3V3")
            poly(board, [p, (p[0], vy)], 0.30, F, "3V3")
            g = pad_xy(board, ref, "2")
            gy = g[1] - 0.6 if ref in ("C1", "C2") else g[1] + 0.6
            add_via(board, g[0], gy, "GND")
            poly(board, [g, (g[0], gy)], 0.30, F, "GND")
        except Exception:
            pass

    # GND stitches (not in seal)
    for xy in [
        (109.2, 104.5),
        (108.5, 106.5),
        (113.5, 104.0),
        (97.0, 102.0),
        (103.0, 102.0),
        (100.0, 88.0),
        (86.0, 100.0),
        (114.0, 100.0),
        (117.0, 108.0),
        (94.5, 107.5),
        (89.2, 110.0),
    ]:
        add_via(board, xy[0], xy[1], "GND")

    # U2 GND ties
    a1, a5, d5 = pad_xy(board, "U2", "A1"), pad_xy(board, "U2", "A5"), pad_xy(board, "U2", "D5")
    poly(board, [a1, a5, d5], W_NECK, F, "GND")
    poly(board, [a1, (109.2, a1[1]), (109.2, 104.5)], 0.30, F, "GND")

    # I2C pullups to pads
    for ref, ball in (("R_SDA", "E4"), ("R_SCL", "E5")):
        try:
            poly(board, [pad_xy(board, ref, "1"), pad_xy(board, "U2", ball)], W_SIG, F, "SDA" if "SDA" in ref else "SCL")
        except Exception as e:
            print(ref, e)

    # Cross cleanup F/B only
    def prio(n):
        if n == "GND":
            return 0
        if n in ("3V3", "VBUS", "VBAT", "VSYS", "PMID"):
            return 5
        if n.startswith("EPD_"):
            return 18
        if n.startswith("BTN"):
            return 25
        return 12

    for rnd in range(5):
        tracks = []
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA" or t.GetLayer() not in (F, B):
                continue
            a, b_ = endpoints(t)
            tracks.append((t, t.GetNetname(), t.GetLayer(), a, b_))
        doomed = set()
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                ti, ni, li, ai, bi = tracks[i]
                tj, nj, lj, aj, bj = tracks[j]
                if li != lj or ni == nj or id(ti) in doomed or id(tj) in doomed:
                    continue
                if crosses(ai, bi, aj, bj):
                    doomed.add(id(ti) if prio(ni) <= prio(nj) else id(tj))
        for t, *_ in tracks:
            if id(t) in doomed:
                board.Delete(t)
        print(f"cross {rnd+1}: {len(doomed)}")
        if not doomed:
            break

    # Dwgs: charging note + IP67 seal
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText(
        "CHG: TP1(VBUS)->U2.IN; TP2 GND; BAT->J_BAT; SYS->R_VSYS->3V3. "
        "SW_DBG gates SWD only — does NOT break charge. NTC/TVS/L_SYS/CD per DS."
    )
    txt.SetPosition(pcbnew.VECTOR2I(mm(100), mm(122.2)))
    txt.SetLayer(pcbnew.Dwgs_User)
    txt.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
    board.Add(txt)

    def add_line(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        s.SetLayer(pcbnew.Dwgs_User)
        s.SetWidth(mm(0.1))
        board.Add(s)

    xs, xe, ys, ye = POGO["xmin"], POGO["xmax"], POGO["ymin"], POGO["ymax"]
    add_line(xs, ys, xe, ys)
    add_line(xe, ys, xe, ye)
    add_line(xe, ye, xs, ye)
    add_line(xs, ye, xs, ys)

    try:
        board.GetTitleBlock().SetComment(1, "Ø40 4L — F/In1(GND)/In2(3V3)/B — BQ25120A charge path")
    except Exception:
        pass

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(PCB), board)
    print("saved charging 4L pass")
    os._exit(0)


if __name__ == "__main__":
    main()
