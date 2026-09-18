#!/usr/bin/env python3
"""Migrate Ø40 e-ink watch PCB to 4L and clean shorts using planes.

Stack:
  F.Cu   — components + fine signals + local escapes
  In1.Cu — solid GND plane
  In2.Cu — 3V3 pour (+ optional power tracks)
  B.Cu   — pogo pads + secondary signals + light GND pour

IP67: no NEW vias in pogo seal land. Keep SW_DBG gating, Ø40, BQ passives.
"""
from __future__ import annotations

import math
from pathlib import Path

import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
W_SIG, W_PWR, W_FAT, W_NECK = 0.18, 0.45, 0.50, 0.20
VIA_D, VIA_DRILL = 0.60, 0.30
CX, CY, R_ZONE = 100.0, 100.0, 19.4
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)


def mm(v):
    return pcbnew.FromMM(v)


def netcode(board, name):
    ni = board.GetNetInfo().GetNetItem(name)
    if ni is None:
        raise KeyError(name)
    return ni.GetNetCode()


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


def pad_by_net(board, ref, net):
    for p in find_fp(board, ref).Pads():
        if p.GetNetname() == net:
            return (
                pcbnew.ToMM(p.GetPosition().x),
                pcbnew.ToMM(p.GetPosition().y),
                p.GetNumber(),
            )
    raise KeyError(f"{ref}:{net}")


def add_track(board, x1, y1, x2, y2, w, layer, net):
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w))
    t.SetLayer(layer)
    t.SetNetCode(netcode(board, net))
    board.Add(t)
    return t


def poly(board, pts, w, layer, net):
    for a, b in zip(pts, pts[1:]):
        add_track(board, a[0], a[1], b[0], b[1], w, layer, net)


def in_seal(x, y):
    return POGO["xmin"] <= x <= POGO["xmax"] and POGO["ymin"] <= y <= POGO["ymax"]


def add_via(board, x, y, net):
    if in_seal(x, y):
        print(f"  SKIP via in seal ({x:.2f},{y:.2f}) {net}")
        return None
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    try:
        v.SetWidth(pcbnew.F_Cu, mm(VIA_D))
    except Exception:
        pass
    try:
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    except Exception:
        pass
    v.SetDrill(mm(VIA_DRILL))
    v.SetNetCode(netcode(board, net))
    board.Add(v)
    return v


def add_circle_zone(board, net, layer, clearance=0.20, min_t=0.15):
    z = pcbnew.ZONE(board)
    z.SetNetCode(netcode(board, net))
    z.SetLayer(layer)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_t))
    try:
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    except Exception:
        pass
    for i in range(64):
        ang = 2 * math.pi * i / 64
        z.Outline().Append(mm(CX + R_ZONE * math.cos(ang)), mm(CY + R_ZONE * math.sin(ang)))
    board.Add(z)
    return z


def endpoints(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return [(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))]
    a, b = t.GetStart(), t.GetEnd()
    return [
        (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)),
        (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)),
    ]


def orient(p, q, r):
    return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])


def segments_cross(a, b, c, d):
    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


def main():
    board = pcbnew.LoadBoard(str(PCB))
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    IN1, IN2 = pcbnew.In1_Cu, pcbnew.In2_Cu

    # ------------------------------------------------------------------
    # 1) Enable 4 copper layers
    # ------------------------------------------------------------------
    board.SetCopperLayerCount(4)
    board.SetLayerType(IN1, pcbnew.LT_POWER)
    board.SetLayerType(IN2, pcbnew.LT_POWER)
    board.SetLayerType(F, pcbnew.LT_SIGNAL)
    board.SetLayerType(B, pcbnew.LT_SIGNAL)
    print("copper layers:", board.GetCopperLayerCount())

    ensure_net(board, "PMID")
    # Ensure PMID on A3/B3
    for num in ("A3", "B3"):
        for p in find_fp(board, "U2").Pads():
            if p.GetNumber() == num:
                p.SetNetCode(netcode(board, "PMID"))

    # ------------------------------------------------------------------
    # 2) Remove old copper zones (will recreate for 4L stack)
    # ------------------------------------------------------------------
    for z in list(board.Zones()):
        if not z.GetIsRuleArea():
            board.Delete(z)
    print("cleared copper zones")

    # In1: solid GND
    add_circle_zone(board, "GND", IN1, clearance=0.20)
    # In2: 3V3 power pour
    add_circle_zone(board, "3V3", IN2, clearance=0.25)
    # B.Cu: light GND pour (helps pogo return; keepout via clearance)
    add_circle_zone(board, "GND", B, clearance=0.25)
    # F.Cu: small local 3V3 pour under MCU area optional — skip to reduce shorts;
    # keep F clear for signals. Tiny GND pour? skip.
    print("zones: In1 GND, In2 3V3, B GND")

    # ------------------------------------------------------------------
    # 3) Delete long power / GND tracks on F/B that planes replace
    #    Keep short escapes (<2.5mm) near pads; delete long spines.
    # ------------------------------------------------------------------
    POWER_NETS = {"GND", "3V3", "3V3_DISP", "VBUS", "VBAT", "VSYS", "PMID"}

    def is_long_power_spine(t):
        if t.GetClass() == "PCB_VIA":
            return False
        net = t.GetNetname()
        layer = t.GetLayer()
        if net not in POWER_NETS:
            return False
        # Keep In1/In2 tracks if any
        if layer in (IN1, IN2):
            return False
        pts = endpoints(t)
        if len(pts) < 2:
            return False
        (x1, y1), (x2, y2) = pts
        L = math.hypot(x1 - x2, y1 - y2)
        # Always delete GND tracks on F/B (plane handles) except ultra-short ties
        if net == "GND" and L > 0.8:
            return True
        # Delete long 3V3 on F/B — In2 plane
        if net == "3V3" and L > 2.0:
            return True
        # Delete long 3V3_DISP F/B spines — will re-route short + via to In2-ish
        # Actually 3V3_DISP is NOT on In2 (In2 is 3V3). Keep 3V3_DISP as tracks
        # but delete ones that are known shorting corridors later.
        if net == "3V3_DISP" and L > 6.0 and layer == F:
            return True
        # Long VBUS/VBAT/VSYS on F — keep fat but delete duplicates > 15mm weird
        if net in ("VBUS", "VBAT", "VSYS") and L > 12.0:
            return True
        return False

    doomed = [t for t in list(board.GetTracks()) if is_long_power_spine(t)]
    for t in doomed:
        board.Delete(t)
    print(f"deleted {len(doomed)} long power/GND spines")

    # Delete 3V3 along U1 pad row y=86.35 (guaranteed short)
    doomed = []
    for t in list(board.GetTracks()):
        if t.GetClass() == "PCB_VIA" or t.GetNetname() != "3V3":
            continue
        if t.GetLayer() != F:
            continue
        (x1, y1), (x2, y2) = endpoints(t)
        if abs(y1 - 86.35) < 0.2 and abs(y2 - 86.35) < 0.2 and max(x1, x2) > 99.0:
            doomed.append(t)
    for t in doomed:
        board.Delete(t)
    print(f"deleted {len(doomed)} 3V3 pad-row shorts")

    # Remove via-in-pad under pogo TP*
    tps = [(93.0, 114.0), (96.0, 114.0), (99.0, 114.0), (93.0, 111.0), (96.0, 111.0), (99.0, 111.0)]
    doomed = []
    for t in list(board.GetTracks()):
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = endpoints(t)[0]
        for tx, ty in tps:
            if math.hypot(x - tx, y - ty) < 0.35:
                doomed.append(t)
                break
    for t in doomed:
        board.Delete(t)
    print(f"deleted {len(doomed)} pogo via-in-pad")

    # ------------------------------------------------------------------
    # 4) Geometric cross cleanup on F and B (signals only priority)
    # ------------------------------------------------------------------
    prio = {
        "GND": 0,
        "3V3": 5,
        "3V3_DISP": 8,
        "VBUS": 10,
        "VBAT": 10,
        "VSYS": 10,
        "PMID": 10,
    }

    def np(n):
        if n.startswith("EPD_"):
            return 18
        if n.startswith("BTN"):
            return 25
        if "SWD" in n or n == "nRESET" or "POGO" in n or n == "nRESET_POGO":
            return 15
        if n in ("SDA", "SCL", "PMIC_INT"):
            return 16
        return prio.get(n, 20)

    for round_i in range(6):
        tracks = []
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                continue
            if t.GetLayer() not in (F, B):
                continue
            a, b = endpoints(t)
            tracks.append((t, t.GetNetname(), t.GetLayer(), a, b))
        doomed_ids = set()
        for i in range(len(tracks)):
            if id(tracks[i][0]) in doomed_ids:
                continue
            for j in range(i + 1, len(tracks)):
                if id(tracks[j][0]) in doomed_ids:
                    continue
                ti, ni, li, ai, bi = tracks[i]
                tj, nj, lj, aj, bj = tracks[j]
                if li != lj or ni == nj:
                    continue
                if not segments_cross(ai, bi, aj, bj):
                    continue
                if np(ni) < np(nj):
                    doomed_ids.add(id(ti))
                elif np(nj) < np(ni):
                    doomed_ids.add(id(tj))
                else:
                    li_ = math.hypot(ai[0] - bi[0], ai[1] - bi[1])
                    lj_ = math.hypot(aj[0] - bj[0], aj[1] - bj[1])
                    doomed_ids.add(id(ti) if li_ <= lj_ else id(tj))
        for t, *_ in tracks:
            if id(t) in doomed_ids:
                board.Delete(t)
        print(f"cross round {round_i+1}: deleted {len(doomed_ids)}")
        if not doomed_ids:
            break

    # ------------------------------------------------------------------
    # 5) Rebuild critical connectivity using vias → planes
    # ------------------------------------------------------------------
    # --- GND stitch vias (not in seal) ---
    gnd_vias = [
        (109.2, 104.5),
        (108.5, 106.5),
        (113.5, 104.0),
        (113.5, 107.5),
        (97.0, 102.0),
        (103.0, 102.0),
        (95.0, 95.0),
        (105.0, 95.0),
        (100.0, 88.0),
        (86.0, 100.0),
        (114.0, 100.0),
        (110.9, 112.5),
        (113.7, 110.5),
        (117.2, 108.0),
        (94.5, 107.5),
        (104.0, 107.5),
        (100.0, 104.0),
        (92.0, 104.0),
    ]
    for x, y in gnd_vias:
        add_via(board, x, y, "GND")

    # U2 GND pad ties + via
    a1 = pad_xy(board, "U2", "A1")
    a5 = pad_xy(board, "U2", "A5")
    d5 = pad_xy(board, "U2", "D5")
    poly(board, [a1, a5], W_NECK, F, "GND")
    poly(board, [a5, d5], W_NECK, F, "GND")
    poly(board, [a1, (109.2, a1[1]), (109.2, 104.5)], 0.30, F, "GND")

    # Cap GND pads → nearby via
    for ref in ("C_IN", "C_BAT", "C_PMID"):
        try:
            p = pad_xy(board, ref, "2")
            poly(board, [p, (109.2, p[1]), (109.2, 104.5)], 0.30, F, "GND")
        except Exception as e:
            print(ref, e)
    for ref in ("C_SYS", "C_VINLS", "C_LDO"):
        for p in find_fp(board, ref).Pads():
            if p.GetNetname() == "GND":
                xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                poly(board, [xy, a5], 0.30, F, "GND")

    # SW GND pads
    for ref in ("SW1", "SW2", "SW3"):
        try:
            g = pad_xy(board, ref, "2")
            vx, vy = g[0] + 0.3, g[1] + 0.8
            add_via(board, vx, vy, "GND")
            poly(board, [g, (vx, g[1]), (vx, vy)], 0.30, F, "GND")
        except Exception as e:
            print(ref, e)

    # --- 3V3: pad escapes → via → In2 plane ---
    p28 = pad_xy(board, "U1", "28")
    p30 = pad_xy(board, "U1", "30")
    poly(board, [p30, p28], W_NECK + 0.05, F, "3V3")
    # west via (not along pad row)
    poly(board, [p30, (97.0, p30[1]), (97.0, 87.5)], 0.30, F, "3V3")
    add_via(board, 97.0, 87.5, "3V3")
    # east via drop then east at y=87.5
    poly(board, [p28, (p28[0], 87.5), (106.0, 87.5)], 0.30, F, "3V3")
    add_via(board, 106.0, 87.5, "3V3")
    # R_VSYS 3V3 side
    r3 = pad_xy(board, "R_VSYS", "2")
    add_via(board, r3[0], r3[1], "3V3")
    # existing C1/C2/C3/C4
    for ref in ("C1", "C2", "C3", "C4"):
        try:
            p = pad_xy(board, ref, "1")
            add_via(board, p[0], p[1] - 0.6 if ref in ("C1", "C2") else p[1] + 0.6, "3V3")
            vy = p[1] - 0.6 if ref in ("C1", "C2") else p[1] + 0.6
            poly(board, [p, (p[0], vy)], 0.30, F, "3V3")
            # GND via other pad
            g = pad_xy(board, ref, "2")
            add_via(board, g[0], g[1] - 0.6 if ref in ("C1", "C2") else g[1] + 0.6, "GND")
            gy = g[1] - 0.6 if ref in ("C1", "C2") else g[1] + 0.6
            poly(board, [g, (g[0], gy)], 0.30, F, "GND")
        except Exception as e:
            print(ref, e)
    # I2C pullups to 3V3 via plane
    for ref in ("R_SDA", "R_SCL"):
        p = pad_xy(board, ref, "2")
        add_via(board, p[0], p[1] - 0.7, "3V3")
        poly(board, [p, (p[0], p[1] - 0.7)], W_SIG, F, "3V3")
    # R1/R2 3V3
    for ref in ("R1", "R2"):
        try:
            p = pad_xy(board, ref, "1")
            add_via(board, p[0] + 0.6, p[1], "3V3")
            poly(board, [p, (p[0] + 0.6, p[1])], 0.25, F, "3V3")
        except Exception:
            pass
    # J_SWD 3V3
    for p in find_fp(board, "J_SWD").Pads():
        if p.GetNetname() == "3V3":
            xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            add_via(board, 85.5, xy[1], "3V3")
            poly(board, [xy, (85.5, xy[1])], W_PWR, F, "3V3")

    # --- VBUS: TP1 → corridor → A2 + C_IN (F only, PowerFat) ---
    a2 = pad_xy(board, "U2", "A2")
    poly(
        board,
        [(93.0, 114.0), (93.0, 112.2), (110.6, 112.2), (110.6, a2[1]), a2],
        W_FAT,
        F,
        "VBUS",
    )
    try:
        cin = pad_xy(board, "C_IN", "1")
        poly(board, [cin, (cin[0], a2[1]), a2], 0.35, F, "VBUS")
    except Exception:
        pass
    # Optional In3-style: put short VBUS also on In2 as track? Keep F only for VBUS.
    add_via(board, 104.0, 112.2, "VBUS")  # outside seal — for future In3; on 4L just stitch

    # --- VBAT ---
    b1 = pad_xy(board, "U2", "B1")
    b2 = pad_xy(board, "U2", "B2")
    poly(board, [b1, b2], W_NECK, F, "VBAT")
    poly(board, [b1, (b1[0], 107.9), (100.0, 107.9), (100.0, 115.8)], W_FAT, F, "VBAT")
    try:
        cbat = pad_xy(board, "C_BAT", "1")
        poly(board, [cbat, b1], 0.35, F, "VBAT")
    except Exception:
        pass
    try:
        jbat = pad_xy(board, "J_BAT", "1")
        poly(board, [(100.0, 115.8), jbat], W_FAT, F, "VBAT")
    except Exception:
        pass

    # --- VSYS + PMID + R_VSYS ---
    b5 = pad_xy(board, "U2", "B5")
    b4 = pad_xy(board, "U2", "B4")
    c4 = pad_xy(board, "U2", "C4")
    poly(board, [b5, b4, c4], W_NECK, F, "VSYS")
    rvs = pad_xy(board, "R_VSYS", "1")
    poly(board, [b5, (b5[0], 104.4), (rvs[0], 104.4), rvs], W_PWR, F, "VSYS")
    for ref in ("C_SYS", "C_VINLS"):
        for p in find_fp(board, ref).Pads():
            if p.GetNetname() == "VSYS":
                xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                tgt = b5 if ref == "C_SYS" else c4
                poly(board, [xy, tgt], 0.30, F, "VSYS")

    a3 = pad_xy(board, "U2", "A3")
    b3 = pad_xy(board, "U2", "B3")
    poly(board, [a3, b3], W_NECK, F, "PMID")
    try:
        cp = pad_xy(board, "C_PMID", "1")
        poly(board, [cp, (a3[0], cp[1]), a3], 0.30, F, "PMID")
    except Exception:
        pass

    # --- 3V3_DISP: C5 → short F → via → route on B (secondary) to FPCs ---
    c5 = pad_xy(board, "U2", "C5")
    poly(board, [c5, (113.0, c5[1])], W_PWR, F, "3V3_DISP")
    add_via(board, 113.0, c5[1], "3V3_DISP")
    for p in find_fp(board, "C_LDO").Pads():
        if p.GetNetname() == "3V3_DISP":
            xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            poly(board, [xy, (113.0, xy[1]), (113.0, c5[1])], 0.30, F, "3V3_DISP")
    # B.Cu distribution
    poly(
        board,
        [(113.0, c5[1]), (104.0, 105.5), (96.0, 105.5), (92.0, 105.5), (92.0, 87.5), (94.0, 87.5)],
        W_PWR,
        B,
        "3V3_DISP",
    )
    add_via(board, 94.0, 87.5, "3V3_DISP")
    add_via(board, 92.0, 105.5, "3V3_DISP")
    add_via(board, 104.0, 105.5, "3V3_DISP")
    # Left strap
    poly(board, [(92.0, 105.5), (84.5, 105.5)], W_PWR, B, "3V3_DISP")
    add_via(board, 84.5, 105.5, "3V3_DISP")
    for p in find_fp(board, "J_STRAP_L").Pads():
        if p.GetNetname() == "3V3_DISP":
            xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            poly(board, [(84.5, 105.5), (84.5, xy[1]), xy], W_PWR, F, "3V3_DISP")
    # Right strap
    poly(board, [(113.0, c5[1]), (115.5, c5[1]), (115.5, 102.5)], W_PWR, B, "3V3_DISP")
    add_via(board, 115.5, 102.5, "3V3_DISP")
    for p in find_fp(board, "J_STRAP_R").Pads():
        if p.GetNetname() == "3V3_DISP":
            xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            poly(board, [(115.5, 102.5), (115.5, xy[1]), xy], W_PWR, F, "3V3_DISP")
    # Main display
    poly(board, [(94.0, 87.5), (94.0, 82.5), (97.75, 82.5)], W_PWR, F, "3V3_DISP")
    for p in find_fp(board, "J_DISP_MAIN").Pads():
        if p.GetNetname() == "3V3_DISP":
            xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            poly(board, [(97.75, 82.5), (xy[0], 82.5), xy], W_PWR, F, "3V3_DISP")

    # --- I2C on B ---
    sda_u = pad_xy(board, "U1", "27")
    scl_u = pad_xy(board, "U1", "29")
    sda_p = pad_xy(board, "U2", "E4")
    scl_p = pad_xy(board, "U2", "E5")
    add_via(board, sda_u[0] + 0.5, 88.5, "SDA")
    poly(board, [sda_u, (sda_u[0] + 0.5, sda_u[1]), (sda_u[0] + 0.5, 88.5)], W_SIG, F, "SDA")
    poly(board, [(sda_u[0] + 0.5, 88.5), (109.0, 88.5), (109.0, 107.2), (sda_p[0], 107.2)], W_SIG, B, "SDA")
    add_via(board, sda_p[0], 107.2, "SDA")
    poly(board, [(sda_p[0], 107.2), sda_p], W_SIG, F, "SDA")
    try:
        rs = pad_xy(board, "R_SDA", "1")
        poly(board, [rs, sda_p], W_SIG, F, "SDA")
    except Exception:
        pass

    add_via(board, scl_u[0] + 0.5, 88.9, "SCL")
    poly(board, [scl_u, (scl_u[0] + 0.5, scl_u[1]), (scl_u[0] + 0.5, 88.9)], W_SIG, F, "SCL")
    poly(board, [(scl_u[0] + 0.5, 88.9), (109.6, 88.9), (109.6, 107.5), (scl_p[0], 107.5)], W_SIG, B, "SCL")
    add_via(board, scl_p[0], 107.5, "SCL")
    poly(board, [(scl_p[0], 107.5), scl_p], W_SIG, F, "SCL")
    try:
        rs = pad_xy(board, "R_SCL", "1")
        poly(board, [rs, scl_p], W_SIG, F, "SCL")
    except Exception:
        pass

    try:
        int_u = pad_by_net(board, "U1", "PMIC_INT")
        int_p = pad_xy(board, "U2", "D2")
        add_via(board, int_u[0] - 0.5, 89.3, "PMIC_INT")
        poly(board, [(int_u[0], int_u[1]), (int_u[0] - 0.5, int_u[1]), (int_u[0] - 0.5, 89.3)], W_SIG, F, "PMIC_INT")
        poly(board, [(int_u[0] - 0.5, 89.3), (94.0, 89.3), (94.0, 106.4), (int_p[0], 106.4)], W_SIG, B, "PMIC_INT")
        add_via(board, int_p[0], 106.4, "PMIC_INT")
        poly(board, [(int_p[0], 106.4), int_p], W_SIG, F, "PMIC_INT")
    except Exception as e:
        print("INT", e)

    # --- SWD F clear corridors ---
    for net, dbg_pad, xcor in (
        ("SWDIO", "1", 88.0),
        ("SWDCLK", "2", 88.5),
        ("nRESET", "3", 89.0),
    ):
        try:
            src = pad_by_net(board, "U1", net)
            dst = pad_xy(board, "SW_DBG", dbg_pad)
            poly(board, [(src[0], src[1]), (xcor, src[1]), (xcor, dst[1]), dst], W_SIG, F, net)
        except Exception as e:
            print(net, e)

    for net, dbg_pad, tp in (
        ("SWDIO_POGO", "6", (99.0, 114.0)),
        ("SWDCLK_POGO", "5", (93.0, 111.0)),
        ("nRESET_POGO", "4", (96.0, 111.0)),
    ):
        src = pad_xy(board, "SW_DBG", dbg_pad)
        poly(board, [src, (tp[0], 108.0), tp], W_SIG, F, net)

    # --- Buttons on B ---
    for net, sw, dx in (("BTN1", "SW1", 0.8), ("BTN2", "SW2", -0.8), ("BTN3", "SW3", 0.9)):
        try:
            src = pad_by_net(board, "U1", net)
            dst = pad_xy(board, sw, "1")
            vx, vy = src[0] + dx, src[1] + 1.0
            add_via(board, vx, vy, net)
            poly(board, [(src[0], src[1]), (vx, src[1]), (vx, vy)], W_SIG, F, net)
            poly(board, [(vx, vy), (vx, 110.5), (dst[0], 110.5)], W_SIG, B, net)
            add_via(board, dst[0], 110.5, net)
            poly(board, [(dst[0], 110.5), dst], W_SIG, F, net)
        except Exception as e:
            print(net, e)

    # --- SPI: F escape → via → B star ---
    farm = {
        "EPD_SCK": {"pad": "9", "vias": [(105.5, 91.5), (97.0, 85.5), (115.0, 96.5), (85.0, 96.5)]},
        "EPD_MOSI": {"pad": "20", "vias": [(106.5, 90.8), (98.0, 85.5), (114.5, 97.5), (86.0, 97.5)]},
        "EPD_DC": {"pad": "19", "vias": [(102.0, 88.8), (99.0, 85.5), (113.5, 98.5), (86.5, 98.5)]},
        "EPD_RST": {"pad": "16", "vias": [(104.0, 87.8), (100.0, 85.5), (112.5, 99.5), (87.5, 99.5)]},
    }
    for net, cfg in farm.items():
        try:
            src = pad_xy(board, "U1", cfg["pad"])
        except KeyError:
            src = pad_by_net(board, "U1", net)[:2]
        v0 = cfg["vias"][0]
        poly(board, [src, v0], W_SIG, F, net)
        add_via(board, v0[0], v0[1], net)
        for v in cfg["vias"][1:]:
            add_via(board, v[0], v[1], net)
            poly(board, [v0, v], W_SIG, B, net)

    singles = [
        ("EPD_CS_MAIN", "22", (101.0, 85.5)),
        ("EPD_BUSY_MAIN", "13", (105.8, 90.0)),
        ("EPD_CS_L", "23", (91.2, 88.5)),
        ("EPD_CS_R", "24", (108.8, 88.5)),
        ("EPD_BUSY_L", "10", (90.2, 97.0)),
        ("EPD_BUSY_R", "14", (109.8, 99.0)),
    ]
    for net, pnum, via_pt in singles:
        try:
            src = pad_xy(board, "U1", pnum)
        except Exception:
            try:
                src = pad_by_net(board, "U1", net)[:2]
            except Exception as e:
                print("spi", net, e)
                continue
        add_via(board, via_pt[0], via_pt[1], net)
        poly(board, [src, via_pt], W_SIG, F, net)
        for jref in ("J_DISP_MAIN", "J_STRAP_L", "J_STRAP_R"):
            for p in find_fp(board, jref).Pads():
                if p.GetNetname() != net:
                    continue
                xy = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                poly(board, [via_pt, (xy[0], via_pt[1])], W_SIG, B, net)
                vx, vy = xy[0], via_pt[1]
                if not in_seal(vx, vy):
                    add_via(board, vx, vy, net)
                    poly(board, [(vx, vy), xy], W_SIG, F, net)

    # ------------------------------------------------------------------
    # 6) IP67 Dwgs seal outline (ensure present)
    # ------------------------------------------------------------------
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

    # Title block comment
    try:
        board.GetTitleBlock().SetComment(1, "Ø40mm 4L watch PCB — F/In1(GND)/In2(3V3)/B — REV0.2")
    except Exception:
        pass

    # Final cross cleanup once more
    for round_i in range(4):
        tracks = []
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA" or t.GetLayer() not in (F, B):
                continue
            a, b = endpoints(t)
            tracks.append((t, t.GetNetname(), t.GetLayer(), a, b))
        doomed_ids = set()
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                ti, ni, li, ai, bi = tracks[i]
                tj, nj, lj, aj, bj = tracks[j]
                if li != lj or ni == nj:
                    continue
                if id(ti) in doomed_ids or id(tj) in doomed_ids:
                    continue
                if segments_cross(ai, bi, aj, bj):
                    if np(ni) <= np(nj):
                        doomed_ids.add(id(ti))
                    else:
                        doomed_ids.add(id(tj))
        for t, *_ in tracks:
            if id(t) in doomed_ids:
                board.Delete(t)
        print(f"final cross {round_i+1}: {len(doomed_ids)}")
        if not doomed_ids:
            break

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(PCB), board)
    print("saved 4L board")
    print("layers:", board.GetCopperLayerCount())
    for z in board.Zones():
        if not z.GetIsRuleArea():
            print(" zone", z.GetNetname(), z.GetLayerName())


if __name__ == "__main__":
    main()
