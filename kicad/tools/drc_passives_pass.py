#!/usr/bin/env python3
"""DRC passives pass: BQ25120A decap + I2C pullups + short/cross cleanup on 2L Ø40.

Harvard honesty: 2L density may prevent shorts→0; document remaining blockers.
IP67: no NEW vias inside pogo seal envelope; remove via-in-pad under TP* where safe.
"""
from __future__ import annotations

import math
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
BACKUP = ROOT / "backups" / f"e-ink-watch.kicad_pcb.pre-drc-passives-{datetime.now():%H%M%S}"

W_SIG = 0.18
W_PWR = 0.45
W_FAT = 0.50
W_NECK = 0.20
VIA_D = 0.60
VIA_DRILL = 0.30

# Pogo seal envelope (PCB coords): matrix 2x3 @3mm, sheet ~15.4x12.4 + margin
# TP cluster roughly x=91.5..100.5, y=109..116 — keepout expanded
POGO_SEAL = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def netcode(board, name: str) -> int:
    return board.GetNetInfo().GetNetItem(name).GetNetCode()


def ensure_net(board, name: str) -> int:
    ni = board.GetNetInfo().GetNetItem(name)
    if ni is not None:
        return ni.GetNetCode()
    new = pcbnew.NETINFO_ITEM(board, name)
    board.Add(new)
    return new.GetNetCode()


def find_fp(board, ref: str):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    raise KeyError(ref)


def pad_xy(board, ref: str, num: str):
    fp = find_fp(board, ref)
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            pos = p.GetPosition()
            return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
    raise KeyError(f"{ref}.{num}")


def set_pad_net(board, ref: str, num: str, netname: str) -> None:
    code = ensure_net(board, netname)
    for p in find_fp(board, ref).Pads():
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


def poly(board, pts, width, layer, netname):
    for a, b in zip(pts, pts[1:]):
        add_track(board, a[0], a[1], b[0], b[1], width, layer, netname)


def in_pogo_seal(x, y) -> bool:
    return (
        POGO_SEAL["xmin"] <= x <= POGO_SEAL["xmax"]
        and POGO_SEAL["ymin"] <= y <= POGO_SEAL["ymax"]
    )


def add_via(board, x, y, netname, allow_in_seal=False):
    if in_pogo_seal(x, y) and not allow_in_seal:
        print(f"  SKIP via in pogo seal ({x:.2f},{y:.2f}) net={netname}")
        return None
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    try:
        v.SetWidth(mm(VIA_D))
    except TypeError:
        try:
            v.SetWidth(pcbnew.F_Cu, mm(VIA_D))
        except Exception:
            pass
    v.SetDrill(mm(VIA_DRILL))
    v.SetNetCode(netcode(board, netname))
    board.Add(v)
    return v


def endpoints(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return [(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))]
    a, b = t.GetStart(), t.GetEnd()
    return [
        (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)),
        (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)),
    ]


def seg_len(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def nearly(a, b, tol=0.12):
    return abs(a - b) < tol


def track_hits_bbox(a, b, xmin, xmax, ymin, ymax):
    # crude: either endpoint in box or segment crosses box
    for x, y in (a, b):
        if xmin <= x <= xmax and ymin <= y <= ymax:
            return True
    # axis-aligned quick reject
    if max(a[0], b[0]) < xmin or min(a[0], b[0]) > xmax:
        return False
    if max(a[1], b[1]) < ymin or min(a[1], b[1]) > ymax:
        return False
    return True


def delete_tracks(board, pred, label=""):
    doomed = []
    for t in list(board.GetTracks()):
        if pred(t):
            doomed.append(t)
    for t in doomed:
        board.Delete(t)
    print(f"deleted {len(doomed)} {label}")
    return len(doomed)


def load_fp(board, lib_nickname, fp_name, ref, value, x, y, rot=0):
    """Place footprint from global KiCad lib via IO manager."""
    io = pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    # Try standard path
    paths = [
        f"/usr/share/kicad/footprints/{lib_nickname}.pretty/{fp_name}.kicad_mod",
    ]
    fp = None
    for path in paths:
        if Path(path).exists():
            fp = io.FootprintLoad(str(Path(path).parent), fp_name)
            break
    if fp is None:
        # FootprintLoad with lib path
        libpath = f"/usr/share/kicad/footprints/{lib_nickname}.pretty"
        fp = pcbnew.FootprintLoad(libpath, fp_name)
    if fp is None:
        raise RuntimeError(f"Cannot load {lib_nickname}:{fp_name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    # unique path
    try:
        fp.SetFPIDAsString(f"{lib_nickname}:{fp_name}")
    except Exception:
        pass
    board.Add(fp)
    return fp


def assign_cap_nets(fp, net_pos, net_neg):
    """0402: pad1 left / pad2 right when rot=0."""
    pads = sorted(fp.Pads(), key=lambda p: p.GetPosition().x)
    if len(pads) != 2:
        pads = list(fp.Pads())
    pads[0].SetNetCode(netcode(fp.GetParent() if False else None, net_pos) if False else None)


def wire_two_pad(board, fp, net_a, net_b):
    """Assign nets to pad 1 and pad 2 by number."""
    for p in fp.Pads():
        n = p.GetNumber()
        if n == "1":
            p.SetNetCode(netcode(board, net_a))
        elif n == "2":
            p.SetNetCode(netcode(board, net_b))


def main():
    shutil.copy2(PCB, BACKUP)
    print("backup", BACKUP)

    board = pcbnew.LoadBoard(str(PCB))
    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    # ------------------------------------------------------------------
    # 1) Zone hygiene: one GND F.Cu, one GND B.Cu; keep 3V3 F
    # ------------------------------------------------------------------
    gnd_f = []
    gnd_b = []
    for z in list(board.Zones()):
        if z.GetIsRuleArea():
            continue
        if z.GetNetname() == "GND":
            if z.GetLayer() == F:
                gnd_f.append(z)
            elif z.GetLayer() == B:
                gnd_b.append(z)
    print("GND zones F/B:", len(gnd_f), len(gnd_b))
    # Keep first F, convert extras to B or delete
    if len(gnd_f) >= 2:
        for z in gnd_f[1:]:
            if not gnd_b:
                z.SetLayer(B)
                gnd_b.append(z)
                print("moved duplicate GND F → B")
            else:
                board.Delete(z)
                print("deleted duplicate GND F zone")
    if not gnd_b:
        z = pcbnew.ZONE(board)
        z.SetNetCode(netcode(board, "GND"))
        z.SetLayer(B)
        z.SetLocalClearance(mm(0.20))
        z.SetMinThickness(mm(0.15))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        CX, CY, R = 100.0, 100.0, 19.4
        for i in range(48):
            ang = 2 * math.pi * i / 48
            z.Outline().Append(mm(CX + R * math.cos(ang)), mm(CY + R * math.sin(ang)))
        board.Add(z)
        print("added B.Cu GND zone")

    # ------------------------------------------------------------------
    # 2) Assign PMID to A3/B3 (datasheet)
    # ------------------------------------------------------------------
    ensure_net(board, "PMID")
    set_pad_net(board, "U2", "A3", "PMID")
    set_pad_net(board, "U2", "B3", "PMID")
    # Tie PMID balls
    poly(board, [(111.0, 105.2), (111.0, 105.6)], W_NECK, F, "PMID")
    print("PMID assigned A3/B3")

    # ------------------------------------------------------------------
    # 3) Delete known shorting / dangerous tracks
    # ------------------------------------------------------------------
    def is_dangerous(t):
        if t.GetClass() == "PCB_VIA":
            return False
        pts = endpoints(t)
        if len(pts) < 2:
            return False
        (x1, y1), (x2, y2) = pts
        net = t.GetNetname()
        layer = t.GetLayer()

        # 3V3 across U1 north pad row — guaranteed short
        if net == "3V3" and layer == F:
            if nearly(y1, 86.35, 0.2) and nearly(y2, 86.35, 0.2):
                if max(x1, x2) > 99.0:  # extends past pad 28 toward SPI pads
                    return True

        # GND bus under J_DISP_MAIN pad row / EPD fanout (y≈83.15–84.25)
        if net == "GND" and layer == F:
            if nearly(y1, 84.10, 0.15) and nearly(y2, 84.10, 0.15) and min(x1, x2) < 102:
                return True
            if nearly(y1, 83.15, 0.15) and nearly(y2, 83.15, 0.15) and 94 < max(x1, x2) < 102:
                return True
            # vertical stubs feeding that bus
            if nearly(x1, 98.25, 0.1) and nearly(x2, 98.25, 0.1) and min(y1, y2) < 84.5:
                return True
            if nearly(x1, 101.75, 0.1) and nearly(x2, 101.75, 0.1) and min(y1, y2) < 84.5:
                return True
            # long horizontal GND through FPC L/R corridors that cross signals
            if nearly(y1, 98.75, 0.1) and nearly(y2, 98.75, 0.1) and abs(x1 - x2) > 2.5:
                # keep short pad ties only — delete long spines
                return True
            if nearly(y1, 102.25, 0.1) and nearly(y2, 102.25, 0.1) and abs(x1 - x2) > 2.5:
                return True
            # vertical GND at x=106.2 crossing 3V3 zone / caps
            if nearly(x1, 106.2, 0.1) and nearly(x2, 106.2, 0.1) and abs(y1 - y2) > 3:
                return True
            if nearly(x1, 93.8, 0.1) and nearly(x2, 93.8, 0.1) and abs(y1 - y2) > 3:
                return True
            # GND y=104.65 through U2 / VSYS
            if nearly(y1, 104.65, 0.1) and nearly(y2, 104.65, 0.1) and max(x1, x2) > 110:
                return True

        # VSYS long stub west across board into 3V3/GND chaos
        if net == "VSYS" and layer == F:
            if nearly(y1, 105.6, 0.15) and nearly(y2, 105.6, 0.15) and min(x1, x2) < 108:
                return True

        # VBAT long horizontal at y=107.2 crossing buttons / VBUS
        if net == "VBAT" and layer == F:
            if nearly(y1, 107.2, 0.15) and nearly(y2, 107.2, 0.15) and abs(x1 - x2) > 5:
                return True
            # vertical VBAT down into pogo seal
            if nearly(x1, 110.2, 0.15) and nearly(x2, 110.2, 0.15) and max(y1, y2) > 110:
                return True

        # VBUS vertical stub at x=108 through BTN area
        if net == "VBUS" and layer == F:
            if nearly(x1, 108.0, 0.15) and nearly(x2, 108.0, 0.15) and min(y1, y2) < 110:
                return True
            # dangling stub x=93 y=110-114 duplicate of PowerFat
            if nearly(x1, 93.0, 0.1) and nearly(x2, 93.0, 0.1):
                w = pcbnew.ToMM(t.GetWidth())
                if w < 0.4:  # thin duplicate
                    return True

        # BTN horizontals at y=103.60 through 3V3 corridor
        if net in ("BTN1", "BTN2", "BTN3") and layer == F:
            if nearly(y1, 103.60, 0.12) and nearly(y2, 103.60, 0.12) and max(x1, x2) > 105:
                return True
            # BTN3 old path through U2
            if net == "BTN3" and nearly(x1, 111.8, 0.15) and nearly(x2, 111.8, 0.15):
                if min(y1, y2) < 107:
                    return True
            if net == "BTN3" and nearly(y1, 103.60, 0.15) and max(x1, x2) > 105:
                return True

        # 3V3 F.Cu long west spine at y=102.2 into J_SWD — crosses many nets;
        # keep B.Cu path; delete F portion west of x=94
        if net == "3V3" and layer == F:
            if nearly(y1, 102.2, 0.15) and nearly(y2, 102.2, 0.15) and min(x1, x2) < 90:
                return True
            # vertical 3V3 at x=102.5 down through buttons
            if nearly(x1, 102.5, 0.1) and nearly(x2, 102.5, 0.1) and max(y1, y2) > 105:
                return True

        # 3V3_DISP F.Cu right spine that crosses GND at FPC R
        if net == "3V3_DISP" and layer == F:
            # duplicate short stubs
            if nearly(y1, 106.0, 0.1) and nearly(y2, 106.0, 0.1) and min(x1, x2) >= 111.8:
                if abs(x1 - x2) > 2.0 and pcbnew.ToMM(t.GetWidth()) < 0.35:
                    return True  # thin duplicate of 0.45
            # north-going vertical into display that crosses GND stubs — keep B path
            if nearly(x1, 115.55, 0.1) and nearly(x2, 115.55, 0.1) and min(y1, y2) < 95:
                return True

        return False

    delete_tracks(board, is_dangerous, "dangerous shorts")

    # Remove via-in-pad under pogo TP* (IP67 P2/P3) — connectivity via F.Cu tracks only
    def is_pogo_via_in_pad(t):
        if t.GetClass() != "PCB_VIA":
            return False
        x, y = endpoints(t)[0]
        # Exact TP centers
        tps = [
            (93.0, 114.0),
            (96.0, 114.0),
            (99.0, 114.0),
            (93.0, 111.0),
            (96.0, 111.0),
            (99.0, 111.0),
        ]
        for tx, ty in tps:
            if math.hypot(x - tx, y - ty) < 0.35:
                return True
        return False

    delete_tracks(board, is_pogo_via_in_pad, "pogo via-in-pad")

    # Delete dangling/orphan vias that only connected deleted tracks near seal (optional careful)
    # Keep GND stitch vias outside seal.

    # ------------------------------------------------------------------
    # 4) Move SW2/SW3 away from U2 courtyard for passives room
    # ------------------------------------------------------------------
    sw2 = find_fp(board, "SW2")
    sw3 = find_fp(board, "SW3")
    # New positions: east-south of U2, inside Ø40 (edge ~119.5 at equator but south smaller)
    sw3.SetPosition(pcbnew.VECTOR2I(mm(116.5), mm(108.0)))
    sw2.SetPosition(pcbnew.VECTOR2I(mm(114.5), mm(111.0)))
    print("moved SW2→(114.5,111) SW3→(116.5,108)")

    # Delete remaining BTN tracks (will re-route)
    delete_tracks(
        board,
        lambda t: t.GetClass() != "PCB_VIA" and t.GetNetname() in ("BTN1", "BTN2", "BTN3"),
        "all BTN tracks",
    )

    # Re-route buttons clear of U2 / power
    # U1 pads: BTN1=61, BTN2=50, BTN3=60 — use existing escape stubs if any remain;
    # fanout used approximate coordinates from module east/south.
    # From prior: BTN1 from (98,92.95), BTN2 (96.25,94.95), BTN3 (98.8,92.95)
    # Route south on B.Cu then to switches on F.
    # Find U1 pad numbers for buttons
    u1 = find_fp(board, "U1")
    btn_pads = {}
    for p in u1.Pads():
        if p.GetNetname() in ("BTN1", "BTN2", "BTN3"):
            btn_pads[p.GetNetname()] = (
                pcbnew.ToMM(p.GetPosition().x),
                pcbnew.ToMM(p.GetPosition().y),
            )
    print("BTN pads", btn_pads)

    # BTN1 → SW1
    if "BTN1" in btn_pads:
        x0, y0 = btn_pads["BTN1"]
        add_via(board, x0, y0 + 0.9, "BTN1")
        poly(board, [(x0, y0), (x0, y0 + 0.9)], W_SIG, F, "BTN1")
        poly(
            board,
            [(x0, y0 + 0.9), (x0, 110.5), (107.5, 110.5)],
            W_SIG,
            B,
            "BTN1",
        )
        add_via(board, 107.5, 110.5, "BTN1")
        sw1p = pad_xy(board, "SW1", "1")
        poly(board, [(107.5, 110.5), (107.5, sw1p[1]), sw1p], W_SIG, F, "BTN1")

    # BTN2 → SW2
    if "BTN2" in btn_pads:
        x0, y0 = btn_pads["BTN2"]
        add_via(board, x0 - 0.8, y0 + 0.8, "BTN2")
        poly(board, [(x0, y0), (x0 - 0.8, y0), (x0 - 0.8, y0 + 0.8)], W_SIG, F, "BTN2")
        poly(
            board,
            [(x0 - 0.8, y0 + 0.8), (x0 - 0.8, 111.5), (112.8, 111.5)],
            W_SIG,
            B,
            "BTN2",
        )
        add_via(board, 112.8, 111.5, "BTN2")
        sw2p = pad_xy(board, "SW2", "1")
        poly(board, [(112.8, 111.5), sw2p], W_SIG, F, "BTN2")

    # BTN3 → SW3 (south of U2 on B, avoid BGA)
    if "BTN3" in btn_pads:
        x0, y0 = btn_pads["BTN3"]
        add_via(board, x0 + 0.9, y0 + 0.9, "BTN3")
        poly(board, [(x0, y0), (x0 + 0.9, y0), (x0 + 0.9, y0 + 0.9)], W_SIG, F, "BTN3")
        poly(
            board,
            [(x0 + 0.9, y0 + 0.9), (x0 + 0.9, 109.5), (114.8, 109.5)],
            W_SIG,
            B,
            "BTN3",
        )
        add_via(board, 114.8, 109.5, "BTN3")
        sw3p = pad_xy(board, "SW3", "1")
        poly(board, [(114.8, 109.5), (114.8, sw3p[1]), sw3p], W_SIG, F, "BTN3")

    # ------------------------------------------------------------------
    # 5) Repair power after deletions
    # ------------------------------------------------------------------
    # 3V3: pad28↔30 only on F, escape via B (keep existing B spine if present)
    p28 = pad_xy(board, "U1", "28")
    p30 = pad_xy(board, "U1", "30")
    add_track(board, p28[0], p28[1], p30[0], p30[1], W_NECK + 0.05, F, "3V3")
    # local escapes to existing vias at (97,87.5) and (106,87.5) if still there
    add_track(board, p30[0], p30[1], 97.0, p30[1], 0.30, F, "3V3")
    add_track(board, 97.0, p30[1], 97.0, 87.5, 0.30, F, "3V3")
    # east escape: only to via, NOT along pad row
    add_track(board, p28[0], p28[1], p28[0], 87.5, 0.30, F, "3V3")
    add_track(board, p28[0], 87.5, 106.0, 87.5, 0.35, F, "3V3")

    # VSYS: short escape north to R_VSYS only
    b5 = pad_xy(board, "U2", "B5")
    b4 = pad_xy(board, "U2", "B4")
    c4 = pad_xy(board, "U2", "C4")
    poly(board, [b5, b4, c4], W_NECK, F, "VSYS")
    poly(board, [b5, (b5[0], 104.4), (107.5, 104.4), (107.5, 104.625)], W_PWR, F, "VSYS")

    # VBAT: B1-B2 + south then west corridor SOUTH of U2 but NORTH of buttons, clear of seal
    b1 = pad_xy(board, "U2", "B1")
    b2 = pad_xy(board, "U2", "B2")
    poly(board, [b1, b2], W_NECK, F, "VBAT")
    # go west at y=107.8 then down at x=100 to J_BAT — avoid pogo seal vias
    poly(
        board,
        [b1, (b1[0], 107.9), (100.0, 107.9), (100.0, 113.8), (100.0, 115.8)],
        W_FAT,
        F,
        "VBAT",
    )
    # also to J_BAT pin if needed
    add_via(board, 100.0, 107.9, "VBAT")  # outside seal (y=107.9 < 108.5)

    # VBUS: TP1 → corridor y=112.2 → U2.A2 ; no via on TP1
    a2 = pad_xy(board, "U2", "A2")
    poly(
        board,
        [(93.0, 114.0), (93.0, 112.2), (110.6, 112.2), (110.6, a2[1]), a2],
        W_FAT,
        F,
        "VBUS",
    )
    # stitch via outside seal
    add_via(board, 104.0, 112.2, "VBUS")

    # 3V3_DISP from C5: short F escape + B star (repair after deletes)
    c5 = pad_xy(board, "U2", "C5")
    add_track(board, c5[0], c5[1], 113.0, c5[1], W_PWR, F, "3V3_DISP")
    add_via(board, 113.0, c5[1], "3V3_DISP")
    # B corridor west under module to existing vias
    poly(board, [(113.0, c5[1]), (104.0, 105.2), (96.0, 105.2)], W_PWR, B, "3V3_DISP")

    # GND: rely on zones; add short ties at U2 GND pads only
    a1 = pad_xy(board, "U2", "A1")
    a5 = pad_xy(board, "U2", "A5")
    d5 = pad_xy(board, "U2", "D5")
    poly(board, [a1, a5], W_NECK, F, "GND")
    poly(board, [a5, d5], W_NECK, F, "GND")
    add_via(board, 109.2, 104.5, "GND")  # outside U2, outside seal
    poly(board, [a1, (109.2, a1[1]), (109.2, 104.5)], 0.35, F, "GND")

    # ------------------------------------------------------------------
    # 6) Place BQ25120A passives + I2C pull-ups near U2
    # Datasheet-typical (TI DS + checklist), 0402, account DC bias:
    #   CIN≥1µF, CPMID≥3µF eff → 4.7µF, CSYS≥4.7µF eff → 10µF,
    #   CBAT≥1µF, CVINLS≥1µF (VINLS≡VSYS on this board), CLDO≥1µF
    # Trace stubs to caps: Power 0.35–0.45 (IR negligible at mm scale)
    # ------------------------------------------------------------------
    placements = [
        # ref, value, lib, fp, x, y, rot, net1, net2
        ("C_IN", "1uF", "Capacitor_SMD", "C_0402_1005Metric", 108.6, 104.5, 0, "VBUS", "GND"),
        ("C_PMID", "4.7uF", "Capacitor_SMD", "C_0402_1005Metric", 111.0, 103.9, 0, "PMID", "GND"),
        ("C_SYS", "10uF", "Capacitor_SMD", "C_0402_1005Metric", 113.5, 104.8, 90, "VSYS", "GND"),
        ("C_BAT", "1uF", "Capacitor_SMD", "C_0402_1005Metric", 108.6, 105.8, 0, "VBAT", "GND"),
        ("C_VINLS", "1uF", "Capacitor_SMD", "C_0402_1005Metric", 113.5, 105.8, 90, "VSYS", "GND"),
        ("C_LDO", "1uF", "Capacitor_SMD", "C_0402_1005Metric", 113.5, 106.8, 90, "3V3_DISP", "GND"),
        ("R_SDA", "4.7k", "Resistor_SMD", "R_0402_1005Metric", 109.5, 107.6, 0, "SDA", "3V3"),
        ("R_SCL", "4.7k", "Resistor_SMD", "R_0402_1005Metric", 111.5, 107.6, 0, "SCL", "3V3"),
    ]

    placed = {}
    for ref, value, lib, fpname, x, y, rot, n1, n2 in placements:
        # skip if already exists
        try:
            find_fp(board, ref)
            print("exists", ref)
            continue
        except KeyError:
            pass
        fp = load_fp(board, lib, fpname, ref, value, x, y, rot)
        wire_two_pad(board, fp, n1, n2)
        placed[ref] = (fp, n1, n2, x, y, rot)
        print(f"placed {ref}={value} @ ({x},{y}) r{rot} {n1}/{n2}")

    # Route passives with short stubs (physics: ESL ∝ loop area — keep <2 mm)
    def pad_centers(fp):
        out = {}
        for p in fp.Pads():
            out[p.GetNumber()] = (
                pcbnew.ToMM(p.GetPosition().x),
                pcbnew.ToMM(p.GetPosition().y),
            )
        return out

    # C_IN: pad1 VBUS ↔ A2, pad2 GND
    if "C_IN" in placed:
        fp = placed["C_IN"][0]
        pc = pad_centers(fp)
        add_track(board, pc["1"][0], pc["1"][1], a2[0], a2[1], 0.35, F, "VBUS")
        add_track(board, pc["2"][0], pc["2"][1], a1[0], a1[1], 0.35, F, "GND")

    # C_PMID
    if "C_PMID" in placed:
        fp = placed["C_PMID"][0]
        pc = pad_centers(fp)
        a3 = pad_xy(board, "U2", "A3")
        add_track(board, pc["1"][0], pc["1"][1], a3[0], a3[1], 0.35, F, "PMID")
        add_track(board, pc["2"][0], pc["2"][1], a1[0], pc["2"][1], 0.35, F, "GND")
        add_track(board, a1[0], pc["2"][1], a1[0], a1[1], 0.35, F, "GND")

    # C_SYS (rot90: pad1 toward package)
    if "C_SYS" in placed:
        fp = placed["C_SYS"][0]
        pc = pad_centers(fp)
        # determine which pad is closer to B5
        d1 = math.hypot(pc["1"][0] - b5[0], pc["1"][1] - b5[1])
        d2 = math.hypot(pc["2"][0] - b5[0], pc["2"][1] - b5[1])
        p_sys, p_gnd = ("1", "2") if d1 < d2 else ("2", "1")
        # fix nets if orientation swapped
        for p in fp.Pads():
            if p.GetNumber() == p_sys:
                p.SetNetCode(netcode(board, "VSYS"))
            else:
                p.SetNetCode(netcode(board, "GND"))
        add_track(board, pc[p_sys][0], pc[p_sys][1], b5[0], b5[1], 0.35, F, "VSYS")
        add_track(board, pc[p_gnd][0], pc[p_gnd][1], a5[0], a5[1], 0.35, F, "GND")

    # C_BAT
    if "C_BAT" in placed:
        fp = placed["C_BAT"][0]
        pc = pad_centers(fp)
        add_track(board, pc["1"][0], pc["1"][1], b1[0], b1[1], 0.35, F, "VBAT")
        add_track(board, pc["2"][0], pc["2"][1], a1[0], a1[1], 0.35, F, "GND")

    # C_VINLS (on VSYS near C4)
    if "C_VINLS" in placed:
        fp = placed["C_VINLS"][0]
        pc = pad_centers(fp)
        d1 = math.hypot(pc["1"][0] - c4[0], pc["1"][1] - c4[1])
        d2 = math.hypot(pc["2"][0] - c4[0], pc["2"][1] - c4[1])
        p_v, p_g = ("1", "2") if d1 < d2 else ("2", "1")
        for p in fp.Pads():
            if p.GetNumber() == p_v:
                p.SetNetCode(netcode(board, "VSYS"))
            else:
                p.SetNetCode(netcode(board, "GND"))
        add_track(board, pc[p_v][0], pc[p_v][1], c4[0], c4[1], 0.30, F, "VSYS")
        add_track(board, pc[p_g][0], pc[p_g][1], a5[0], pc[p_g][1], 0.30, F, "GND")
        add_track(board, a5[0], pc[p_g][1], a5[0], a5[1], 0.30, F, "GND")

    # C_LDO on 3V3_DISP
    if "C_LDO" in placed:
        fp = placed["C_LDO"][0]
        pc = pad_centers(fp)
        d1 = math.hypot(pc["1"][0] - c5[0], pc["1"][1] - c5[1])
        d2 = math.hypot(pc["2"][0] - c5[0], pc["2"][1] - c5[1])
        p_v, p_g = ("1", "2") if d1 < d2 else ("2", "1")
        for p in fp.Pads():
            if p.GetNumber() == p_v:
                p.SetNetCode(netcode(board, "3V3_DISP"))
            else:
                p.SetNetCode(netcode(board, "GND"))
        add_track(board, pc[p_v][0], pc[p_v][1], c5[0], c5[1], 0.30, F, "3V3_DISP")
        add_track(board, pc[p_g][0], pc[p_g][1], d5[0], d5[1], 0.30, F, "GND")

    # I2C pull-ups to 3V3
    e4 = pad_xy(board, "U2", "E4")
    e5 = pad_xy(board, "U2", "E5")
    if "R_SDA" in placed:
        fp = placed["R_SDA"][0]
        pc = pad_centers(fp)
        # pad1 SDA, pad2 3V3
        add_track(board, pc["1"][0], pc["1"][1], e4[0], e4[1], W_SIG, F, "SDA")
        # 3V3: via to B spine or short to nearby 3V3
        add_track(board, pc["2"][0], pc["2"][1], pc["2"][0], 103.35, W_SIG, F, "3V3")
        add_track(board, pc["2"][0], 103.35, 107.5, 103.35, 0.30, F, "3V3")
    if "R_SCL" in placed:
        fp = placed["R_SCL"][0]
        pc = pad_centers(fp)
        add_track(board, pc["1"][0], pc["1"][1], e5[0], e5[1], W_SIG, F, "SCL")
        add_track(board, pc["2"][0], pc["2"][1], pc["2"][0], 103.35, W_SIG, F, "3V3")
        add_track(board, pc["2"][0], 103.35, 107.5, 103.35, 0.30, F, "3V3")

    # ------------------------------------------------------------------
    # 7) Secondary geometric cleanup: delete remaining F.Cu crossings
    # ------------------------------------------------------------------
    def orient(p, q, r):
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    def segments_cross(a, b, c, d):
        o1, o2 = orient(a, b, c), orient(a, b, d)
        o3, o4 = orient(c, d, a), orient(c, d, b)
        if o1 * o2 < 0 and o3 * o4 < 0:
            return True
        return False

    # Priority: delete GND track if it crosses a non-GND track (zones handle GND)
    # Also delete lower-priority signal if two signals cross on same layer
    priority = {
        "GND": 0,
        "3V3": 10,
        "3V3_DISP": 10,
        "VBUS": 12,
        "VBAT": 12,
        "VSYS": 12,
        "PMID": 12,
        "SDA": 20,
        "SCL": 20,
        "PMIC_INT": 20,
        "SWDIO": 15,
        "SWDCLK": 15,
        "nRESET": 15,
        "SWDIO_POGO": 15,
        "SWDCLK_POGO": 15,
        "nRESET_POGO": 15,
        "BTN1": 25,
        "BTN2": 25,
        "BTN3": 25,
    }

    def net_prio(n):
        if n.startswith("EPD_"):
            return 18
        return priority.get(n, 22)

    changed = True
    rounds = 0
    while changed and rounds < 8:
        changed = False
        rounds += 1
        tracks = []
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                continue
            a, b = endpoints(t)
            tracks.append((t, t.GetNetname(), t.GetLayer(), a, b))
        doomed = set()
        for i in range(len(tracks)):
            if id(tracks[i][0]) in doomed:
                continue
            for j in range(i + 1, len(tracks)):
                if id(tracks[j][0]) in doomed:
                    continue
                ti, ni, li, ai, bi = tracks[i]
                tj, nj, lj, aj, bj = tracks[j]
                if li != lj or ni == nj:
                    continue
                if not segments_cross(ai, bi, aj, bj):
                    continue
                # delete lower priority (GND first)
                if net_prio(ni) < net_prio(nj):
                    doomed.add(id(ti))
                elif net_prio(nj) < net_prio(ni):
                    doomed.add(id(tj))
                else:
                    # same class: delete shorter
                    if seg_len(ai, bi) <= seg_len(aj, bj):
                        doomed.add(id(ti))
                    else:
                        doomed.add(id(tj))
        for t, *_ in tracks:
            if id(t) in doomed:
                board.Delete(t)
                changed = True
        print(f"cross-cleanup round {rounds}: deleted {len(doomed)}")

    # ------------------------------------------------------------------
    # 8) Ensure IP67 note still present; add seal keepout reminder
    # ------------------------------------------------------------------
    has_ip67 = False
    for d in board.GetDrawings():
        try:
            if "IP67" in d.GetText():
                has_ip67 = True
        except Exception:
            pass
    if not has_ip67:
        txt = pcbnew.PCB_TEXT(board)
        txt.SetText(
            "IP67: no seal-land copper ring on PCB — gasket keepout is mechanical (case); "
            "keep pogo 2x3@3mm clear of seal boss; NO NEW VIAS in pogo seal land"
        )
        txt.SetPosition(pcbnew.VECTOR2I(mm(100), mm(121)))
        txt.SetLayer(pcbnew.Dwgs_User)
        txt.SetTextSize(pcbnew.VECTOR2I(mm(0.7), mm(0.7)))
        board.Add(txt)

    # Dwgs outline of seal keepout (rectangle)
    def add_line(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        s.SetLayer(pcbnew.Dwgs_User)
        s.SetWidth(mm(0.1))
        board.Add(s)

    xs, xe = POGO_SEAL["xmin"], POGO_SEAL["xmax"]
    ys, ye = POGO_SEAL["ymin"], POGO_SEAL["ymax"]
    add_line(xs, ys, xe, ys)
    add_line(xe, ys, xe, ye)
    add_line(xe, ye, xs, ye)
    add_line(xs, ye, xs, ys)

    # ------------------------------------------------------------------
    # 9) Fill zones + save
    # ------------------------------------------------------------------
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(PCB), board)
    print("saved", PCB)

    # summary refs
    refs = sorted(fp.GetReference() for fp in board.GetFootprints())
    print("refs:", refs)


if __name__ == "__main__":
    main()
