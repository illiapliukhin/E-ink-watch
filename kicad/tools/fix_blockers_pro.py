#!/usr/bin/env python3
"""
Ordered blocker fix + professional routing pass for e-ink-watch.kicad_pcb.

Discipline: assumptions stated; physics widths applied; no net merging to "fix" shorts.
"""
from __future__ import annotations

import json
import math
import re
import uuid
from pathlib import Path

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
PRO = ROOT / "e-ink-watch.kicad_pro"
REPORTS = ROOT / "reports"

# --- Physics-chosen widths (see CALC_POWER_TRACES.md) ---
W_SIG = 0.18
W_PWR = 0.45          # 3V3 / 3V3_DISP / VSYS
W_PWR_FAT = 0.50      # VBAT / VBUS
VIA_SIZE, VIA_DRILL = 0.60, 0.30
CLEAR_EDGE = 0.25
CX, CY, R_BOARD = 100.0, 100.0, 20.0

# J_SWD new position: left of pogo, near SW_DBG, pads along +X at y=108
JSWD_AT = (84.0, 108.0)
JSWD_ANG = 90.0
# Empirical KiCad 90°: pad i at (cx + i*2.54, cy)
JSWD_PADS = {
    "3V3": (84.0, 108.0),
    "SWDIO": (86.54, 108.0),
    "SWDCLK": (89.08, 108.0),
    "nRESET": (91.62, 108.0),
    "GND": (94.16, 108.0),
}

SW_DBG_PADS = {
    "SWDIO": (87.55, 104.5),
    "SWDCLK": (87.55, 105.5),
    "nRESET": (87.55, 106.5),
    "nRESET_POGO": (93.45, 106.5),
    "SWDCLK_POGO": (93.45, 105.5),
    "SWDIO_POGO": (93.45, 104.5),
}

NET_ID = {
    "": 0, "GND": 1, "3V3": 2, "3V3_DISP": 3, "VBAT": 4, "VSYS": 5, "VBUS": 6,
    "EPD_SCK": 7, "EPD_MOSI": 8, "EPD_DC": 9, "EPD_RST": 10, "EPD_CS_MAIN": 11,
    "EPD_CS_L": 12, "EPD_CS_R": 13, "EPD_BUSY_MAIN": 14, "EPD_BUSY_L": 15,
    "EPD_BUSY_R": 16, "SWDIO": 17, "SWDCLK": 18, "nRESET": 19, "BTN1": 20,
    "BTN2": 21, "BTN3": 22, "SWDIO_POGO": 23, "SWDCLK_POGO": 24, "nRESET_POGO": 25,
    "OPT": 26,
}


def uid() -> str:
    return str(uuid.uuid4())


def extract_top_blocks(pcb: str, tag: str) -> list[tuple[int, int, str]]:
    """Extract top-level (tag ...) blocks with paren matching."""
    blocks = []
    i = 0
    token = "(" + tag
    while True:
        j = pcb.find(token, i)
        if j < 0:
            break
        # must be at indent start of a top-ish element: preceded by newline+tabs or start
        if j > 0 and pcb[j - 1] not in "\n\t ":
            i = j + 1
            continue
        # only treat as top-level if line starts with single tab roughly
        line_start = pcb.rfind("\n", 0, j) + 1
        prefix = pcb[line_start:j]
        if prefix not in ("\t", ""):
            i = j + 1
            continue
        depth = 0
        k = j
        in_str = False
        esc = False
        while k < len(pcb):
            ch = pcb[k]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        blocks.append((j, k + 1, pcb[j : k + 1]))
                        break
            k += 1
        i = k + 1
    return blocks


def parse_seg(text: str):
    m = re.search(
        r'\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\)\s+'
        r'\(width\s+([-\d.]+)\)\s+\(layer\s+"([^"]+)"\)\s+\(net\s+(\d+)\)',
        text,
    )
    if not m:
        return None
    return {
        "x1": float(m.group(1)),
        "y1": float(m.group(2)),
        "x2": float(m.group(3)),
        "y2": float(m.group(4)),
        "w": float(m.group(5)),
        "layer": m.group(6),
        "net": int(m.group(7)),
        "text": text,
    }


def parse_via(text: str):
    m = re.search(
        r'\(at\s+([-\d.]+)\s+([-\d.]+)\)\s+\(size\s+([-\d.]+)\)\s+\(drill\s+([-\d.]+)\)'
        r'(?:\s+\(layers\s+"([^"]+)"\s+"([^"]+)"\))?\s+\(net\s+(\d+)\)',
        text,
    )
    if not m:
        return None
    return {
        "x": float(m.group(1)),
        "y": float(m.group(2)),
        "size": float(m.group(3)),
        "drill": float(m.group(4)),
        "net": int(m.group(7)),
        "text": text,
    }


def fmt_seg(x1, y1, x2, y2, w, layer, net) -> str:
    return (
        f'\t(segment\n'
        f'\t\t(start {x1:g} {y1:g})\n'
        f'\t\t(end {x2:g} {y2:g})\n'
        f'\t\t(width {w:g})\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(net {net})\n'
        f'\t\t(uuid "{uid()}")\n'
        f'\t)'
    )


def fmt_via(x, y, net, size=VIA_SIZE, drill=VIA_DRILL) -> str:
    return (
        f'\t(via\n'
        f'\t\t(at {x:g} {y:g})\n'
        f'\t\t(size {size:g})\n'
        f'\t\t(drill {drill:g})\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n'
        f'\t\t(net {net})\n'
        f'\t\t(uuid "{uid()}")\n'
        f'\t)'
    )


def path_segs(pts, w, layer, netname) -> list[str]:
    net = NET_ID[netname]
    out = []
    for (a, b) in zip(pts, pts[1:]):
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            continue
        out.append(fmt_seg(a[0], a[1], b[0], b[1], w, layer, net))
    return out


def nearly(a, b, eps=0.02):
    return abs(a - b) < eps


def main():
    pcb = PCB.read_text()
    assert '(property "Reference" "J_SWD"' in pcb

    # ------------------------------------------------------------------
    # 1) Move J_SWD footprint at-position
    # ------------------------------------------------------------------
    # Replace only the footprint's own (at ...) — first (at after footprint header
    def move_jswd(text: str) -> str:
        idx = text.find('(property "Reference" "J_SWD"')
        start = text.rfind("(footprint", 0, idx)
        # find (at within first 300 chars of footprint
        head = text[start : start + 350]
        m = re.search(r"\(at\s+[-\d.]+\s+[-\d.]+(?:\s+[-\d.]+)?\)", head)
        assert m, "J_SWD at not found"
        old = m.group(0)
        new = f"(at {JSWD_AT[0]:g} {JSWD_AT[1]:g} {JSWD_ANG:g})"
        return text[: start + m.start()] + new + text[start + m.end() :]

    pcb = move_jswd(pcb)
    print(f"Moved J_SWD to {JSWD_AT} rot {JSWD_ANG}")

    # Assign U2 pad 4 to VBUS (was unconnected) — placeholder VIN assumption
    # pad "4" ... no net currently
    def assign_u2_pad4_vbus(text: str) -> str:
        idx = text.find('(property "Reference" "U2"')
        start = text.rfind("(footprint", 0, idx)
        depth = 0
        k = start
        while k < len(text):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    end = k + 1
                    break
            k += 1
        block = text[start:end]
        # Find pad "4" and insert/replace net
        pm = re.search(r'\(pad "4" thru_hole|\(pad "4" smd', block)
        if not pm:
            raise SystemExit("U2 pad 4 not found")
        # get pad block
        ps = pm.start()
        d = 0
        i = ps
        while i < len(block):
            if block[i] == "(":
                d += 1
            elif block[i] == ")":
                d -= 1
                if d == 0:
                    pe = i + 1
                    break
            i += 1
        pad = block[ps:pe]
        if '(net ' in pad:
            pad2 = re.sub(r'\(net\s+\d+\s+"[^"]*"\)', '(net 6 "VBUS")', pad, count=1)
        else:
            # insert before uuid
            pad2 = re.sub(
                r'(\(uuid\s+")',
                r'(net 6 "VBUS")\n\t\t\t\1',
                pad,
                count=1,
            )
        block2 = block[:ps] + pad2 + block[pe:]
        return text[:start] + block2 + text[end:]

    pcb = assign_u2_pad4_vbus(pcb)
    print("Assigned U2.4 -> VBUS (placeholder VIN)")

    # ------------------------------------------------------------------
    # Collect segments/vias and decide deletions
    # ------------------------------------------------------------------
    segs = extract_top_blocks(pcb, "segment")
    vias = extract_top_blocks(pcb, "via")
    print(f"Parsed {len(segs)} segments, {len(vias)} vias")

    del_ranges: list[tuple[int, int]] = []
    new_items: list[str] = []

    def mark_del(a, b):
        del_ranges.append((a, b))

    # --- Delete obsolete J_SWD / off-board SWD stubs ---
    swd_nets = {17, 18, 19}  # SWDIO SWDCLK nRESET
    for a, b, t in segs:
        s = parse_seg(t)
        if not s:
            continue
        net = s["net"]
        x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
        name = {v: k for k, v in NET_ID.items()}.get(net, "?")

        # Old header row y=111.5
        if net in swd_nets | {2}:  # include 3V3 feeds to old header
            if nearly(y1, 111.5) or nearly(y2, 111.5):
                mark_del(a, b)
                continue
            # vertical 3V3 to old header
            if net == 2 and nearly(x1, 95.05) and nearly(x2, 95.05) and max(y1, y2) > 110:
                mark_del(a, b)
                continue
        # SW_DBG fanout stubs that went down to old header (x=87.55 deep)
        if net in swd_nets and nearly(x1, 87.55) and nearly(x2, 87.55) and max(y1, y2) > 109:
            mark_del(a, b)
            continue
        if net in swd_nets and nearly(y1, 110.8) or (net in swd_nets and nearly(y2, 110.8) and nearly(y1, 110.8)):
            if net in swd_nets and (nearly(y1, 110.8) or nearly(y2, 110.8)):
                if min(x1, x2) < 92:
                    mark_del(a, b)
                    continue
        if net in swd_nets and (nearly(y1, 110.3) or nearly(y2, 110.3)):
            if min(x1, x2) < 92:
                mark_del(a, b)
                continue

        # Delete ALL existing *_POGO tracks (rebuild clean)
        if net in (23, 24, 25):
            mark_del(a, b)
            continue

        # Delete ALL VBUS tracks (rebuild to U2.4)
        if net == 6:
            mark_del(a, b)
            continue

        # Power short fixes: delete problematic tracks to rebuild
        # 1) GND F.Cu spine (100,98.5)-(100,107) — shorts VBAT/VSYS
        if net == 1 and s["layer"] == "F.Cu":
            if nearly(x1, 100) and nearly(x2, 100) and min(y1, y2) < 100 and max(y1, y2) > 105:
                mark_del(a, b)
                continue
            # other long GND on F.Cu through center that cause spaghetti — keep connector GNDs

        # 2) VBAT vertical on x=100 through U2 — rebuild offset
        if net == 4:
            if nearly(x1, 100) and nearly(x2, 100) and max(y1, y2) > 110:
                mark_del(a, b)
                continue
            if nearly(y1, 106.25) and nearly(y2, 106.25) and min(x1, x2) < 100.1 and max(x1, x2) > 98:
                # keep pad-level VBAT links; delete only the from-x=100 feeder
                if nearly(x1, 100) or nearly(x2, 100):
                    mark_del(a, b)
                    continue

        # 3) 3V3_DISP long vertical x=95.2 from 106.75 to 87 — major crossing highway
        if net == 3 and s["layer"] == "F.Cu":
            if nearly(x1, 95.2) and nearly(x2, 95.2) and abs(y1 - y2) > 10:
                mark_del(a, b)
                continue
            # horizontal 101.4375,106.75 -> 95.2,106.75 crosses U2
            if nearly(y1, 106.75) and nearly(y2, 106.75) and min(x1, x2) < 96 and max(x1, x2) > 100:
                mark_del(a, b)
                continue

        # 4) Widen existing power tracks later — mark thin power for rebuild selectively
        # Skip for now; upgrade widths in place below

    # Vias to delete
    for a, b, t in vias:
        v = parse_via(t)
        if not v:
            continue
        # GND via on old J_SWD pad5
        if v["net"] == 1 and nearly(v["x"], 99.16) and nearly(v["y"], 111.5):
            mark_del(a, b)
            continue
        # VBUS via at TP1 — will recreate with stitch
        if v["net"] == 6 and nearly(v["x"], 93) and nearly(v["y"], 114):
            mark_del(a, b)
            continue
        # Too-close via pairs: move by deleting and re-adding
        # GND (94.85,97.75) near 3V3 (95.05,97.45)
        if v["net"] == 1 and nearly(v["x"], 94.85) and nearly(v["y"], 97.75):
            mark_del(a, b)
            continue
        # GND (100.95,103.65) near 3V3 (101.05,103.35)
        if v["net"] == 1 and nearly(v["x"], 100.95) and nearly(v["y"], 103.65):
            mark_del(a, b)
            continue

    # ------------------------------------------------------------------
    # Rebuild routes
    # ------------------------------------------------------------------
    # J_SWD factory path from MCU bus
    p = JSWD_PADS
    new_items += path_segs([(92.2, 100.25), (p["SWDIO"][0], 100.25), p["SWDIO"]], W_SIG, "F.Cu", "SWDIO")
    new_items += path_segs([(91.2, 100.75), (p["SWDCLK"][0], 100.75), p["SWDCLK"]], W_SIG, "F.Cu", "SWDCLK")
    new_items += path_segs([(90.2, 101.25), (p["nRESET"][0], 101.25), p["nRESET"]], W_SIG, "F.Cu", "nRESET")
    # 3V3 to J_SWD
    new_items += path_segs([(94.9, 102.2), (p["3V3"][0], 102.2), p["3V3"]], W_PWR, "F.Cu", "3V3")
    # GND from J_SWD to nearby U2 GND area + vias
    new_items += path_segs([p["GND"], (p["GND"][0], 107.25), (97.0625, 107.25)], W_PWR, "F.Cu", "GND")
    new_items.append(fmt_via(p["GND"][0], 107.25, NET_ID["GND"]))
    new_items.append(fmt_via(97.0625, 107.25, NET_ID["GND"]))  # may duplicate existing — ok-ish

    # SW_DBG MCU side → verticals at J_SWD pad X (gating preserved)
    for net in ("SWDIO", "SWDCLK", "nRESET"):
        sx, sy = SW_DBG_PADS[net]
        px, py = p[net]
        new_items += path_segs([(sx, sy), (px, sy)], W_SIG, "F.Cu", net)
        # vertical already covers sy if sy between 100.xx and 108

    # POGO side — route RIGHT of J_SWD, clear of pads (x>=96.5)
    # SWDIO_POGO: SW_DBG → TP3(99,114)
    sx, sy = SW_DBG_PADS["SWDIO_POGO"]
    new_items += path_segs([(sx, sy), (99.0, sy), (99.0, 114.0)], W_SIG, "F.Cu", "SWDIO_POGO")
    # SWDCLK_POGO → TP4(93,111)
    sx, sy = SW_DBG_PADS["SWDCLK_POGO"]
    new_items += path_segs([(sx, sy), (96.5, sy), (96.5, 111.0), (93.0, 111.0)], W_SIG, "F.Cu", "SWDCLK_POGO")
    # nRESET_POGO → TP5(96,111)
    sx, sy = SW_DBG_PADS["nRESET_POGO"]
    new_items += path_segs([(sx, sy), (97.5, sy), (97.5, 111.0), (96.0, 111.0)], W_SIG, "F.Cu", "nRESET_POGO")

    # VBUS: TP1(93,114) → U2.4(98.5625, 107.75), around J_SWD (stay right/below pads)
    # Path avoids y=108 x=84..94.16: go down-right then left to pad4
    u2_vbus = (98.5625, 107.75)
    new_items += path_segs(
        [
            (93.0, 114.0),
            (93.0, 112.0),
            (97.0, 112.0),
            (97.0, 107.75),
            u2_vbus,
        ],
        W_PWR_FAT,
        "F.Cu",
        "VBUS",
    )
    new_items.append(fmt_via(93.0, 114.0, NET_ID["VBUS"]))  # TP1 stitch
    new_items.append(fmt_via(97.0, 112.0, NET_ID["VBUS"]))
    new_items.append(fmt_via(97.0, 107.75, NET_ID["VBUS"]))

    # VBAT: J_BAT(100,115.8) → left side U2, avoid x=100 through VSYS
    # U2 VBAT pads around (98.5625, 106.25/106.75) and (99.25/99.75, 105.5625)
    new_items += path_segs(
        [
            (100.0, 115.8),
            (100.0, 113.5),
            (97.5, 113.5),
            (97.5, 106.25),
            (98.5625, 106.25),
        ],
        W_PWR_FAT,
        "F.Cu",
        "VBAT",
    )
    new_items.append(fmt_via(97.5, 113.5, NET_ID["VBAT"]))
    new_items.append(fmt_via(97.5, 106.25, NET_ID["VBAT"]))

    # Replace deleted 3V3_DISP vertical with cleaner path on B.Cu / offset
    # From U2 pad area (101.4375,106.75) down via to B.Cu lane at x=94.0 to display
    new_items += path_segs([(101.4375, 106.75), (101.4375, 105.5)], W_PWR, "F.Cu", "3V3_DISP")
    new_items.append(fmt_via(101.4375, 105.5, NET_ID["3V3_DISP"]))
    new_items += path_segs([(101.4375, 105.5), (94.0, 105.5), (94.0, 87.0)], W_PWR, "B.Cu", "3V3_DISP")
    new_items.append(fmt_via(94.0, 87.0, NET_ID["3V3_DISP"]))
    new_items += path_segs([(94.0, 87.0), (95.2, 87.0), (97.75, 87.0)], W_PWR, "F.Cu", "3V3_DISP")

    # Relocated GND vias (clear of 3V3 vias)
    new_items.append(fmt_via(93.5, 98.5, NET_ID["GND"]))   # was 94.85,97.75
    new_items.append(fmt_via(99.5, 104.5, NET_ID["GND"]))  # was 100.95,103.65
    # Stitch U1/U2 EP to B.Cu pour (replace deleted F.Cu spine)
    new_items.append(fmt_via(100.0, 98.5, NET_ID["GND"]))
    new_items.append(fmt_via(100.0, 107.0, NET_ID["GND"]))
    new_items.append(fmt_via(100.0, 102.5, NET_ID["GND"]))

    # Upgrade widths on remaining power segments (in-place text replace on kept segs)
    # Done after splice by post-pass on full text

    # ------------------------------------------------------------------
    # Apply deletions (from end) and insert new items before zones
    # ------------------------------------------------------------------
    # Deduplicate del ranges
    del_ranges = sorted(set(del_ranges), key=lambda x: -x[0])
    print(f"Deleting {len(del_ranges)} copper items")
    for a, b in del_ranges:
        pcb = pcb[:a] + pcb[b:]

    # Clean double blank lines from deletions
    pcb = re.sub(r"\n\t\n\t\n", "\n\t\n", pcb)

    # Insert new segments/vias before first (zone
    zidx = pcb.find("\n\t(zone")
    if zidx < 0:
        zidx = pcb.rfind("\n)")
    insertion = "\n" + "\n".join(new_items) + "\n"
    pcb = pcb[:zidx] + insertion + pcb[zidx:]
    print(f"Inserted {len(new_items)} new copper items")

    # ------------------------------------------------------------------
    # Professional pass: widen remaining power tracks on F.Cu/B.Cu
    # ------------------------------------------------------------------
    def widen_power(text: str) -> str:
        # For each segment with net in power, bump width if thinner than target
        fat_nets = {4, 6}  # VBAT VBUS
        pwr_nets = {2, 3, 5}  # 3V3 3V3_DISP VSYS

        def repl(m):
            full = m.group(0)
            net = int(m.group(1))
            w = float(m.group(2))
            target = None
            if net in fat_nets:
                target = W_PWR_FAT
            elif net in pwr_nets:
                target = W_PWR
            elif net == 1 and w >= 0.35:
                # GND tracks that are already power-ish → 0.45
                target = W_PWR
            if target and w + 1e-6 < target:
                full = re.sub(r"\(width\s+[-\d.]+\)", f"(width {target:g})", full, count=1)
            return full

        # segment blocks — careful with regex on net then width order is width before net in file
        # actual order: width then layer then net
        pattern = re.compile(
            r"\(segment\n\t\t\(start [-\d.]+ [-\d.]+\)\n\t\t\(end [-\d.]+ [-\d.]+\)\n"
            r"\t\t\(width ([-\d.]+)\)\n\t\t\(layer \"[^\"]+\"\)\n\t\t\(net (\d+)\)\n"
            r"\t\t\(uuid \"[^\"]+\"\)\n\t\)",
            re.M,
        )

        def repl2(m):
            w = float(m.group(1))
            net = int(m.group(2))
            target = None
            if net in fat_nets:
                target = W_PWR_FAT
            elif net in pwr_nets:
                target = W_PWR
            elif net == 1 and w >= 0.35:
                target = W_PWR
            body = m.group(0)
            if target and w + 1e-6 < target:
                body = re.sub(r"\(width\s+[-\d.]+\)", f"(width {target:g})", body, count=1)
            return body

        return pattern.sub(repl2, text)

    pcb = widen_power(pcb)

    # Strip filled_polygon from zones so refill is clean (keep polygon outline)
    def strip_fills(text: str) -> str:
        # remove filled_polygon blocks inside zones
        out = []
        i = 0
        while True:
            j = text.find("(filled_polygon", i)
            if j < 0:
                out.append(text[i:])
                break
            out.append(text[i:j])
            # match block
            depth = 0
            k = j
            in_str = False
            esc = False
            while k < len(text):
                ch = text[k]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            k += 1
                            break
                k += 1
            # also drop preceding whitespace/newline
            while out and out[-1].endswith("\n"):
                # keep one newline
                break
            i = k
        return "".join(out)

    pcb = strip_fills(pcb)
    print("Stripped zone fills for re-pour")

    # Sanity: paren balance
    def balance(s):
        d = 0
        in_str = False
        esc = False
        for ch in s:
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "(":
                d += 1
            elif ch == ")":
                d -= 1
                if d < 0:
                    return False
        return d == 0

    if not balance(pcb):
        raise SystemExit("Paren imbalance after edit — aborting write")

    PCB.write_text(pcb)
    print(f"Wrote {PCB}")

    # ------------------------------------------------------------------
    # Net classes in .kicad_pro
    # ------------------------------------------------------------------
    pro = json.loads(PRO.read_text())
    pro["net_settings"] = {
        "classes": [
            {
                "bus_width": 12,
                "clearance": 0.15,
                "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2,
                "line_style": 0,
                "microvia_diameter": 0.3,
                "microvia_drill": 0.1,
                "name": "Default",
                "pcb_color": "rgba(0, 0, 0, 0.000)",
                "priority": 2147483647,
                "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": W_SIG,
                "via_diameter": VIA_SIZE,
                "via_drill": VIA_DRILL,
                "wire_width": 6,
            },
            {
                "bus_width": 12,
                "clearance": 0.15,
                "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2,
                "line_style": 0,
                "microvia_diameter": 0.3,
                "microvia_drill": 0.1,
                "name": "Power",
                "pcb_color": "rgba(0, 0, 0, 0.000)",
                "priority": 0,
                "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": W_PWR,
                "via_diameter": VIA_SIZE,
                "via_drill": VIA_DRILL,
                "wire_width": 6,
            },
            {
                "bus_width": 12,
                "clearance": 0.15,
                "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2,
                "line_style": 0,
                "microvia_diameter": 0.3,
                "microvia_drill": 0.1,
                "name": "PowerFat",
                "pcb_color": "rgba(0, 0, 0, 0.000)",
                "priority": 0,
                "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": W_PWR_FAT,
                "via_diameter": VIA_SIZE,
                "via_drill": VIA_DRILL,
                "wire_width": 6,
            },
            {
                "bus_width": 12,
                "clearance": 0.15,
                "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2,
                "line_style": 0,
                "microvia_diameter": 0.3,
                "microvia_drill": 0.1,
                "name": "Signal",
                "pcb_color": "rgba(0, 0, 0, 0.000)",
                "priority": 1,
                "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": W_SIG,
                "via_diameter": VIA_SIZE,
                "via_drill": VIA_DRILL,
                "wire_width": 6,
            },
        ],
        "meta": {"version": 4},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": [
            {"netclass": "PowerFat", "pattern": "VBAT"},
            {"netclass": "PowerFat", "pattern": "VBUS"},
            {"netclass": "Power", "pattern": "3V3"},
            {"netclass": "Power", "pattern": "3V3_DISP"},
            {"netclass": "Power", "pattern": "VSYS"},
            {"netclass": "Power", "pattern": "GND"},
            {"netclass": "Signal", "pattern": "EPD_*"},
            {"netclass": "Signal", "pattern": "SWD*"},
            {"netclass": "Signal", "pattern": "nRESET*"},
            {"netclass": "Signal", "pattern": "BTN*"},
        ],
    }
    # Also set board rules clearance preference
    try:
        rules = pro["board"]["design_settings"]["rules"]
        rules["min_clearance"] = 0.15
        rules["min_track_width"] = 0.15
        rules["min_via_diameter"] = VIA_SIZE
        rules["min_through_hole_diameter"] = VIA_DRILL
    except Exception as e:
        print("rules update warn", e)
    # track width presets
    try:
        pro["board"]["design_settings"]["track_widths"] = [0.15, W_SIG, 0.25, W_PWR, W_PWR_FAT]
        pro["board"]["design_settings"]["via_dimensions"] = [
            {"diameter": VIA_SIZE, "drill": VIA_DRILL}
        ]
    except Exception as e:
        print("widths update warn", e)

    PRO.write_text(json.dumps(pro, indent=2) + "\n")
    print("Updated net classes in .kicad_pro")

    # Verify J_SWD + TP clearance with math
    print("\nClearance check J_SWD vs TP:")
    tps = {
        "TP1": (93.0, 114.0),
        "TP2": (96.0, 114.0),
        "TP3": (99.0, 114.0),
        "TP4": (93.0, 111.0),
        "TP5": (96.0, 111.0),
        "TP6": (99.0, 111.0),
    }
    ok = True
    for net, (px, py) in JSWD_PADS.items():
        r = math.hypot(px - CX, py - CY)
        if r + 0.85 + CLEAR_EDGE > R_BOARD:
            print(f"  EDGE FAIL {net} r={r:.2f}")
            ok = False
        for tn, (tx, ty) in tps.items():
            d = math.hypot(px - tx, py - ty)
            gap = d - 0.85 - 0.75
            if gap < 0.25:
                print(f"  COLLISION {net} vs {tn} gap={gap:.3f}")
                ok = False
            elif gap < 1.0:
                print(f"  tight {net} vs {tn} gap={gap:.3f}")
    # nRESET on-board
    for net, (px, py) in JSWD_PADS.items():
        r = math.hypot(px - CX, py - CY)
        print(f"  pad {net} ({px},{py}) r={r:.2f}")
    print("J_SWD vs TP:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
