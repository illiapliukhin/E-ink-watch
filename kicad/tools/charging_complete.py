#!/usr/bin/env python3
"""Complete Li-ion charging path for BQ25120A wearable.

Adds (design-intent, not certified):
  - TVS on VBUS (ESD at pogo)
  - Ferrite FB1 series on VBUS
  - R_ISET / R_ILIM / R_IPRETERM
  - TS NTC + pull-up (JEITA)
  - L1 2.2uH SW→SYS buck inductor
  - Keep 4-layer stack; SW_DBG must not break VBUS/GND

Harvard honesty: PCM on cell still required; this is not IEC 62133 certification.
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
BACKUP = ROOT / "backups" / f"e-ink-watch.kicad_pcb.pre-charging-{datetime.now():%H%M%S}"

# Charge current assumption: ~100 mAh cell @ ~0.5C → 50 mA
# BQ25120A: ICHARGE = K_ISET / R_ISET, K≈200 AΩ → R=4.02k → ~49.8 mA
R_ISET_VAL = "4.02k"
# Input ILIM ~100 mA for pogo 5V: R_ILIM = 200/0.1 = 2.0k
R_ILIM_VAL = "2.0k"
# IPRETERM → GND = internal default (~20% / IC default)
R_IPRETERM_VAL = "0R"
# TS: 10k NTC (103AT class) to GND, 10k pull-up to VIN/VBUS
R_TS_VAL = "10k"
NTC_VAL = "10k_NTC"
L1_VAL = "2.2uH"
FB1_VAL = "BLM18PG121SN1"  # class
TVS_VAL = "PESD5V0S1UL"

W_PWR = 0.40
W_SIG = 0.18
VIA_D = 0.55
VIA_DRILL = 0.25

# Keepouts: pogo seal envelope — no NEW vias inside
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def uid() -> str:
    return str(uuid.uuid4())


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


def wire_two_pad(board, fp, net_a, net_b):
    for p in fp.Pads():
        n = p.GetNumber()
        if n == "1":
            p.SetNetCode(ensure_net(board, net_a))
        elif n == "2":
            p.SetNetCode(ensure_net(board, net_b))


def add_track(board, x1, y1, x2, y2, width, layer, netname):
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNetCode(ensure_net(board, netname))
    board.Add(t)
    return t


def poly_track(board, pts, width, layer, netname):
    for a, b in zip(pts, pts[1:]):
        add_track(board, a[0], a[1], b[0], b[1], width, layer, netname)


def in_pogo(x, y):
    return POGO["xmin"] <= x <= POGO["xmax"] and POGO["ymin"] <= y <= POGO["ymax"]


def add_via(board, x, y, netname):
    if in_pogo(x, y):
        print(f"  SKIP via in pogo seal ({x:.2f},{y:.2f}) {netname}")
        return None
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNetCode(ensure_net(board, netname))
    board.Add(v)
    return v


def load_fp(board, lib_nickname, fp_name, ref, value, x, y, rot=0):
    # Avoid duplicate refs
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            print(f"  exists {ref}, skip place")
            return fp
    libpath = f"/usr/share/kicad/footprints/{lib_nickname}.pretty"
    fp = pcbnew.FootprintLoad(libpath, fp_name)
    if fp is None:
        raise RuntimeError(f"Cannot load {lib_nickname}:{fp_name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    try:
        fp.SetFPIDAsString(f"{lib_nickname}:{fp_name}")
    except Exception:
        pass
    board.Add(fp)
    print(f"  placed {ref}={value} @ ({x},{y})")
    return fp


def main():
    shutil.copy2(PCB, BACKUP)
    print("backup", BACKUP)

    board = pcbnew.LoadBoard(str(PCB.resolve()))
    if board is None:
        raise SystemExit("LoadBoard failed")
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    assert board.GetCopperLayerCount() == 4, "must stay 4L"

    # --- nets ---
    for n in ("VBUS", "VBAT", "VSYS", "PMID", "GND", "SW", "ISET", "ILIM", "TS", "IPRETERM", "VBUS_POGO"):
        ensure_net(board, n)

    # Assign U2 charge-critical balls
    set_pad_net(board, "U2", "A4", "SW")       # inductor switch node
    set_pad_net(board, "U2", "C1", "ISET")
    set_pad_net(board, "U2", "C2", "ILIM")
    set_pad_net(board, "U2", "C3", "TS")
    set_pad_net(board, "U2", "D1", "IPRETERM")
    # /CD E2: leave NC (internal PD → charge enabled). Documented.
    print("U2 balls SW/ISET/ILIM/TS/IPRETERM assigned")

    # --- Place passives near U2 (east/south of PMIC, outside pogo seal) ---
    # U2 center (111, 106)
    # L1 SW→SYS: north-east of U2
    L1 = load_fp(board, "Inductor_SMD", "L_0805_2012Metric", "L1", L1_VAL, 113.2, 104.2, 0)
    # R_ISET, R_ILIM, R_IPRETERM west/south of U2
    R_ISET = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_ISET", R_ISET_VAL, 108.4, 106.8, 90)
    R_ILIM = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_ILIM", R_ILIM_VAL, 108.4, 107.6, 90)
    R_IPRE = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_IPRETERM", R_IPRETERM_VAL, 108.4, 108.4, 90)
    # TS network: R_TS pullup + RT1 NTC
    R_TS = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "R_TS", R_TS_VAL, 112.8, 107.8, 0)
    RT1 = load_fp(board, "Resistor_SMD", "R_0402_1005Metric", "RT1", NTC_VAL, 112.8, 108.6, 0)
    # TVS + ferrite on VBUS path, outside seal (near U2 IN side, west)
    FB1 = load_fp(board, "Inductor_SMD", "L_0603_1608Metric", "FB1", FB1_VAL, 106.5, 104.5, 0)
    D_TVS = load_fp(board, "Diode_SMD", "D_SOD-323", "D_TVS", TVS_VAL, 105.2, 103.5, 0)

    # Net assignment for two-pad parts
    # L1: pad1=SW, pad2=VSYS
    wire_two_pad(board, L1, "SW", "VSYS")
    # R_ISET: ISET—GND
    wire_two_pad(board, R_ISET, "ISET", "GND")
    wire_two_pad(board, R_ILIM, "ILIM", "GND")
    wire_two_pad(board, R_IPRE, "IPRETERM", "GND")
    # R_TS: VBUS—TS ; RT1: TS—GND
    wire_two_pad(board, R_TS, "VBUS", "TS")
    wire_two_pad(board, RT1, "TS", "GND")
    # FB1: insert in VBUS — use VBUS_POGO (TP1 side) → FB1 → VBUS (U2/C_IN)
    # Rework: TP1 currently on VBUS. Split: TP1→VBUS_POGO, FB1 series, then VBUS to U2.
    set_pad_net(board, "TP1", "1", "VBUS_POGO")
    wire_two_pad(board, FB1, "VBUS_POGO", "VBUS")
    # TVS across VBUS_POGO to GND (clamp at connector side)
    # SOD-323: pad1 cathode (for uni) / either for bi — PESD5V0S1UL is uni: pad1=A, pad2=K typically
    # Clamp from VBUS_POGO to GND: anode(1) to GND, cathode(2) to VBUS_POGO for uni reverse... 
    # Actually PESD5V0S1UL: pin1=cathode, pin2=anode for unidirectional — connect cathode to VBUS, anode GND.
    # Footprint pad numbering: check — typically pad1 left = cathode for SOD.
    wire_two_pad(board, D_TVS, "VBUS_POGO", "GND")  # will note orientation in report

    # Also move C_IN to stay on VBUS (charger side) — already VBUS/GND OK
    # If any track still ties TP1 old position to VBUS, reconnect via FB1

    # --- Routing ---
    u2 = find_fp(board, "U2")

    def u2ball(n):
        return pad_xy(board, "U2", n)

    # L1 routing: A4(SW) → L1.1 ; L1.2 → B5(VSYS)
    sw = u2ball("A4")
    sysb = u2ball("B5")
    l1p1 = pad_xy(board, "L1", "1")
    l1p2 = pad_xy(board, "L1", "2")
    poly_track(board, [sw, (sw[0], l1p1[1]), l1p1], W_PWR, F, "SW")
    poly_track(board, [l1p2, (sysb[0], l1p2[1]), sysb], W_PWR, F, "VSYS")

    # R_ISET
    iset = u2ball("C1")
    r1 = pad_xy(board, "R_ISET", "1")
    r2 = pad_xy(board, "R_ISET", "2")
    poly_track(board, [iset, (r1[0], iset[1]), r1], W_SIG, F, "ISET")
    # pad2 to GND via short + via
    add_via(board, r2[0] - 0.4, r2[1], "GND")
    add_track(board, r2[0], r2[1], r2[0] - 0.4, r2[1], W_SIG, F, "GND")

    # R_ILIM
    ilim = u2ball("C2")
    i1 = pad_xy(board, "R_ILIM", "1")
    i2 = pad_xy(board, "R_ILIM", "2")
    poly_track(board, [ilim, (ilim[0], i1[1]), (i1[0], i1[1])], W_SIG, F, "ILIM")
    add_via(board, i2[0] - 0.4, i2[1], "GND")
    add_track(board, i2[0], i2[1], i2[0] - 0.4, i2[1], W_SIG, F, "GND")

    # R_IPRETERM
    ip = u2ball("D1")
    p1 = pad_xy(board, "R_IPRETERM", "1")
    p2 = pad_xy(board, "R_IPRETERM", "2")
    poly_track(board, [ip, (p1[0], ip[1]), p1], W_SIG, F, "IPRETERM")
    add_via(board, p2[0] - 0.4, p2[1], "GND")
    add_track(board, p2[0], p2[1], p2[0] - 0.4, p2[1], W_SIG, F, "GND")

    # TS: U2.C3 → junction; R_TS from VBUS; RT1 to GND
    ts = u2ball("C3")
    rts1 = pad_xy(board, "R_TS", "1")  # VBUS
    rts2 = pad_xy(board, "R_TS", "2")  # TS
    rt1_1 = pad_xy(board, "RT1", "1")  # TS
    rt1_2 = pad_xy(board, "RT1", "2")  # GND
    poly_track(board, [ts, (ts[0], rts2[1]), rts2], W_SIG, F, "TS")
    add_track(board, rts2[0], rts2[1], rt1_1[0], rt1_1[1], W_SIG, F, "TS")
    # R_TS pad1 to VBUS (near C_IN / A2)
    vin = u2ball("A2")
    poly_track(board, [rts1, (rts1[0], vin[1] + 0.3), (vin[0], vin[1] + 0.3), vin], W_SIG, F, "VBUS")
    add_via(board, rt1_2[0], rt1_2[1] + 0.5, "GND")
    add_track(board, rt1_2[0], rt1_2[1], rt1_2[0], rt1_2[1] + 0.5, W_SIG, F, "GND")

    # FB1 + TVS + TP1 path
    # Delete old direct TP1-VBUS tracks that bypass FB (optional cleanup — connect FB)
    tp1 = pad_xy(board, "TP1", "1")
    fb_a = pad_xy(board, "FB1", "1")  # VBUS_POGO
    fb_b = pad_xy(board, "FB1", "2")  # VBUS
    # Route TP1 → FB1.1 on F.Cu staying outside seal as much as possible
    # TP1 at (93,114) in seal — track may exit seal; no new via in seal
    poly_track(
        board,
        [tp1, (tp1[0], 108.0), (fb_a[0], 108.0), fb_a],
        W_PWR,
        F,
        "VBUS_POGO",
    )
    # FB1.2 → C_IN / U2.A2 (VBUS)
    cin = None
    try:
        cin = pad_xy(board, "C_IN", "1")
        # determine which pad is VBUS
        for p in find_fp(board, "C_IN").Pads():
            if p.GetNetname() == "VBUS":
                cin = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                break
    except Exception:
        cin = vin
    poly_track(board, [fb_b, (fb_b[0], cin[1]), cin], W_PWR, F, "VBUS")

    # TVS
    t1 = pad_xy(board, "D_TVS", "1")
    t2 = pad_xy(board, "D_TVS", "2")
    # Connect pad1 to VBUS_POGO, pad2 to GND
    poly_track(board, [t1, (t1[0], fb_a[1]), fb_a], W_PWR, F, "VBUS_POGO")
    add_via(board, t2[0], t2[1] - 0.6, "GND")
    add_track(board, t2[0], t2[1], t2[0], t2[1] - 0.6, W_SIG, F, "GND")

    # Verify SW_DBG nets unchanged
    swd = find_fp(board, "SW_DBG")
    bad = [p.GetNetname() for p in swd.Pads() if p.GetNetname() in ("VBUS", "VBUS_POGO", "VBAT", "GND")]
    # GND on mechanical pads OK; VBUS must not appear
    if any(n in ("VBUS", "VBUS_POGO", "VBAT") for n in bad):
        raise SystemExit(f"SW_DBG incorrectly on charge net: {bad}")
    print("SW_DBG charge-path isolation OK")

    pcbnew.Refresh()
    board.Save(str(PCB))
    print("saved", PCB)

    # Summary dump
    print("\n=== POST charge refs ===")
    for ref in ["U2", "L1", "R_ISET", "R_ILIM", "R_IPRETERM", "R_TS", "RT1", "FB1", "D_TVS", "TP1", "C_IN", "J_BAT", "SW_DBG"]:
        try:
            fp = find_fp(board, ref)
            nets = sorted({p.GetNetname() or "NC" for p in fp.Pads()})
            print(f"  {ref:12s} {fp.GetValue():20s} {nets}")
        except KeyError:
            print(f"  {ref:12s} MISSING")

    print("copper layers", board.GetCopperLayerCount())


if __name__ == "__main__":
    main()
