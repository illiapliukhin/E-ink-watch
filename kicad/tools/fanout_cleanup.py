#!/usr/bin/env python3
"""Post-fanout cleanup: B.Cu GND, remaining unconnected, worst shorts."""
from __future__ import annotations

import math
from pathlib import Path

import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def main() -> None:
    board = pcbnew.LoadBoard(str(PCB))
    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    def netcode(name: str) -> int:
        return board.GetNetInfo().GetNetItem(name).GetNetCode()

    def add_track(x1, y1, x2, y2, w, layer, net):
        if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
            return
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNetCode(netcode(net))
        board.Add(t)

    def add_via(x, y, net):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        try:
            v.SetWidth(pcbnew.F_Cu, mm(0.6))
        except TypeError:
            pass
        v.SetDrill(mm(0.3))
        v.SetNetCode(netcode(net))
        board.Add(v)

    def poly(pts, w, layer, net):
        for a, b in zip(pts, pts[1:]):
            add_track(a[0], a[1], b[0], b[1], w, layer, net)

    def endpoints(t):
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            return [(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))]
        a, b = t.GetStart(), t.GetEnd()
        return [
            (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)),
            (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)),
        ]

    # --- Convert duplicate F.Cu GND zone to B.Cu if present ---
    gnd_zones = [
        z
        for z in board.Zones()
        if (not z.GetIsRuleArea()) and z.GetNetname() == "GND"
    ]
    print("GND zones:", len(gnd_zones))
    if len(gnd_zones) >= 2:
        # Keep first, set second to B.Cu
        gnd_zones[1].SetLayer(B)
        print("set second GND zone → B.Cu")
    elif len(gnd_zones) == 1:
        z = pcbnew.ZONE(board)
        z.SetNetCode(netcode("GND"))
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

    # --- Remaining unconnected stitches ---
    poly([(108.0, 110.0), (108.0, 112.2), (110.6, 112.2)], 0.50, F, "VBUS")

    add_via(111.5, 105.2, "3V3_DISP")
    poly([(111.8, 106.0), (111.5, 106.0), (111.5, 105.2)], 0.45, F, "3V3_DISP")
    poly([(111.5, 105.2), (104.0, 105.2)], 0.45, B, "3V3_DISP")
    poly([(92.0, 105.5), (84.45, 105.5), (84.45, 108.5)], 0.45, B, "3V3_DISP")

    poly([(86.4, 96.35), (86.4, 98.75), (81.95, 98.75)], 0.45, F, "GND")
    add_via(86.4, 97.5, "GND")
    poly([(115.2, 105.5), (115.2, 104.65), (113.6, 104.65)], 0.45, F, "GND")
    poly([(113.6, 104.65), (110.2, 104.65), (110.2, 105.2)], 0.45, F, "GND")
    add_via(113.6, 104.65, "GND")

    # --- BTN3 clear of U2 ---
    doomed = []
    for t in list(board.GetTracks()):
        if t.GetNetname() != "BTN3" or t.GetClass() == "PCB_VIA":
            continue
        (x1, y1), (x2, y2) = endpoints(t)
        if abs(y1 - 105.5) < 0.08 and abs(y2 - 105.5) < 0.08 and max(x1, x2) > 108:
            doomed.append(t)
        if abs(x1 - 108.4) < 0.08 and abs(x2 - 108.4) < 0.08 and max(y1, y2) > 104:
            doomed.append(t)
    for t in doomed:
        board.Delete(t)
    print("BTN3 deleted", len(doomed))
    poly([(102.75, 103.6), (102.75, 107.8), (111.8, 107.8), (111.8, 105.5)], 0.18, F, "BTN3")

    # --- 3V3 escape via B.Cu (avoid y=85.6 F collision with SPI) ---
    doomed = []
    for t in list(board.GetTracks()):
        if t.GetNetname() != "3V3" or t.GetClass() == "PCB_VIA":
            continue
        pts = endpoints(t)
        if len(pts) < 2:
            continue
        (x1, y1), (x2, y2) = pts
        if abs(y1 - 85.6) < 0.08 and abs(y2 - 85.6) < 0.08:
            doomed.append(t)
        elif (abs(y1 - 86.35) < 0.15 and abs(y2 - 85.6) < 0.08) or (
            abs(y2 - 86.35) < 0.15 and abs(y1 - 85.6) < 0.08
        ):
            doomed.append(t)
        # also remove F.Cu long spines we added south at x=93.5 / 106 on F
        elif abs(x1 - 93.5) < 0.08 and abs(x2 - 93.5) < 0.08 and min(y1, y2) < 90:
            doomed.append(t)
        elif abs(x1 - 106.0) < 0.08 and abs(x2 - 106.0) < 0.08 and min(y1, y2) < 90 and max(y1,y2) < 100:
            # careful — only the north escape
            if max(y1, y2) <= 96.5:
                doomed.append(t)
    for t in doomed:
        board.Delete(t)
    print("3V3 deleted", len(doomed))

    p28, p30 = (98.4, 86.35), (97.6, 86.35)
    add_track(p28[0], p28[1], p30[0], p30[1], 0.25, F, "3V3")
    add_via(97.0, 87.5, "3V3")
    poly([(p30[0], p30[1]), (97.0, p30[1]), (97.0, 87.5)], 0.35, F, "3V3")
    poly([(97.0, 87.5), (93.5, 87.5), (93.5, 98.5), (94.9, 98.5), (94.9, 101.95)], 0.45, B, "3V3")
    add_via(94.9, 101.95, "3V3")
    add_via(106.0, 87.5, "3V3")
    poly([(p28[0], p28[1]), (106.0, p28[1]), (106.0, 87.5)], 0.35, F, "3V3")
    poly([(106.0, 87.5), (106.0, 96.01)], 0.45, B, "3V3")
    add_via(106.0, 96.01, "3V3")
    poly([(106.0, 96.01), (105.2, 96.01)], 0.45, F, "3V3")

    # R_VSYS stitch
    poly([(107.5, 102.975), (107.5, 103.35), (106.0, 103.35), (104.95, 103.35)], 0.45, F, "3V3")
    poly([(107.5, 104.625), (107.5, 104.4)], 0.45, F, "VSYS")

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(PCB), board)
    print("saved")
    for z in board.Zones():
        print("zone", z.GetNetname(), z.GetLayerName())


if __name__ == "__main__":
    main()
